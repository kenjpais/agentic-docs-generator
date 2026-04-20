---
id: ADR-0002
title: "ZeroTrustWorkloadIdentityManager CR acts as root owner aggregating all operand CRs"
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

# ZeroTrustWorkloadIdentityManager CR as Root Owner and Status Aggregator for All Operand CRs

## Executive Summary
The operator designates the singleton `ZeroTrustWorkloadIdentityManager` (ZTWIM) CR named `cluster` as the Kubernetes controller owner of all subordinate operand CRs (`SpireAgent`, `SpireServer`, `SpiffeCSIDriver`, `SpireOIDCDiscoveryProvider`), and aggregates their individual health conditions into a single `Operands` list on the ZTWIM status. This creates a single authoritative top-level object for operators and tooling to observe and control the entire SPIRE deployment lifecycle.

## What
- `api/v1alpha1/zero_trust_workload_identity_manager_types.go`: defines the ZTWIM CR, its singleton constraint (`name == 'cluster'`), and the `ZeroTrustWorkloadIdentityManagerStatus` with an `Operands []OperandStatus` field indexed by `kind`.
- `pkg/controller/spiffe-csi-driver/controller.go`, `pkg/controller/spire-agent/controller.go`, `pkg/controller/spire-oidc-discovery-provider/controller.go`: each reconciler fetches the ZTWIM `cluster` CR early in reconciliation and sets it as the controller owner reference on the respective operand CR via `controllerutil.SetControllerReference`.
- The decision being captured: ZTWIM owns operand CRs at the Kubernetes object level, and operand status rolls up into the ZTWIM status.

## Why
The SPIRE stack is a multi-component system (server, agent, CSI driver, OIDC provider) that must be installed, configured, and torn down as a coherent unit. Without a single root owner:
- Deleting the ZTWIM CR would leave orphaned operand CRs and their downstream Kubernetes resources.
- Cluster administrators and OLM would have no single object to inspect for overall SPIRE health.
- Each operand controller would need independent lifecycle tracking, duplicating responsibility for install/uninstall coordination.

## Goals
- Enable cascading deletion: removing the ZTWIM CR garbage-collects all operand CRs via Kubernetes owner reference GC.
- Provide a single `kubectl get zerotrustworkloadidentitymanager cluster -o yaml` view of aggregate SPIRE health.
- Allow each operand controller to remain independently focused on its own component while still participating in a unified ownership graph.
- Ensure `ZTWIMSpecChangedPredicate` watches on ZTWIM propagate spec changes into each operand's reconciliation loop.

## Non-Goals
- ZTWIM does not contain low-level SPIRE configuration (delegated to per-operand CRDs per the type comment in `zero_trust_workload_identity_manager_types.go`).
- The ownership pattern does not address cross-operand ordering or dependency sequencing (e.g., SpireServer must be ready before SpireAgent).
- ZTWIM status does not replace the per-operand CR status; it mirrors a summary.

## How
**Owner reference establishment (per reconciler):**
Each reconciler (`SpiffeCsiReconciler`, `SpireAgentReconciler`, `SpireOidcDiscoveryProviderReconciler`) follows an identical pattern early in `Reconcile()`:
1. Fetch the operand CR by `req.NamespacedName`.
2. Fetch `ZeroTrustWorkloadIdentityManager` by hardcoded name `"cluster"`.
3. Call `utils.NeedsOwnerReferenceUpdate(operand, &ztwim)` — a guard to avoid spurious updates.
4. If update needed: call `controllerutil.SetControllerReference(&ztwim, operand, r.scheme)` then `r.ctrlClient.Update(ctx, operand)`.
5. Failure at any step sets a `Ready=False` condition on the operand and returns early.

**Watch propagation:**
Each controller's `SetupWithManager` adds `.Watches(&v1alpha1.ZeroTrustWorkloadIdentityManager{}, handler.EnqueueRequestsFromMapFunc(mapFunc), builder.WithPredicates(utils.ZTWIMSpecChangedPredicate))`. The `mapFunc` always enqueues `{Name: "cluster"}`, so any ZTWIM spec change triggers reconciliation of the operand's `cluster` singleton CR.

**Status aggregation:**
`ZeroTrustWorkloadIdentityManagerStatus.Operands` is a `+listType=map` keyed by `kind`, with entries for each of the four operand kinds. `OperandStatus` carries `Ready string` (pattern-validated `true|false`), `Message`, and mirrored `Conditions`. The ZTWIM controller (not shown in evidence but implied) reads each operand CR's `ConditionalStatus` and writes summarized entries into this list.

**Singleton enforcement:**
A CEL validation rule on the ZTWIM CRD (`self.metadata.name == 'cluster'`) ensures only one instance can exist cluster-wide, making the hardcoded `"cluster"` lookups in all reconcilers safe.

## Alternatives
**Flat ownership (no root CR):** Each operand CR could exist independently with no parent. This was rejected because it provides no unified deletion, no aggregate status surface, and requires cluster admins to monitor four separate CRs.

**ZTWIM owns Kubernetes resources directly:** ZTWIM could own DaemonSets, Deployments, etc. directly. Rejected because it bypasses the per-operand CRD abstraction and merges concerns; per-operand CRDs allow independent configuration and separate reconciliation scopes.

**Label-based grouping without owner references:** Resources could be grouped by labels rather than ownership. Rejected because Kubernetes GC only operates on owner references; label-based cleanup requires explicit deletion logic that is fragile on operator crashes.

## Risks
- **Owner reference on cluster-scoped objects:** Kubernetes restricts cross-namespace owner references. Since ZTWIM is cluster-scoped (`scope=Cluster`), this works, but any future namespace-scoped operand CR would break `SetControllerReference` with a cross-namespace error.
- **Hardcoded `"cluster"` name:** Every reconciler contains `types.NamespacedName{Name: "cluster"}`. If the singleton naming convention changes, this must be updated in every controller; there is no shared constant visible in the evidence.
- **Status aggregation lag:** The ZTWIM aggregate status is only as fresh as the last operand reconciliation cycle. A failed operand controller will not update ZTWIM status, potentially showing stale health data.
- **Cascading deletion risk:** Because owner references enable GC, an accidental deletion of the ZTWIM `cluster` CR will cascade to delete all operand CRs and their downstream resources, which may be surprising to administrators who expect uninstall to be non-destructive (noted tension with the PR description's stated intent that "uninstall should not delete the operand").
