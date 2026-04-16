---
id: ADR-0003
title: "Upstream cert-manager manifests embedded as bindata and mutated at reconciliation time rather than templated at build time"
date: 2021-07-05
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Upstream Manifests as Embedded Bindata with Reconciliation-Time Mutation

## Executive Summary
The operator embeds upstream cert-manager, trust-manager, and istio-csr release YAML as Go bindata assets and applies programmatic mutations (args, images, volumes, scheduling, resources) at reconciliation time rather than using a templating engine or generating manifests at build time. This keeps the operator's configuration surface in typed Go code, leverages library-go's `staticresourcecontroller` for idempotent resource management, and makes upstream upgrades an explicit Makefile-driven re-download step rather than a silent diff.

## What
- **Embedded assets**: Upstream YAML split into per-resource files under `pkg/operator/assets/`, accessed via `assets.Asset` / `assets.MustAsset`.
- **Static resources**: RBAC, ServiceAccounts, Services applied unchanged via `staticresourcecontroller.NewStaticResourceController` (see `cert_manager_cainjector_deployment.go`).
- **Deployment mutation pipelines**: `getDeploymentObject` functions in `pkg/controller/certmanager/`, `pkg/controller/trustmanager/deployments.go`, and `pkg/controller/istiocsr/deployments.go` decode the embedded YAML into typed `*appsv1.Deployment` objects and apply sequential, named mutation functions before applying to the cluster.
- **Decision**: Use bindata + imperative mutation instead of a Helm chart, Kustomize overlays, or Go `text/template`.

## Why
OpenShift operators managed by OLM must ship all manifests in-process; no external chart renderer is available at runtime. The operator also needs to overlay OpenShift-specific concerns (image overrides via environment variables, cloud-credential secrets, trusted CA configmaps, scheduling constraints) that upstream manifests cannot anticipate. Using typed Go mutations instead of a templating language gives compile-time safety and allows conditional logic (e.g., `defaultCAPackageEnabled`, `secretTargetsEnabled`) that would be verbose or error-prone in YAML templates.

## Goals
- Ship a self-contained operator binary with all operand manifests baked in.
- Allow OpenShift-specific mutations (image, args, scheduling, volumes) without forking upstream manifests.
- Provide explicit, auditable upgrade paths: re-download upstream YAML via Makefile, regenerate bindata, review diff in PR.
- Fail loudly at reconciliation time when the upstream manifest structure has changed incompatibly (via `validateDeploymentManifest` in `trustmanager/deployments.go`).
- Reuse library-go's `staticresourcecontroller` for idempotent apply of non-deployment resources.

## Non-Goals
- Runtime manifest templating or user-facing Helm values.
- Tracking upstream cert-manager changes automatically (no CD pipeline for manifest sync).
- Supporting arbitrary user-supplied manifests.

## How
**Data flow:**

1. At build time, upstream YAML is downloaded (Makefile target), split per resource, and compiled into `pkg/operator/assets/` via `go-bindata` or equivalent.
2. At reconciliation time, static resources (RBAC, SA, Services) are registered as string paths in arrays like `certManagerCAInjectorAssetFiles` and passed to `staticresourcecontroller.NewStaticResourceController`, which calls `assets.Asset` and applies them idempotently.
3. Deployments follow a separate pipeline: `getDeploymentObject` calls `assets.MustAsset(deploymentAssetName)`, decodes bytes into `*appsv1.Deployment` via a codec (e.g., `common.DecodeObjBytes`), then pipes the object through a chain of named mutators.

**Mutation chain (trustmanager example, `deployments.go`):**
- `common.UpdateName/Namespace/ResourceLabels` — identity fields
- `updateDeploymentArgs` — constructs the full `--flag=value` arg list from `v1alpha1.TrustManager` spec fields
- `updateImage` — reads `RELATED_IMAGE_*` env var; errors if unset (making image injection mandatory)
- `updateDefaultCAPackageVolume` — conditionally adds a ConfigMap volume and hash annotation for rolling restarts
- `updateResourceRequirements`, `updateAffinityRules`, `updatePodTolerations`, `updateNodeSelector` — scheduling overlays from CR spec
- `validateDeploymentManifest` — asserts required container and volume names exist, catching upstream structural renames before silent no-ops

**Apply strategy differs by controller:**
- `trustmanager`: SSA via `client.Apply` + `client.ForceOwnership`
- `istiocsr`: optimistic update (`UpdateWithRetry`) with `hasObjectChanged` guard
- `certmanager`: library-go `staticresourcecontroller` for static files; a separate generic deployment controller for the Deployment

## Alternatives

**Helm / Kustomize at runtime**: Would allow closer tracking of upstream defaults but requires embedding a chart renderer in the operator binary, introduces YAML-level logic, and complicates OLM packaging. Library-go's operator pattern is incompatible with Helm's release lifecycle.

**Go `text/template` over YAML**: Keeps logic in YAML but loses type safety; conditional blocks become unwieldy and template errors surface at runtime rather than compile time.

**Fork upstream manifests entirely**: Eliminates the dependency on upstream structure but creates a permanent maintenance divergence. The current approach retains upstream YAML as the source of truth and layers mutations on top.

**Controller-runtime `MutatingWebhook` or defaulting logic**: Could push mutations to admission time but requires a running webhook, adds operational complexity, and doesn't solve the build-time embedding requirement.

## Risks

- **Structural coupling**: If upstream renames a container (`trustManagerContainerName`) or removes a volume (`tlsVolumeName`), mutation functions silently no-op unless `validateDeploymentManifest`-style guards exist. Only trustmanager has this guard; certmanager and istiocsr controllers are more fragile.
- **Upgrade opacity**: Upgrading the embedded manifests requires a manual Makefile step and PR review. There is no automated signal when upstream releases a new version.
- **Arg list ownership**: Full `--flag=value` arg lists are constructed entirely in Go (e.g., `updateArgList` in `istiocsr/deployments.go`); any new upstream flag must be explicitly added or it will be absent, regardless of what the embedded YAML contains.
- **Inconsistent apply strategies** across the three controllers (SSA vs. update vs. staticresourcecontroller) increases cognitive overhead and can cause ownership conflicts if controllers are changed independently.
