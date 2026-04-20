---
id: ADR-0004
title: "Create-only operational mode for protecting externally managed resources from operator reconciliation"
date: 2025-05-26
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [pkg/controller]
jira: SPIRE-28

enhancement-refs:
  - repo: "openshift/enhancements"
    number: 1775
    title: "SPIRE-26: Proposal for zero trust workload identity manager"
supersedes: ""
superseded-by: ""
---

# Create-Only Operational Mode for Externally Managed Resources

## Executive Summary
All controllers in the zero-trust workload identity manager operator implement a uniform "create-only" mode, activated via an environment variable, that allows the operator to bootstrap required resources without ever overwriting subsequent out-of-band modifications. This mode is observable on each CR through a named status condition, enabling platform teams and GitOps tooling to own resource configuration post-installation without fighting operator reconciliation.

## What
Every controller (`SpiffeCsiReconciler`, `SpireAgentReconciler`, `SpireOidcDiscoveryProviderReconciler`) checks a shared flag at the start of each `Reconcile` call. The boolean is threaded through every resource reconciliation function (DaemonSet, ConfigMap, Deployment, ServiceAccount, RBAC, Service, Route, ClusterSPIFFEID). In create-only mode, the `Get → notFound → Create / found → skip update` branch is taken instead of `Get → found → needsUpdate → Update`.

## Why
SPIRE and SPIFFE components (the CSI driver DaemonSet, agent ConfigMap, OIDC deployment) are security-critical and frequently tuned by platform operators after initial rollout—adjusting resource limits, node selectors, or tolerations without wanting the operator to revert changes. Standard Kubernetes operators continuously reconcile toward desired state, making post-install manual changes impossible to preserve. The enhancement proposal (SPIRE-26) explicitly required that uninstallation must not delete operands and that the operator be resilient without being dictatorial over existing configurations.

## Goals
- Allow initial resource bootstrapping by the operator without requiring full lifecycle ownership.
- Preserve out-of-band changes to any managed resource type across reconciliation loops.
- Surface the active mode as a named status condition (`CreateOnlyMode`) on every CR so operators can inspect it via `kubectl get`.
- Provide a clean transition: when the mode is disabled, the prior `ConditionTrue` is explicitly downgraded to `ConditionFalse`.

## Non-Goals
- Does not implement per-resource granularity (mode is all-or-nothing across the operator).
- Does not track or audit what out-of-band changes were made.
- Does not protect resources from deletion—only updates are suppressed.
- Does not expose the mode toggle through the CR spec; it is operator-level configuration only.

## How
**Activation:** `utils.IsInCreateOnlyMode()` reads an environment variable. Each controller calls this once per reconciliation via its `handleCreateOnlyMode` method (e.g., `SpiffeCsiReconciler.handleCreateOnlyMode` in `pkg/controller/spiffe-csi-driver/controller.go`), which returns the boolean and registers the status condition.

**Status propagation:** `handleCreateOnlyMode` calls `statusMgr.AddCondition(utils.CreateOnlyModeStatusType, ...)` with `metav1.ConditionTrue` when active. On deactivation, `apimeta.FindStatusCondition` checks whether the condition was previously `True` before writing `ConditionFalse`—avoiding spurious status writes when the mode was never enabled.

**Per-resource enforcement:** The `createOnlyMode bool` is passed explicitly to every `reconcile*` function. In `pkg/controller/spiffe-csi-driver/daemonset.go`, `reconcileDaemonSet` follows this pattern: `Get` the existing resource; if not found, `Create`; if found and `needsUpdate()` returns true, check `createOnlyMode`—if true, log and skip; if false, `Update`. This pattern is replicated for ConfigMap, Deployment, ServiceAccount, RBAC, and Route across all three controller packages.

**Update detection:** `needsUpdate` delegates to `utils.ResourceNeedsUpdate`, centralizing diff logic and ensuring create-only mode is only consulted when a real change would otherwise be applied.

## Alternatives

**CRD spec field (`spec.createOnly: true`):** Would allow per-instance control without restarting the operator, but complicates the reconciliation loop (the operator would need to reconcile its own behavior based on spec), and would expose the mode to cluster-user RBAC rather than restricting it to operator administrators via environment configuration.

**Finalizers / ownership annotations:** Resources could be annotated to opt out of reconciliation individually. More granular, but requires users to understand and manage annotations on operator-owned resources, and adds watch complexity.

**Pausing the operator entirely:** A `ManagedClusterOperator` pause flag exists in OLM-managed operators. This would stop all reconciliation, including health checks and status updates, which is too coarse—create-only mode still creates missing resources and still reports readiness conditions.

## Risks

- **Silent divergence:** When create-only mode is active, the CR status shows `Ready=True` even if managed resources have been significantly altered. Debugging issues requires inspecting the actual resources rather than trusting operator status.
- **Mode transition hazard:** Disabling create-only mode triggers a normal reconciliation that immediately overwrites all accumulated out-of-band changes. This is not guarded by a confirmation step and could be destructive if done unintentionally.
- **Duplication burden:** `handleCreateOnlyMode` is copy-pasted identically across all three controllers. Any change to the status condition semantics must be applied in multiple places; there is no shared base reconciler.
- **Environment variable coupling:** Operator restarts are required to toggle the mode, making it unsuitable for temporary, targeted bypass of reconciliation.
