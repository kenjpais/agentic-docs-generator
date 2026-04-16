---
id: ADR-0001
title: "Singleton CRD pattern enforced via CEL validation for CertManager and TrustManager, namespaced singleton for IstioCSR"
date: 2021-06-22
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [api/operator]
supersedes: ""
superseded-by: ""
---

# Singleton CRD Pattern via CEL Validation for CertManager, TrustManager, and IstioCSR

## Executive Summary
The operator enforces a singleton-per-scope constraint across its three managed resources—`CertManager` (cluster-scoped, auto-created as `cluster`), `TrustManager` (cluster-scoped, CEL-enforced name `cluster`), and `IstioCSR` (namespace-scoped, CEL-enforced name `default` per namespace)—creating a consistent "one authoritative instance per scope" contract that eliminates ambiguity in operator reconciliation while allowing multi-tenant IstioCSR deployments across namespaces.

## What
- `api/operator/v1alpha1/certmanager_types.go`: `CertManager` struct, cluster-scoped (`+kubebuilder:resource:scope=Cluster`), auto-created by the operator as `cluster` if absent.
- `api/operator/v1alpha1/trustmanager_types.go`: `TrustManager` struct, cluster-scoped, with a type-level CEL rule `self.metadata.name == 'cluster'`.
- `api/operator/v1alpha1/istiocsr_types.go`: `IstioCSR` struct, namespace-scoped (`scope=Namespaced`), with a type-level CEL rule `self.metadata.name == 'default'`.

## Why
An operator reconciling cluster-wide infrastructure components (cert-manager, trust-manager, istio-csr) must have exactly one authoritative configuration source per logical scope. Without this constraint, two users could independently create differently-named `TrustManager` CRs, creating undefined behavior: which instance should the operator reconcile? Which deployment does it own? The singleton pattern makes the answer unambiguous, simplifies the reconciler (it can always `Get` by the known name rather than listing and selecting), and prevents operational split-brain scenarios where multiple configurations fight over shared cluster resources.

## Goals
- Prevent multiple conflicting operator configurations per scope at the API level, not just in controller logic.
- Allow independent IstioCSR deployments in separate namespaces (multi-tenant Istio mesh support) while preserving the per-namespace singleton guarantee.
- Use declarative, admission-time enforcement so invalid names are rejected before any controller logic runs.
- Keep the operator's reconcile loop simple: fetch by well-known name, no disambiguation needed.

## Non-Goals
- Supporting multiple `CertManager` or `TrustManager` instances in the same cluster.
- Providing a general multi-instance operator pattern for these components.
- Enforcing singleton behavior via a validating webhook instead of CEL (CEL is the chosen mechanism).

## How
**TrustManager and IstioCSR — CEL at the type level:** Both types carry a `+kubebuilder:validation:XValidation` marker directly on the struct declaration. For `TrustManager` in `trustmanager_types.go`:
```
+kubebuilder:validation:XValidation:rule="self.metadata.name == 'cluster'",message="TrustManager is a singleton, .metadata.name must be 'cluster'"
```
For `IstioCSR` in `istiocsr_types.go`:
```
+kubebuilder:validation:XValidation:rule="self.metadata.name == 'default'",message="istiocsr is a singleton, .metadata.name must be 'default'"
```
These rules are embedded into the CRD's `x-kubernetes-validations` during `controller-gen` CRD generation. The API server enforces them on every CREATE and UPDATE via CRD validation—no webhook, no controller logic required.

**CertManager — implicit singleton via operator bootstrap:** `CertManager` carries no CEL name rule; instead the operator auto-creates a `CertManager` CR named `cluster` if none exists. This is an older pattern predating the CEL approach (introduced 2021); the constraint is enforced by convention and operator bootstrap logic rather than API validation.

**IstioCSR namespace-scoped flexibility:** Because `IstioCSR` is `scope=Namespaced`, the CEL rule `self.metadata.name == 'default'` permits exactly one `IstioCSR` per namespace. Operators deploying multiple Istio meshes can create one per namespace (`istio-system/default`, `mesh-b/default`), each with its own istio-csr agent deployment, while the reconciler always resolves the canonical instance by the fixed name.

**Reconciler simplification:** Controllers can use `client.Get(ctx, types.NamespacedName{Name: "cluster"}, &cm)` or `types.NamespacedName{Name: "default", Namespace: ns}` without list-and-filter logic, making reconciliation deterministic.

## Alternatives
**Validating Admission Webhook for name enforcement:** A webhook could reject misnamed CRs. This was not chosen because it requires running additional infrastructure (a webhook server with TLS), adds operational risk (webhook unavailability blocks admission), and CEL validation is native to the CRD, available since Kubernetes 1.25, with no runtime dependency.

**Allowing multiple instances with a selector/annotation designating the active one:** Each resource type could allow multiple CRs with a label like `operator.openshift.io/active: "true"`. This adds complexity to the reconciler (list, filter, conflict-detect) and creates ambiguous states when multiple CRs claim the active label. Rejected in favor of simplicity.

**Using a single `CertManagerOperator` singleton CRD for all three components:** Collapsing TrustManager and IstioCSR into sub-specs of CertManager would prevent independent lifecycle management (e.g., installing TrustManager without IstioCSR) and contradicts the composable operator model where each component has its own reconciler and CRD.

## Risks
- **Evolution risk — name constraint migration:** If a future use case requires multiple TrustManager instances cluster-wide (e.g., tenant-isolated trust stores), the `self.metadata.name == 'cluster'` CEL rule becomes a breaking API constraint. Removing it requires a CRD schema revision and careful migration of existing resources.
- **Inconsistency risk — CertManager lacks CEL enforcement:** Unlike TrustManager and IstioCSR, `CertManager` relies on operator bootstrap rather than API validation. A user can manually create a second `CertManager` CR with a different name; the operator will ignore it silently, which may confuse users. Adding a CEL rule to `certmanager_types.go` analogous to TrustManager would close this gap.
- **Namespace proliferation risk:** The per-namespace IstioCSR singleton encourages creating many namespaces to run independent meshes. Each namespace gets its own istio-csr agent deployment, which may be resource-intensive at scale and is not validated against any namespace count limit.
- **Debugging risk:** When a CR creation is rejected by CEL, the error message is clear but the user must know to use the exact canonical name. Documentation and `kubectl explain` output must reinforce this constraint.
