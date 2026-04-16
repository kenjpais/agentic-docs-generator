---
id: ADR-0008
title: "Aggregated Status Reporting: Component CRs Roll Up Into Parent Manager CR"
date: 2025-05-26
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [api/v1alpha1, pkg/controller]
jira: SPIRE-28

enhancement-refs:
  - repo: "openshift/enhancements"
    number: 1775
    title: "SPIRE-26: Proposal for zero trust workload identity manager"
supersedes: ""
superseded-by: ""
---

# Aggregated Status Reporting: Component CRs Roll Up Into Parent Manager CR

## Executive Summary
The zero-trust-workload-identity-manager operator uses a two-tier status aggregation pattern where each SPIRE component CR (`SpireAgent`, `SpiffeCSIDriver`, etc.) independently maintains its own `ConditionalStatus`, and the parent `ZeroTrustWorkloadIdentityManager` CR aggregates these into a single `Operands` array. This provides operators a single pane of glass for cluster-wide SPIRE health without requiring direct inspection of every component CR.

## What
- `api/v1alpha1/zero_trust_workload_identity_manager_types.go`: Defines `ZeroTrustWorkloadIdentityManagerStatus` with an `Operands []OperandStatus` field indexed by `kind`, and `OperandStatus` containing `Ready`, `Message`, and `Conditions` fields.
- `pkg/controller/spiffe-csi-driver/controller.go` and `pkg/controller/spire-agent/controller.go`: Each component controller independently manages its own `ConditionalStatus` via a `status.Manager`, which is then read and summarized by the parent controller.
- The decision being documented is: how health state flows from leaf component CRs up to the parent manager CR.

## Why
All component CRs are singleton resources named `"cluster"`, making Kind the only meaningful discriminator. Without aggregation, an operator monitoring SPIRE health would need to watch four separate CRs (`SpireServer`, `SpireAgent`, `SpiffeCSIDriver`, `SpireOIDCDiscoveryProvider`) and correlate their states manually. The `ZeroTrustWorkloadIdentityManager` CR is the user-facing entry point per the enhancement proposal, so it must reflect overall system health. OLM-managed operators are expected to expose a top-level ready condition; aggregation satisfies this requirement.

## Goals
- Provide a single operational health view across all SPIRE components from the `ZeroTrustWorkloadIdentityManager` CR.
- Allow each component controller to reason about and report its own health independently.
- Enable `kubectl get zerotrustworkloadidentitymanager cluster` to answer "is SPIRE healthy?" without inspecting child CRs.
- Use Kind as the map key (`+listMapKey=kind`) since all operands share the name `"cluster"`.

## Non-Goals
- The parent CR does not control or configure SPIRE components directly; that is delegated to `SpireConfig` and individual component CRDs.
- Aggregation does not implement automatic remediation based on rolled-up status.
- Cross-component dependency ordering is not encoded in the status schema.

## How
**Component-level status management:** Each component controller (e.g., `SpireAgentReconciler`, `SpiffeCsiReconciler`) instantiates a `status.Manager` at reconcile time and registers conditions via `statusMgr.AddCondition(...)`. A `defer` block calls `statusMgr.ApplyStatus(ctx, &agent, func() *v1alpha1.ConditionalStatus { return &agent.Status.ConditionalStatus })` to persist the final condition state to the component CR at reconcile end, regardless of success or failure.

**Initial state reset:** `status.SetInitialReconciliationStatus(...)` sets `Ready=false` at reconcile start, ensuring stale ready states never persist across reconcile failures.

**Parent aggregation:** The parent `ZeroTrustWorkloadIdentityManager` controller reads each component CR's `ConditionalStatus` and populates the `Operands []OperandStatus` array. Each `OperandStatus` carries `Kind` (the map key), `Name` (always `"cluster"`), `Ready` (string `"true"`/`"false"`), `Message`, and a subset of `Conditions`.

**Watch topology:** Component controllers watch `ZeroTrustWorkloadIdentityManager` via `Watches(&v1alpha1.ZeroTrustWorkloadIdentityManager{}, ..., utils.ZTWIMSpecChangedPredicate)` and always re-enqueue the `"cluster"` CR name. This means ZTWIM spec changes propagate down to component reconciliation loops.

**Schema enforcement:** `+listType=map` and `+listMapKey=kind` on `Operands` allow server-side apply to merge operand entries by Kind without duplication. The `Kind` field is validated as an enum of the four known component types.

## Alternatives

**Single monolithic controller managing all resources:** One controller reconciles all SPIRE resources and writes status directly. Rejected because it couples unrelated reconciliation logic, makes partial failures harder to isolate, and conflicts with the operator's goal of per-component lifecycle management.

**Push-based status from child to parent via events:** Child controllers emit events or directly patch the parent CR's `Operands` entry. Rejected because concurrent patches from multiple controllers risk conflicts and require careful locking; the pull-based read in the parent controller is safer under controller-runtime's single-threaded reconcile guarantee.

**No aggregation; expose per-component CRs only:** Users inspect individual CRs for health. Rejected because OLM expects a single top-level CR to reflect operator health, and the enhancement proposal explicitly defines `ZeroTrustWorkloadIdentityManager` as the user-facing API.

## Risks

- **Staleness:** The parent controller's `Operands` view is only as fresh as its last reconcile. A component CR may update its `ConditionalStatus` without immediately triggering a parent reconcile, creating a window of inconsistency.
- **Kind enum rigidity:** `OperandStatus.Kind` is validated as a closed enum. Adding a new SPIRE component requires a CRD schema update and an API version bump, which is a breaking change process.
- **Debugging indirection:** A failing component surfaces in two places (its own CR and the parent's `Operands`). Inconsistency between the two during a race is confusing to debug.
- **String-typed Ready field:** `Ready` is a `string` with pattern `^(true|false)$` rather than a `bool` or `metav1.ConditionStatus`. This is non-idiomatic and may surprise consumers expecting a boolean or condition-style value.
