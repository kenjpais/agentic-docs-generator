---
id: ADR-0004
title: "Config Hash Annotation-Driven Rolling Restarts on Configuration Change"
date: 2025-05-27
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Config Hash Annotation-Driven Rolling Restarts on Configuration Change

## Executive Summary
Every controller in this operator renders its configuration into a ConfigMap, computes a deterministic hash of that rendered content, and stamps the hash as a pod template annotation on the corresponding DaemonSet, StatefulSet, or Deployment. Because Kubernetes treats any pod template change as a rollout trigger, configuration changes automatically propagate to running pods via a rolling restart—without manual intervention, custom restart logic, or Kubernetes version-specific APIs.

## What
Three controllers are affected:
- `pkg/controller/spire-agent/` — DaemonSet for SPIRE agent; hash annotation key lives in `daemonset.go`, hash is computed in `configmap.go`
- `pkg/controller/spire-server/` — StatefulSet for SPIRE server; two hash annotations (`ztwim.openshift.io/spire-server-config-hash` and `ztwim.openshift.io/spire-controller-manager-config-hash`) are injected via `statefulset.go`
- `pkg/controller/spire-oidc-discovery-provider/controller.go` — Deployment; hash annotation key `ztwim.openshift.io/spire-oidc-discovery-provider-config-hash` threads from `reconcileConfigMap` into `reconcileDeployment`

The decision being documented is: **use content-addressed pod template annotations as the sole mechanism for triggering pod restarts when configuration changes**.

## Why
SPIRE agent, server, and OIDC provider processes read their configuration files once at startup. A ConfigMap update alone does not restart running pods, so stale configuration would persist indefinitely. The operator must close the gap between "ConfigMap is updated" and "pods are running with updated config." Manual restart commands are error-prone and incompatible with a declarative operator model.

## Goals
- Declarative, automatic pod rollout whenever `agent.conf`, `server.conf`, or OIDC config content changes.
- Zero-downtime propagation using the existing `RollingUpdate` strategy already configured on each workload.
- Single source of truth: the hash is derived directly from the rendered config, so annotation drift is structurally impossible.
- Auditable: the annotation in etcd records which config generation a pod is running.

## Non-Goals
- Triggering restarts for changes outside the rendered config (e.g., image tag changes, RBAC changes) — those are handled by `needsUpdate` comparisons in each reconciler.
- Graceful SPIRE-level draining or workload re-attestation coordination before restart.
- Multi-config-file hashing beyond what each controller already tracks (e.g., hashing mounted Secrets).

## How
**Hash generation** (`configmap.go`, `generateSpireAgentConfigMap`): The config struct is marshalled to JSON via `json.MarshalIndent`, then passed to `utils.GenerateConfigHash`. The same deterministic serialization is used every reconcile loop, so identical config always produces the same hash.

**Hash propagation**: `reconcileConfigMap` returns `(string, error)` — the hash string is passed up to the main `Reconcile` method and forwarded directly as a parameter to `reconcileDaemonSet` / `reconcileStatefulSet` / `reconcileDeployment`.

**Annotation injection**: `generateSpireAgentDaemonSet` (daemonset.go) and `GenerateSpireServerStatefulSet` (statefulset.go) receive the hash as an argument and write it into `Template.ObjectMeta.Annotations` alongside the `kubectl.kubernetes.io/default-container` hint. For the SPIRE server, two hashes are injected because the pod hosts both `spire-server` and `spire-controller-manager` containers, each with its own ConfigMap.

**Rollout trigger**: The existing `needsUpdate` function detects that the desired StatefulSet/DaemonSet differs from the live object (annotation changed) and calls `r.ctrlClient.Update`. Kubernetes then computes a pod template hash diff and initiates a rolling restart using the `RollingUpdate` strategy already declared on each workload (`MaxUnavailable: 1` for the DaemonSet).

**Create-only mode guard**: Before issuing the update, each reconciler checks `createOnlyMode`; if set, the annotation-driven update is logged but skipped, preventing churn in environments that restrict mutations.

## Alternatives

**Restart via `kubectl rollout restart` / deletion**: Issuing a pod delete or patching `restartedAt` from inside the operator adds imperative logic and requires tracking whether a restart was already issued for a given config version. Dropped because it's stateful, racey, and harder to audit.

**ConfigMap resource version as the annotation**: Using `resourceVersion` from the ConfigMap object would change on any metadata update (labels, annotations) even with identical data, causing spurious restarts. The content hash avoids this.

**Operator-managed file reloading (SIGHUP)**: Sending a signal to the SPIRE process to reload config would require exec access into the pod and detailed knowledge of each component's reload semantics. SPIRE agent does not support hot reload of all options; this approach was not viable.

**Kubernetes `configMapKeyRef` projected volume with `subPath` invalidation**: Kubernetes does not automatically restart pods when projected volumes update; it only refreshes the file contents. SPIRE reads config at startup only, so file refresh alone is insufficient.

## Risks

- **Hash function stability**: If `utils.GenerateConfigHash` implementation changes (different algorithm, encoding), all pods will roll simultaneously on the next reconcile even without a config change. Engineers must treat this function as a stable contract.
- **JSON map serialization ordering**: Go's `map[string]interface{}` marshalling is non-deterministic in theory, but `json.MarshalIndent` with Go's standard library sorts map keys alphabetically, making it stable in practice. This is an implicit dependency that is not explicitly tested.
- **Two-hash skew for SPIRE server**: If the spire-server config and controller-manager config change simultaneously, both hashes update atomically in one pod template update, which is correct. However, a failure between the two ConfigMap updates could leave hashes inconsistent for one reconcile loop.
- **Debugging**: An operator-rolling pods for an apparently invisible reason requires inspecting the annotation value—engineers unfamiliar with the pattern may not look there first.
- **Create-only mode gap**: When `createOnlyMode` is active, config changes accumulate silently; once the mode is lifted, all pending changes apply at once, which may cause a larger-than-expected rollout.
