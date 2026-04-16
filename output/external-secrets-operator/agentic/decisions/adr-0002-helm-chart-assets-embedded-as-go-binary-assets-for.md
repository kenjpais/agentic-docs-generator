---
id: ADR-0002
title: "Helm Chart Assets Embedded as Go Binary Assets for Operand Deployment"
date: 2025-05-31
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [pkg/controller, pkg/operator]
jira: ESO-51
supersedes: ""
superseded-by: ""
---

# Helm Chart Assets Embedded as Go Binary Assets for Operand Deployment

## Executive Summary
The operator embeds pre-rendered external-secrets Helm chart manifests as compiled Go binary assets, decodes them into typed Kubernetes objects at reconciliation time, and mutates them in-memory with user configuration before applying them to the cluster. This approach gives the operator full deterministic control over operand manifests without requiring Helm or Kustomize at runtime, at the cost of requiring a code change to update the upstream chart version.

## What
- `pkg/operator/assets` — code-generated asset registry holding embedded YAML manifests (accessed via `assets.MustAsset`)
- `pkg/controller/external_secrets/deployments.go` — reconciliation logic that decodes assets, mutates them, and applies them via controller-runtime
- The decision governs how `Deployment` objects for the controller, webhook, cert-controller, and Bitwarden components are produced and kept in sync

## Why
OpenShift operators are expected to own and control every aspect of the operand lifecycle. Running Helm at runtime introduces a dependency on the Helm binary, chart repositories, and network access, none of which are available or acceptable in air-gapped OpenShift environments. Embedding manifests as Go assets produces a single self-contained operator binary whose behavior is fully auditable at build time. The Jira acceptance criteria explicitly required using "assets code generated to read the static manifest," indicating this was a platform-level constraint, not a preference.

## Goals
- Produce a single operator binary with no runtime dependency on Helm, Kustomize, or external chart repositories
- Allow per-instance configuration (images, resources, affinity, tolerations, log level, proxy, node selector) to be applied as in-memory mutations on top of a known-good baseline manifest
- Support conditional component deployment (cert-controller disabled when cert-manager is configured; Bitwarden enabled only when its config is present)
- Detect drift from desired state and reconcile only when a meaningful change is observed (`common.HasObjectChanged`)
- Validate user-supplied configuration (resource requirements, node selectors, tolerations, affinity) before applying it

## Non-Goals
- Upgrading the embedded chart version automatically or tracking upstream Helm releases at runtime
- Supporting arbitrary Helm values or templating beyond what the operator's CRD surface area exposes
- Managing CRDs or ClusterRoles via this asset mechanism (those are separate concerns)

## How
**Asset embedding:** YAML manifests derived from the external-secrets Helm chart are pre-rendered and compiled into the operator binary via a code-generation step that populates `pkg/operator/assets`. `assets.MustAsset(assetName)` retrieves the raw bytes at runtime; panicking on missing assets is intentional — a missing asset indicates a broken build, not a recoverable runtime error.

**Reconciliation flow in `deployments.go`:**
1. `createOrApplyDeployments` builds a table of `(assetName, condition)` pairs. Conditional entries (`certControllerDeploymentAssetName` gated on `!isCertManagerConfigEnabled`, `bitwardenDeploymentAssetName` gated on `isBitwardenConfigEnabled`) drive which components are deployed for a given `ExternalSecretsConfig` instance.
2. `createOrApplyDeploymentFromAsset` calls `getDeploymentObject`, checks cluster state via `r.Exists`, and decides between create, update (only when `HasObjectChanged` returns true), or no-op.
3. `getDeploymentObject` performs the full mutation pipeline: decode bytes → set namespace → apply `ResourceMetadata` labels/annotations → set pod template labels/annotations → switch on asset name to call component-specific mutators (`updateContainerSpec`, `updateWebhookContainerSpec`, etc.) → apply cross-cutting concerns (resource requirements, affinity, tolerations, node selector, proxy config, user deployment overrides).

**Image injection:** Container images are not baked into assets; they are injected from environment variables (`externalsecretsImageEnvVarName`, `bitwardenImageEnvVarName`) validated at reconcile time. A missing variable returns an `IrrecoverableError`, preventing the operator from applying a deployment with an empty image.

**Validation:** Resource requirements are validated using internal Kubernetes validation (`corevalidation.ValidateContainerResourceRequirements`) via an `unsafe.Pointer` cast from `corev1` to `core` types, avoiding a full API conversion. Node selectors and tolerations go through `metav1validation` and analogous validators before being written to the deployment spec.

## Alternatives

**Run Helm at runtime:** Would allow tracking upstream chart values precisely but requires the Helm binary in the operator image, network access to chart repos, and introduces non-determinism. Incompatible with air-gapped OpenShift deployments.

**Kustomize overlays applied at runtime:** Controller-runtime has Kustomize support. However, this still requires shipping overlay files separately and does not eliminate the need for a patching strategy; it trades one file format for another without simplifying the mutation logic.

**Server-Side Apply with static manifests and strategic merge:** SSA would reduce the operator's need to track `HasObjectChanged` manually, but it loses fine-grained control over which fields the operator owns versus what users may modify, and requires careful field manager discipline across upgrades.

**Dynamic manifest generation (pure Go structs, no embedded YAML):** Building `appsv1.Deployment` objects entirely in Go eliminates the asset pipeline but loses the Helm chart as a source of truth and makes diff-based chart upgrades harder to review.

## Risks

- **Chart version drift:** Updating the upstream external-secrets chart requires a manual re-render and code change. There is no automated mechanism to detect or pull chart updates, creating a maintenance burden.
- **Asset pipeline opacity:** If the code-generation step for `pkg/operator/assets` is not run before a build, the binary silently embeds stale manifests. `MustAsset` panics protect against missing keys but not stale content.
- **`unsafe.Pointer` cast for validation:** The cast from `corev1.ResourceRequirements` to `core.ResourceRequirements` in `validateResourceRequirements` is fragile; any divergence in field layout between the two structs across Kubernetes version bumps will cause silent data corruption or panics.
- **Mutation pipeline ordering:** The sequential mutation functions in `getDeploymentObject` have implicit ordering dependencies. A later mutator (e.g., `applyUserDeploymentConfigs`) may silently overwrite an earlier one's output, making behavior hard to reason about as the number of mutators grows.
