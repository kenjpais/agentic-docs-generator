---
id: ADR-0005
title: "Create-Only Operational Mode for Upgrade Safety"
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

# Create-Only Operational Mode for Upgrade Safety

## Executive Summary
All controllers in the zero-trust workload identity manager operator implement a create-only mode, activated via `utils.IsInCreateOnlyMode()`, that allows the operator to bootstrap missing resources during upgrades without overwriting existing ones. The mode is surfaced as a typed status condition on each CR, giving both human operators and automation visibility into the reconciler's current posture.

## What
- All three component controllers (`SpiffeCsiReconciler`, `SpireAgentReconciler`, `SpireOidcDiscoveryProviderReconciler`) implement `handleCreateOnlyMode()` using an identical pattern.
- The mode gates the `Update` path in every resource reconciler (e.g., `reconcileDaemonSet` in `pkg/controller/spiffe-csi-driver/daemonset.go`).
- The mode state is written to the CR's `ConditionalStatus.Conditions` using condition type `utils.CreateOnlyModeStatusType` with reasons `utils.CreateOnlyModeEnabled` / `utils.CreateOnlyModeDisabled`.

## Why
The operator manages security-critical infrastructure (SPIRE agents, SPIFFE CSI driver, OIDC discovery) that may be shared with or configured by external systems. During OLM-managed upgrades, a new operator version reconciling immediately and overwriting in-flight workload configuration could cause SPIFFE identity issuance outages. The enhancement proposal explicitly requires that uninstall not delete operands, signaling a philosophy of non-destructive operator behavior. Create-only mode extends this to upgrades: the operator must be safe to deploy into an already-running cluster.

## Goals
- Prevent the operator from overwriting existing resource configuration during upgrades or when external ownership is assumed.
- Provide observable state: users can `kubectl get` any component CR and inspect the `CreateOnlyMode` condition.
- Apply consistently across all controllers without per-resource special-casing.
- Allow the mode to self-clear: when `IsInCreateOnlyMode()` returns false and the prior condition was `True`, the condition is explicitly flipped to `False`.

## Non-Goals
- Does not define what triggers create-only mode (the mechanism behind `IsInCreateOnlyMode()` is external to the controllers, likely an environment variable).
- Does not protect against deletion of managed resources; only updates are suppressed.
- Does not apply to the SCC reconcilers, which appear to handle their own idempotency separately.

## How
**Mode detection:** Each controller's `Reconcile()` calls `handleCreateOnlyMode()` immediately after owner-reference setup and before any resource reconciliation. The method calls `utils.IsInCreateOnlyMode()` (a shared utility, not per-controller logic) and registers the appropriate condition with the `status.Manager`.

**Condition lifecycle:** If mode is active, `statusMgr.AddCondition(utils.CreateOnlyModeStatusType, utils.CreateOnlyModeEnabled, ..., metav1.ConditionTrue)` is called. If mode is inactive but the condition previously existed as `True`, it is explicitly set to `False` via `apimeta.FindStatusCondition()` + `AddCondition(..., utils.CreateOnlyModeDisabled, ..., metav1.ConditionFalse)`. Conditions are flushed at reconcile completion via the deferred `statusMgr.ApplyStatus()`.

**Update suppression:** The `createOnlyMode bool` return value is threaded through every resource reconciler as a parameter. In `pkg/controller/spiffe-csi-driver/daemonset.go`, `reconcileDaemonSet` follows the pattern: `Create` if not found, then `if err == nil && needsUpdate(...) { if createOnlyMode { log skip } else { Update } }`. This pattern is replicated in all resource reconcilers across all three controllers.

**Observability:** Because conditions are written to `ConditionalStatus` on the CR itself and flushed via the deferred status apply, the mode is immediately visible through standard Kubernetes status inspection on `SpiffeCSIDriver`, `SpireAgent`, and `SpireOIDCDiscoveryProvider` objects.

## Alternatives
**Full reconciliation with leader-election pause:** The operator could stop reconciling entirely during upgrades. This would risk missing newly-required resources and is harder to implement safely with OLM.

**Webhook-based admission protection:** A validating webhook could block updates to managed resources during upgrades. This adds an availability dependency (the webhook itself) and doesn't solve the operator-self-update scenario.

**Annotation-based opt-out per resource:** Individual resources could carry an annotation disabling operator management. This is more granular but requires manual intervention and is not observable through CR status.

**Server-side apply with ownership fields:** Using SSA would allow field-level conflict detection. However, SSA semantics during upgrades between operator versions with changing field managers introduce their own hazard class, and the pattern was not chosen given the operator's non-destructive philosophy.

## Risks
- **Silent drift accumulation:** While in create-only mode, configuration drift between the desired spec and actual resources accumulates silently. When the mode deactivates, a single reconcile applies all accumulated changes simultaneously, which may cause rolling restarts across all managed DaemonSets and Deployments at once.
- **Mode activation mechanism is opaque:** The implementation delegates to `utils.IsInCreateOnlyMode()` without exposing its trigger in the controllers. Engineers modifying reconcilers must trace into the utility package to understand when the mode activates, creating a maintenance gap.
- **No per-resource granularity:** Create-only mode is all-or-nothing per reconcile cycle. A partial upgrade where only some resources need protection cannot be expressed.
- **Condition-only observability:** There is no metric or event emitted when create-only mode suppresses an update, making it difficult to detect prolonged drift in monitoring systems without querying CR conditions directly.
