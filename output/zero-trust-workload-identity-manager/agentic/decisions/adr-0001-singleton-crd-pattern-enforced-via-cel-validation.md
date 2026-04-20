---
id: ADR-0001
title: "Singleton CRD pattern enforced via CEL validation across all component APIs"
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

# Singleton CRD Pattern Enforced via CEL Validation

## Executive Summary
Every SPIRE component CRD in this operator enforces a hard singleton constraint via CEL XValidation rules that reject any resource whose `metadata.name` is not `cluster`. This design decision, introduced in the initial API commit, deliberately limits each cluster to exactly one instance of each SPIRE component, eliminating an entire class of multi-tenancy problems at the API layer and allowing the reconciler to assume a single, well-known object name rather than tracking arbitrary resource inventories.

## What
Five cluster-scoped CRD types are affected: `SpireServer`, `SpireAgent`, `SpiffeCSIDriver`, `SpireOIDCDiscoveryProvider`, and `ZeroTrustWorkloadIdentityManager`, defined in `api/v1alpha1/`. Each carries the marker `+kubebuilder:validation:XValidation:rule="self.metadata.name == 'cluster'"` directly on the type declaration, meaning the Kubernetes API server rejects any create or update request that violates this constraint before it reaches the operator.

## Why
SPIRE is architecturally a cluster-wide identity plane: one trust domain, one set of root CAs, one agent DaemonSet per node. Running multiple SPIRE servers in the same cluster with the same trust domain creates split-brain scenarios for attestation and certificate issuance. Without the singleton constraint, an operator reconciler must either arbitrate between competing instances (complex) or silently ignore duplicates (dangerous). Enforcing uniqueness at admission time means the problem never enters the system. It also allows the `ZeroTrustWorkloadIdentityManagerStatus.Operands` list to index entries by `kind` alone (visible in `zero_trust_workload_identity_manager_types.go`: `// Operands are indexed by their kind since all operands are named "cluster"`), confirming the reconciler is built around this assumption.

## Goals
- Prevent conflicting SPIRE configurations within a single cluster at API admission time, not at reconcile time.
- Allow reconcilers to use a fixed, predictable object key (`/cluster`) without list-and-select logic.
- Provide an immediately actionable error message to operators who attempt to create a second instance.
- Keep status aggregation in `ZeroTrustWorkloadIdentityManagerStatus` simple by using `kind` as the unique key.

## Non-Goals
- Multi-tenant or namespace-scoped SPIRE deployments are not supported.
- Federation between multiple clusters is handled via `FederationConfig` in `SpireServerSpec`, not via multiple `SpireServer` instances.
- The singleton constraint does not address HA within a single component (e.g., `SpireOIDCDiscoveryProvider` supports `replicaCount` 1–5 for its underlying pods).

## How
Each type file annotates the root struct with a `+kubebuilder:validation:XValidation` marker:

```
// api/v1alpha1/spire_server_config_types.go
// +kubebuilder:validation:XValidation:rule="self.metadata.name == 'cluster'",message="SpireServer is a singleton, .metadata.name must be 'cluster'"

// api/v1alpha1/spire_agent_config_types.go
// +kubebuilder:validation:XValidation:rule="self.metadata.name == 'cluster'",message="SpireAgent is a singleton, .metadata.name must be 'cluster'"
```

controller-gen compiles these markers into `x-kubernetes-validations` in the generated CRD OpenAPI schema. The Kubernetes API server evaluates the CEL expression on every admission request; no webhook is required. The rule fires on both CREATE and UPDATE because CEL object-level rules are evaluated unconditionally unless the rule references `oldSelf`.

The reconciler consequence is visible in `ZeroTrustWorkloadIdentityManagerStatus`: the `Operands` field uses `+listMapKey=kind`, meaning the composite key for deduplication is `kind` alone—only valid if `name` is always `cluster`. Any code that fetches a component resource can do so with a hardcoded `types.NamespacedName{Name: "cluster"}` lookup rather than a list call.

`SpireServer` additionally layers immutability constraints on persistence fields (`spec.persistence.size`, `spec.persistence.accessMode`, `spec.persistence.storageClass`) and federation removal using `oldSelf`-referencing CEL rules on the same type, demonstrating a consistent pattern of using CEL for all admission-time invariants.

## Alternatives

**Namespace-scoped resources with name uniqueness via webhook**: A validating admission webhook could enforce the singleton. This was not chosen because webhooks introduce operational dependencies (the webhook server must be available for the API to function), whereas CEL runs in-process in the API server and requires no additional components.

**Multiple instances with operator-side arbitration (leader election among CRs)**: The operator could accept multiple instances and designate one as active. This adds significant reconciler complexity and creates ambiguity about which instance wins, which is antithetical to a security-sensitive identity platform.

**Single CRD with no name restriction, documented convention only**: Relying on documentation without enforcement allows accidental duplicate creation, especially in GitOps workflows where concurrent applies can race.

**Using `generateName` and admission webhooks to enforce count**: Admission webhooks checking the existing object count are non-atomic and prone to race conditions under concurrent creates.

## Risks

- **Evolution risk**: If a future requirement demands multiple SPIRE deployments per cluster (e.g., isolated tenant trust domains), the CEL constraint must be removed and the reconciler redesigned from the ground up. The assumption is deeply embedded in the status type's `listMapKey=kind` design.
- **Operational risk**: Administrators accustomed to Kubernetes multi-instance patterns will receive a cryptic API rejection. The error messages are explicit but the constraint is non-obvious from cluster inspection alone.
- **Maintenance risk**: The singleton rule is copy-pasted across five files with no shared abstraction. If the rule logic needs to change (e.g., allowing a second name), all five files must be updated consistently.
