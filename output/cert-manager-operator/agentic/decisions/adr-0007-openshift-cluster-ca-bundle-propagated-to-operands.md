---
id: ADR-0007
title: "OpenShift cluster CA bundle propagated to operands via CNO-injected ConfigMap and SHA-256 hash-triggered rolling restarts"
date: 2026-03-25
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# OpenShift Cluster CA Bundle Propagation to trust-manager via CNO-Injected ConfigMap and Hash-Triggered Rolling Restarts

## Executive Summary
The cert-manager operator bridges OpenShift's cluster-wide CA infrastructure (managed by the Cluster Network Operator) to trust-manager's operand by reading a CNO-injected ConfigMap, reformatting its PEM bundle into trust-manager's proprietary JSON package format, and writing the result into the operand namespace. A SHA-256 hash of the raw PEM content is stored as a pod template annotation so that Kubernetes triggers rolling restarts precisely when certificate content changes — not on incidental metadata updates — avoiding unnecessary disruption to workloads that depend on trust-manager.

## What
- **`pkg/controller/trustmanager/configmaps.go`**: Reads the CNO-injected CA ConfigMap from the operator namespace, serializes it to trust-manager's `caPackage` JSON structure, and applies the result as a ConfigMap in the operand namespace. Returns a SHA-256 hex digest of the raw PEM bundle.
- **`pkg/controller/trustmanager/deployments.go`**: Consumes the digest as `caBundleHash`, mounts the CA package ConfigMap as a volume into the trust-manager container, and stamps `defaultCAPackageHashAnnotation` onto `Deployment.Spec.Template.Annotations`.
- The feature is gated by `DefaultCAPackageConfig` on the `TrustManager` CR spec; all paths are no-ops when the feature is disabled.

## Why
OpenShift clusters manage a cluster-scoped trusted CA bundle centrally via CNO injection into annotated ConfigMaps. trust-manager, however, expects its default CA package in a specific JSON envelope (`{"name":…,"bundle":…,"version":…}`) mounted at a known filesystem path (`--default-package-location`). Without this bridge, trust-manager would have no knowledge of cluster-specific CAs (e.g., proxies, private PKIs), breaking Bundle resolution for workloads in the cluster. Additionally, CA bundles can be updated without any other operator state changing; a naïve approach that tracks ConfigMap `resourceVersion` would trigger restarts on every metadata change, while ignoring CA changes would silently leave the operand with stale trust anchors.

## Goals
- Deliver the OpenShift cluster CA bundle to trust-manager in its required JSON package format.
- Trigger Deployment rolling restarts if and only if PEM certificate content changes.
- Remain a no-op when `DefaultCAPackage` is not enabled, imposing zero overhead on minimal installs.
- Propagate the CNO-provided `resourceVersion` as the package `version` field for auditability.
- Idempotently reconcile: skip the Patch call when ConfigMap content is unchanged (`configMapModified` check).

## Non-Goals
- Rotation or management of the CA bundle itself (that is CNO's responsibility).
- Validation of individual PEM certificates within the bundle.
- Support for non-CNO CA injection mechanisms or user-supplied bundles via this code path.
- Cross-namespace Bundle propagation logic (that is trust-manager's own concern).

## How
**Data flow:**

1. `createOrApplyDefaultCAPackageConfigMap` (configmaps.go) is called during each reconcile loop with the `TrustManager` CR and shared label/annotation maps.
2. `readTrustedCABundle` fetches the CNO-injected ConfigMap by the well-known name `common.TrustedCABundleConfigMapName` from `common.OperatorNamespace`, extracting the PEM string from `common.TrustedCABundleKey`. Hard failure if the key is absent.
3. `formatCAPackage` marshals a `caPackage` struct to JSON, embedding the PEM as `bundle` and the ConfigMap's `resourceVersion` as `version`. This JSON blob becomes the sole data entry in the operand-namespace ConfigMap under `defaultCAPackageFilename`.
4. `computeCABundleHash` applies `crypto/sha256` to the raw PEM string (not the JSON), returning a hex digest. Hashing the PEM rather than the JSON prevents version-field churn (ResourceVersion increments) from causing unnecessary pod restarts.
5. `buildDefaultCAPackageConfigMap` constructs the desired `corev1.ConfigMap` for `operandNamespace` and applies it via SSA (`client.Apply` + `client.ForceOwnership`). The `configMapModified` guard (`maps.Equal` on `.Data` plus managed metadata comparison) skips the Patch when no content has changed.
6. The returned `bundleHash` string flows into `createOrApplyDeployment` → `getDeploymentObject` → `updateDefaultCAPackageVolume` (deployments.go), which sets `deployment.Spec.Template.Annotations[defaultCAPackageHashAnnotation] = caBundleHash`. Kubernetes detects the annotation change on the pod template and initiates a rolling restart of trust-manager pods.
7. `updateDefaultCAPackageVolume` also idempotently splices in the `defaultCAPackageVolumeName` volume (backed by the operand-namespace ConfigMap) and a `ReadOnly` VolumeMount at `defaultCAPackageMountPath` into the trust-manager container, deduplicating by name/path before appending.
8. `validateDeploymentManifest` guards against silent no-ops by asserting that the bindata manifest contains the expected container (`trustManagerContainerName`) and TLS secret volume before any mutations are applied.

## Alternatives

**1. Mount the CNO ConfigMap directly into the operand namespace pod.**
Would require cross-namespace volume mounts, which Kubernetes does not support. A projected volume referencing a ConfigMap in another namespace is not possible natively. Rejected: technically infeasible.

**2. Use a CNO injection annotation on a ConfigMap in the operand namespace.**
CNO injection is namespace-scoped and could annotate a ConfigMap directly in the operand namespace. However, this would not produce trust-manager's required JSON envelope, and the operator would lose the ability to gate the feature or control the exact format. Rejected: insufficient format control.

**3. Restart on ConfigMap ResourceVersion change instead of PEM hash.**
ResourceVersion increments on any metadata update (label changes, annotations). This would trigger spurious rolling restarts on every reconcile that touches the source ConfigMap. Rejected: too disruptive; the PEM hash provides content-addressable restart semantics.

**4. Use a Kubernetes `Secret` instead of a `ConfigMap` for the CA bundle.**
CA certificates are not secret material; using a Secret would impose unnecessary RBAC complexity and obscure the intent. Rejected: semantically incorrect, operational overhead.

## Risks

- **Format coupling**: The `caPackage` JSON struct is trust-manager's internal format. If upstream trust-manager changes its expected package schema, the operator will silently supply a malformed bundle. The TODO comment in `formatCAPackage` acknowledges this is not cross-checked.
- **CNO dependency**: If the CNO-injected ConfigMap is absent or empty at reconcile time, `readTrustedCABundle` returns a hard error, stalling the entire reconcile loop and blocking all other trust-manager operand updates.
- **Hash stability**: The hash covers only the PEM string. If trust-manager requires a restart for reasons beyond PEM content (e.g., mount path or filename changes), the annotation mechanism will not catch it; a manual annotation bump or operator code change is needed.
- **Idempotency window**: Between the ConfigMap Patch and the Deployment Patch, a crash leaves the operand ConfigMap updated but the Deployment annotation stale. The next reconcile self-heals, but there is a brief inconsistency window.
- **ResourceVersion as version**: Embedding `resourceVersion` in the JSON `version` field ties the package version to Kubernetes internals, which are opaque and non-monotonic after etcd compaction or cluster migration.
