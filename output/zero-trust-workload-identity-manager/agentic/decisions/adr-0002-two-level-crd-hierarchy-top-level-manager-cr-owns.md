---
id: ADR-0002
title: "Two-Level CRD Hierarchy: Top-Level Manager CR Owns Component CRs"
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

# Two-Level CRD Hierarchy: ZeroTrustWorkloadIdentityManager as Root Owner of Component CRs

## Executive Summary
The operator uses a two-tier CRD hierarchy where a singleton cluster-scoped `ZeroTrustWorkloadIdentityManager` (ZTWIM) CR holds immutable cluster-wide identity configuration (`trustDomain`, `clusterName`, `bundleConfigMap`) and dynamically becomes the Kubernetes owner of each component CR (`SpireAgent`, `SpiffeCSIDriver`, `SpireOIDCDiscoveryProvider`, etc.) during reconciliation. This separates global trust-domain policy from per-component tuning, enables cascading deletion, and provides a single authoritative source of truth for cross-cutting identity configuration consumed by all component controllers.

## What
- `api/v1alpha1/zero_trust_workload_identity_manager_types.go` defines `ZeroTrustWorkloadIdentityManager`, a cluster-scoped singleton (name must be `"cluster"`) with immutable fields for `trustDomain`, `clusterName`, and `bundleConfigMap`.
- Each component controller (`pkg/controller/spiffe-csi-driver/controller.go`, `pkg/controller/spire-agent/controller.go`, `pkg/controller/spire-oidc-discovery-provider/controller.go`) fetches the ZTWIM CR by hardcoded name `"cluster"` and sets it as the `controllerutil.SetControllerReference` owner of the component CR.
- The ZTWIM `Status.Operands` field aggregates health across all component CRs.

## Why
SPIRE components share foundational identity configuration—particularly `trustDomain`—that must be consistent cluster-wide and should be immutable after initial deployment. Without a root CR owning this config, each component CR would either duplicate it (creating drift risk) or require an implicit convention for how components discover it. The enhancement proposal (SPIRE-26) explicitly calls for a single operator-level API distinct from low-level SPIRE tuning. The owner-reference relationship provides automatic garbage collection: deleting the ZTWIM triggers cascading deletion of all component CRs.

## Goals
- Single point of truth for cluster-wide SPIFFE identity parameters consumed by all component controllers.
- Kubernetes-native garbage collection via owner references without manual cleanup logic.
- Aggregated health status on ZTWIM (`Status.Operands`) giving operators a single-pane view.
- Immutability enforcement on identity-critical fields (`trustDomain`, `clusterName`, `bundleConfigMap`) via CEL validation rules in the CRD.
- Change propagation: each component controller watches `ZeroTrustWorkloadIdentityManager` with `ZTWIMSpecChangedPredicate` so any global config change triggers re-reconciliation of all components.

## Non-Goals
- ZTWIM does not configure low-level SPIRE parameters (log levels, ports, plugin config)—those live in component-specific CRs.
- ZTWIM does not directly manage Kubernetes workload resources (DaemonSets, Deployments); that is delegated to component controllers.
- Multi-instance or namespace-scoped deployments are not supported; the singleton constraint is hard-coded.

## How
**Schema and singleton enforcement:** `ZeroTrustWorkloadIdentityManagerSpec` in `api/v1alpha1/zero_trust_workload_identity_manager_types.go` uses `+kubebuilder:validation:XValidation:rule="self.metadata.name == 'cluster'"` to enforce exactly one instance. Fields `trustDomain`, `clusterName`, and `bundleConfigMap` carry `self == oldSelf` CEL immutability rules.

**Dynamic owner-reference wiring:** Each component reconciler (e.g., `SpiffeCsiReconciler.Reconcile`) follows the same pattern:
1. Fetch the component CR (`SpiffeCSIDriver`, `SpireAgent`, etc.).
2. Fetch ZTWIM by `types.NamespacedName{Name: "cluster"}`.
3. Call `utils.NeedsOwnerReferenceUpdate` to check if the owner reference is already set correctly.
4. If not, call `controllerutil.SetControllerReference(&ztwim, &componentCR, r.scheme)` then `r.ctrlClient.Update`.

**Global config propagation:** For resources needing `trustDomain` or `bundleConfigMap` (e.g., `reconcileConfigMap` and `reconcileDaemonSet` in the spire-agent and OIDC controllers), the ZTWIM pointer `&ztwim` is passed directly into those sub-reconcilers.

**Reactive re-reconciliation:** `SetupWithManager` in each controller watches `v1alpha1.ZeroTrustWorkloadIdentityManager` with `builder.WithPredicates(utils.ZTWIMSpecChangedPredicate)`. The `mapFunc` always enqueues `{Name: "cluster"}` for the component CR, so any ZTWIM spec change triggers full re-reconciliation of all component controllers.

**Status aggregation:** `ZeroTrustWorkloadIdentityManagerStatus.Operands` is a list of `OperandStatus` keyed by `kind`, enabling the ZTWIM controller to surface per-component health in a single CR.

## Alternatives
**Flat single CR containing all component config:** One CR with embedded sub-specs for each SPIRE component. Rejected because it conflates immutable cluster-identity policy with mutable per-component tuning, creates a large monolithic API surface, and prevents independent versioning of component config.

**ConfigMap or Secret for global config:** Cluster-wide config stored in a well-known ConfigMap rather than a CR. Rejected because it lacks schema validation, status reporting, and the owner-reference garbage-collection mechanism that a CRD provides.

**Component CRs directly owning each other or being owned by a non-singleton CR:** Would allow multiple SPIRE deployments per cluster. Rejected per SPIRE-26 design goal of a single managed deployment; the singleton constraint simplifies trust-domain consistency guarantees.

## Risks
- **Reconciliation ordering fragility:** Each component reconciler hard-codes `Name: "cluster"` and fails with a non-retried `ctrl.Result{}` when ZTWIM is not found. If a component CR is created before ZTWIM (e.g., by a user), it stalls silently until ZTWIM is created.
- **Owner-reference on cluster-scoped resources:** Setting a cluster-scoped owner (ZTWIM) on other cluster-scoped CRs is valid, but garbage collection behavior for cluster-scoped owners of cluster-scoped owned objects requires Kubernetes 1.20+ and can behave unexpectedly across namespace boundaries if component CRs are ever made namespaced.
- **Immutability risk:** CEL `self == oldSelf` rules on `trustDomain` and `clusterName` make recovery from misconfiguration require deleting and recreating the ZTWIM, which cascades deletion to all component CRs and their managed workloads—a potentially disruptive operation in production.
- **Duplicated owner-reference pattern:** All three observed controllers duplicate the fetch-then-conditionally-set-owner-reference logic verbatim; any bug in this pattern must be fixed in multiple places.
