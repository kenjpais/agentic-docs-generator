---
id: ADR-0007
title: "Immutability enforcement on critical SpireServer fields via CEL XValidation rules"
date: 2025-05-26
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [api/v1alpha1]
jira: SPIRE-28

enhancement-refs:
  - repo: "openshift/enhancements"
    number: 1775
    title: "SPIRE-26: Proposal for zero trust workload identity manager"
supersedes: ""
superseded-by: ""
---

# Immutability Enforcement on Critical SPIRE Fields via CEL XValidation Rules

## Executive Summary
The operator enforces immutability on a carefully selected set of SPIRE fields directly at the CRD validation layer using Kubernetes CEL `XValidation` rules, preventing in-place mutations that would require destructive data migration or produce an inconsistent trust fabric. This shifts enforcement left into the API server admission webhook rather than into reconciler logic, making violations user-visible immediately and eliminating entire classes of operator error-handling complexity.

## What
Two API types in `api/v1alpha1/` carry immutability constraints:

- **`SpireServer`** (`spire_server_config_types.go`): Persistence fields (`spec.persistence.size`, `spec.persistence.accessMode`, `spec.persistence.storageClass`) and the federation bundle endpoint profile (`BundleEndpointConfig.profile`) are immutable via `oldSelf == self` rules on the `SpireServer` struct. Additionally, once `spec.federation` is set it cannot be removed. The `HttpsWebConfig` type also prevents switching between `acme` and `servingCert` sub-configurations.
- **`ZeroTrustWorkloadIdentityManager`** (`zero_trust_workload_identity_manager_types.go`): `spec.trustDomain`, `spec.clusterName`, and `spec.bundleConfigMap` each carry field-level `self == oldSelf` rules on `ZeroTrustWorkloadIdentityManagerSpec`.

## Why
SPIRE's trust model depends on stable, consistent identifiers and storage:

- **Trust domain and cluster name** are embedded in every SPIFFE ID and federation relationship. Changing them post-issuance invalidates all live SVIDs and breaks federation with peer clusters.
- **Bundle ConfigMap name** is referenced by agents and federated parties; renaming it silently breaks bundle distribution.
- **Persistence fields** back a stateful PVC for SPIRE's internal datastore. Changing size or storage class cannot be applied to an existing PVC without delete-and-recreate, which destroys all registration entries and keys.
- **Federation profile** determines the TLS authentication model; switching it mid-lifecycle would require coordinated re-trust with all federated peers.

Without enforcement, operators or automation could submit mutations that the reconciler would silently ignore or only partially apply, creating invisible drift.

## Goals
- Reject mutating API calls at admission time with human-readable error messages, before any reconciler runs.
- Protect persistence-backed state from destructive re-provisioning triggered by accidental field changes.
- Preserve SPIFFE trust domain integrity across the full workload lifetime.
- Prevent removal of federation configuration once established with remote peers.
- Enforce certificate provisioning strategy stability within `HttpsWebConfig`.

## Non-Goals
- Providing a migration path for changing immutable fields (users must delete and recreate the singleton resource).
- Enforcing immutability for mutable operational fields (log level, resource requests, tolerations, TTL values).
- Runtime reconciler-level guards as a fallback; CEL is the sole enforcement mechanism.

## How
All rules are expressed as `+kubebuilder:validation:XValidation` marker comments, compiled into the CRD's `x-kubernetes-validations` schema by controller-gen. The Kubernetes API server evaluates them via its built-in CEL admission engine on every `UPDATE` operation—no webhook or operator code is involved.

**Resource-level rules on `SpireServer`** use `oldSelf.spec.persistence.size == self.spec.persistence.size` (and analogous rules for `accessMode`, `storageClass`). These live on the top-level struct so they have access to the full old and new object graph. The federation removal guard uses the pattern `!has(oldSelf.spec.federation) || has(self.spec.federation)` with a null-safety prefix, correctly handling the initial creation case where `oldSelf` is null.

**Field-level rules on `ZeroTrustWorkloadIdentityManagerSpec`** use the simpler `self == oldSelf` form placed directly on each field (`TrustDomain`, `ClusterName`, `BundleConfigMap`), which is idiomatic for scalar immutability.

**Sub-object rules on `BundleEndpointConfig`** and `HttpsWebConfig` guard profile switching using `!has(oldSelf.profile) || oldSelf.profile == self.profile` and prevent toggling between `acme` and `servingCert` once either is set.

Both CRDs enforce the singleton pattern (`self.metadata.name == 'cluster'`) at the same layer, establishing a consistent validation philosophy across the entire API surface.

## Alternatives

**Reconciler-level immutability checks**: The operator could compare old and new field values inside its reconcile loop and emit a degraded condition. This was not chosen because it allows the invalid object to persist in etcd, requires every reconciler to duplicate the logic, and produces delayed rather than immediate feedback.

**Defaulting webhooks with field locking**: A mutating webhook could overwrite changed fields with their original values. This silently discards user intent, complicates debugging, and adds operational overhead of a running webhook.

**Separate versioned CRDs (v1alpha1 → v1alpha2)**: Schema promotion could treat each configuration as a new version. This is appropriate for breaking changes across releases but is too heavyweight for preventing accidental in-place edits within a single version.

## Risks

- **Evolution risk**: If a legitimate use case for changing a persistence field emerges (e.g., online PVC expansion support), the immutability rule must be relaxed via a CRD schema version bump—there is no escape hatch without a breaking API change.
- **Operational risk**: Users who need to change trust domain or cluster name must delete the singleton and lose all registration state. The error messages, while descriptive, do not explain this recovery procedure.
- **Maintenance risk**: CEL rules are strings in marker comments with no compile-time type checking. Typos or logic errors (especially in `has()` guards) will only surface during integration testing or in-cluster validation.
- **Upgrade risk**: Tightening CEL rules in a future release could reject previously-valid objects already stored in etcd, requiring a migration step before the operator upgrade can proceed.
