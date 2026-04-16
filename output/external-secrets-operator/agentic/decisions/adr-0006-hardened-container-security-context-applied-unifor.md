---
id: ADR-0006
title: "Hardened Container Security Context Applied Uniformly to All Operand Deployments"
date: 2025-05-31
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [pkg/controller]
jira: ESO-51
supersedes: ""
superseded-by: ""
---

# Hardened Container Security Context Applied Uniformly to All Operand Deployments

## Executive Summary
The operator enforces a fixed, hardened `SecurityContext` on every container it manages—external-secrets controller, webhook, cert-controller, and bitwarden—by overwriting the security context in Go code during reconciliation. This makes security posture a property of the operator binary rather than a property of the Helm chart manifests or cluster admission policy, ensuring it cannot drift or be bypassed by modifying static assets.

## What
- **File**: `pkg/controller/external_secrets/deployments.go`
- **Function**: `updateContainerSecurityContext(*corev1.Container)` — called for every container in every managed deployment
- **Decision**: Security context fields are set programmatically and unconditionally, overriding whatever the base manifest asset declares

## Why
This operator manages operands by rendering static manifest assets (via `assets.MustAsset`) and then layering Go-code mutations on top before applying to the cluster. Without in-code enforcement, the security context would be whatever is committed to the asset files. That creates three failure modes: a manifest update silently weakens security; a cluster without a restrictive admission policy (e.g., Pod Security Admission in `baseline` mode) permits privileged containers; or an operator deployed to a permissive namespace inherits no hardening. OpenShift's security model expects workloads to declare their constraints explicitly rather than relying on cluster-level catch-alls.

## Goals
- Guarantee `AllowPrivilegeEscalation=false`, all capabilities dropped, `ReadOnlyRootFilesystem=true`, `RunAsNonRoot=true`, and `SeccompProfile=RuntimeDefault` on every reconciled container
- Make security posture immutable with respect to asset file content—manifests cannot weaken it
- Apply uniformly across all four operand types without per-deployment conditional logic
- Ensure the constraint survives drift: reconciliation detects and corrects any out-of-band change via `common.HasObjectChanged`

## Non-Goals
- Per-container tuning of security context (e.g., allowing different profiles for different operands)
- Pod-level security context configuration (`PodSecurityContext`)
- Management of OpenShift SCCs or namespace-level Pod Security Admission labels
- Exposing security context fields as user-configurable API fields in `ExternalSecretsConfig`

## How
`getDeploymentObject` in `deployments.go` is the single assembly point for all deployment objects. After decoding the base manifest (`common.DecodeDeploymentObjBytes(assets.MustAsset(assetName))`), it calls asset-specific mutators (`updateContainerSpec`, `updateWebhookContainerSpec`, etc.). Each of those mutators calls `updateContainerSecurityContext` on the container pointer before returning.

`updateContainerSecurityContext` unconditionally replaces `container.SecurityContext` with a fully-specified `*corev1.SecurityContext` struct, using `ptr.To(false)` / `ptr.To(true)` to set pointer-typed booleans, explicitly setting `RunAsUser: nil` to avoid pinning a UID, and setting `SeccompProfile.Type = corev1.SeccompProfileTypeRuntimeDefault`. The assignment is a full replacement, not a merge, so no field from the asset manifest survives.

The reconcile loop in `createOrApplyDeploymentFromAsset` uses `common.HasObjectChanged` to detect deviation from desired state and calls `UpdateWithRetry` to restore it, meaning any out-of-band mutation to the security context on a live deployment will be corrected on the next reconcile cycle.

## Alternatives

**Rely on Pod Security Admission (PSA) at the namespace level**: Configuring the operand namespace with `enforce: restricted` would reject non-conforming pods. This was not chosen because it couples security to cluster configuration outside the operator's control, varies across OpenShift versions and installation profiles, and provides no self-healing when a running pod's spec drifts.

**Encode constraints only in the static asset manifests**: Keeping the security context in YAML assets is simpler but creates a separation between "what the code thinks" and "what the file says," with no code-level guarantee. A manifest regeneration or a PR touching assets could silently regress security.

**OPA/Gatekeeper admission policy**: A cluster-wide policy could enforce these constraints at admission time. This is redundant with in-code enforcement and introduces a hard dependency on policy infrastructure being installed and active, which cannot be assumed in all target environments.

## Risks

- **Operational inflexibility**: `updateContainerSecurityContext` is unconditional. If a future operand legitimately requires a capability (e.g., binding to a privileged port), the code must be refactored rather than simply updating an asset file. The `ReadOnlyRootFilesystem=true` constraint is particularly likely to surface issues as operand software evolves.
- **Silent breakage on image changes**: If a new container image writes to the root filesystem at startup, it will crash with a cryptic `Read-only file system` error. There is no test coverage in the reconciler that validates runtime behavior against the security context.
- **Maintenance coupling**: The four `updateXxxContainerSpec` functions each independently call `updateContainerSecurityContext`. Adding a new operand requires remembering to call it; there is no compile-time or test-time enforcement of this convention.
- **Divergence from upstream Helm chart**: The upstream external-secrets Helm chart may ship its own security context values. Operators adopting a newer chart version will have those values silently overridden, which is correct behavior but may confuse engineers debugging by diffing against the upstream chart.
