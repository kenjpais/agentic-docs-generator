---
id: ADR-0001
title: "Singleton CRD Pattern with Immutable Fields Enforced via CEL Validation"
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

# Singleton CRD Pattern with Immutable Fields Enforced via CEL Validation

## Executive Summary
Every CRD in this operator is constrained to a single cluster-scoped instance named `cluster`, with security-critical fields marked immutable via CEL `XValidation` rules embedded directly in the Go type markers. This design encodes the operational invariant that a SPIRE deployment is a cluster-wide singleton into the API contract itself, preventing misconfiguration that could silently destroy identity trust chains, orphan persistent volumes, or split federation relationships across conflicting instances.

## What
Five cluster-scoped CRD types in `api/v1alpha1/` — `ZeroTrustWorkloadIdentityManager`, `SpireServer`, `SpireAgent`, `SpiffeCSIDriver`, and `SpireOIDCDiscoveryProvider` — each carry a `+kubebuilder:validation:XValidation` marker enforcing `self.metadata.name == 'cluster'`. `SpireServerSpec` additionally marks `persistence.size`, `persistence.accessMode`, `persistence.storageClass`, and `BundleEndpointConfig.profile` as immutable. `ZeroTrustWorkloadIdentityManagerSpec` marks `trustDomain`, `clusterName`, and `bundleConfigMap` immutable using field-level `self == oldSelf` rules.

## Why
SPIRE's trust model is built on a single trust domain per cluster. Multiple `SpireServer` instances would create competing certificate authorities with no defined authority relationship, silently breaking workload identity. Changing `trustDomain` after issuance would invalidate all live SVIDs. Changing PVC `size`, `accessMode`, or `storageClass` on an existing volume claim is rejected by Kubernetes anyway, but leaving it mutable in the CRD would create a deceptive API surface. The enhancement proposal (SPIRE-26) and the Jira acceptance criteria explicitly require OLM-compatible CRDs; OLM itself recommends singleton patterns for cluster-level operands. Without these guards, a misconfigured `kubectl apply` could pass API validation while leaving the cluster in a broken trust state that is difficult to diagnose.

## Goals
- Prevent creation of multiple competing SPIRE deployments in a single cluster.
- Make destructive field changes (trust domain, persistence, federation profile) a hard API error rather than a silent operational failure.
- Encode operational invariants in the CRD schema so they are enforced by the API server without requiring operator reconciliation logic.
- Provide actionable error messages at admission time (`"SpireServer is a singleton, .metadata.name must be 'cluster'"`).
- Pass OLM bundle validation for OpenShift operator certification.

## Non-Goals
- Multi-tenant or multi-instance SPIRE deployments within a single cluster.
- Migration tooling for changing immutable fields (e.g., no `trustDomain` migration path exists).
- Enforcing cross-CRD consistency (e.g., that `SpiffeCSIDriverSpec.agentSocketPath` matches `SpireAgentSpec.socketPath`) — those cross-resource constraints are left to documentation and reconciliation logic.

## How
**Singleton enforcement** is applied at the resource type level via a `+kubebuilder:validation:XValidation` marker on the struct declaration in each types file. For example, in `spire_server_config_types.go` the `SpireServer` type carries `rule="self.metadata.name == 'cluster'"`. kubebuilder generates this into the CRD's `x-kubernetes-validations` field, which the API server evaluates at admission for both CREATE and UPDATE. A user attempting `kubectl apply -f spire-server-prod.yaml` with `name: prod` receives an immediate rejection.

**Field-level immutability** uses two scopes:
- *Type-level CEL on `SpireServer`*: `oldSelf.spec.persistence.size == self.spec.persistence.size` (and equivalent rules for `accessMode`, `storageClass`) are placed on the type marker block in `spire_server_config_types.go`. These compare old and new object state, which requires the API server to have the stored object — meaning they only fire on UPDATE, not CREATE.
- *Field-level CEL on `ZeroTrustWorkloadIdentityManagerSpec` fields*: `trustDomain`, `clusterName`, and `bundleConfigMap` in `zero_trust_workload_identity_manager_types.go` use `+kubebuilder:validation:XValidation:rule="self == oldSelf"` directly on the field, scoping the comparison tightly.
- *Nested type CEL on `BundleEndpointConfig`*: `profile` immutability (`!has(oldSelf.profile) || oldSelf.profile == self.profile`) and `HttpsWebConfig` mutual-exclusion between `acme` and `servingCert` are encoded on the `BundleEndpointConfig` and `HttpsWebConfig` struct types in `spire_server_config_types.go`.

The `OperandStatus.Kind` field in `ZeroTrustWorkloadIdentityManagerStatus` uses an enum constraint (`SpireServer;SpireAgent;SpiffeCSIDriver;SpireOIDCDiscoveryProvider`) to provide a typed index for operand status, consistent with all operands being named `cluster`.

## Alternatives
**Namespace-scoped CRDs with admission webhook enforcement**: Would allow multiple named instances but require a running webhook for singleton enforcement, adding operational overhead and a potential availability dependency. CEL rules are evaluated in-process by the API server with no external dependency.

**Single monolithic CRD for all SPIRE components**: Would eliminate the multi-instance problem entirely but produce an unmanageable schema and prevent independent status reporting per component. The chosen split into five CRDs with the `OperandStatus` aggregation in `ZeroTrustWorkloadIdentityManager` achieves separation of concern while maintaining a single management entry point.

**Operator-side validation only**: Rejecting bad configurations in the reconciliation loop means errors surface as status conditions rather than admission errors, are harder to discover, and require a running operator to be enforced. CEL validation fires even when the operator is down.

**`+kubebuilder:immutable` on the whole spec**: Would prevent any spec change after creation, which is too restrictive for mutable operational fields like `logLevel`, `replicaCount`, and resource requests.

## Risks
- **Evolution risk**: Adding a new required field to an immutable set (e.g., if `trustDomain` needs a migration mechanism) requires a new API version (`v1beta1`) and a conversion webhook. There is no current upgrade path documented.
- **Bootstrap ordering risk**: CEL `oldSelf` comparisons silently pass on CREATE (old object is null), so there is no validation that `persistence.size` is set to a sane initial value — only that it never changes afterward.
- **Operational risk**: A cluster administrator who needs to change the trust domain (e.g., after a domain rename) has no supported path; the only recourse is to delete and recreate all CRs, which destroys live workload identity.
- **Maintenance burden**: Immutability rules are duplicated across type-level and field-level markers with no shared abstraction, making it easy to add a new field and forget the `XValidation` marker.
