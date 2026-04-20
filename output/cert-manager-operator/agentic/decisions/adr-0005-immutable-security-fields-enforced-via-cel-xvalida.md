---
id: ADR-0005
title: "Immutable security fields enforced via CEL XValidation rules on the CRD"
date: 2021-06-22
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [api/operator]
supersedes: ""
superseded-by: ""
---

# Immutable Security Fields via CEL XValidation on CRD API

## Executive Summary
Security-critical configuration fields in the cert-manager operator CRDs are made immutable at the API layer using Kubernetes CEL XValidation rules, rather than relying on controller-side rejection logic. Once network policies are enabled or issuer references are set, they cannot be reverted or altered, making the operator's security posture a first-class API contract enforced by the API server itself before any controller code runs.

## What
Two CRD types are affected: `CertManager` (`api/operator/v1alpha1/certmanager_types.go`) and `IstioCSR` (`api/operator/v1alpha1/istiocsr_types.go`). The specific fields under immutability constraints are:
- `CertManagerSpec.DefaultNetworkPolicy`: one-way latch from `"false"` → `"true"`, cannot revert
- `CertManagerSpec.NetworkPolicies[*].name` and `.componentName`: keys are immutable once any entry exists
- `IstioCSRConfig.CertManagerConfig.IssuerRef`: immutable once set, presence is also immutable (cannot add or remove)
- `IstiodTLSConfig.privateKeyAlgorithm` and `.privateKeySize`: presence is immutable post-creation

## Why
An operator managing PKI infrastructure (cert-manager) and mTLS certificate issuance for a service mesh (istio-csr) occupies a privileged position in cluster security. Allowing operators or users to silently disable network isolation or swap issuer references after initial deployment creates vectors for accidental or malicious security regression. Without API-level enforcement, the only safeguard would be controller reconciliation logic, which runs asynchronously, can be bypassed during outages, and is invisible to users inspecting the CRD schema. CEL rules surface these constraints as schema-level invariants that appear in `kubectl explain` and are enforced synchronously on every `UPDATE` call.

## Goals
- Prevent disabling of network policies once enabled, at the API admission layer with no controller dependency
- Prevent swapping of cert-manager issuer references after they are established, protecting certificate chain continuity
- Prevent key algorithm and size parameters from changing post-creation, ensuring cryptographic consistency
- Make security invariants self-documenting in the CRD schema and human-readable error messages
- Ensure enforcement is synchronous and cannot be bypassed by restarting or disabling the operator

## Non-Goals
- Does not prevent a user with sufficient RBAC from deleting and recreating the resource entirely
- Does not enforce immutability of operational/scheduling fields (resources, tolerations, nodeSelector)
- Does not replace RBAC controls; assumes appropriate role bindings gate who can update these resources
- Does not cover runtime enforcement of the network policies themselves (that remains the controller's job)

## How
CEL rules are embedded directly as `+kubebuilder:validation:XValidation` markers on field or type declarations, which kubebuilder compiles into `x-kubernetes-validations` in the generated CRD manifest.

**Network policy one-way latch** (`certmanager_types.go`, `DefaultNetworkPolicy` field):
```
rule="oldSelf != 'true' || self == 'true'"
```
The predicate allows any transition except `'true'` → anything-other-than-`'true'`. Combined with the `Enum` constraint (`"true";"false";""`), this is a complete one-way latch.

**NetworkPolicy key immutability** (`CertManagerSpec.NetworkPolicies` slice):
```
rule="oldSelf.all(op, self.exists(p, p.name == op.name && p.componentName == op.componentName))"
```
Every existing `(name, componentName)` pair must survive any update; entries can be added but not removed or renamed. The `+listType=map` with `+listMapKey=name` and `+listMapKey=componentName` markers also enable strategic merge semantics consistent with this contract.

**IssuerRef presence and value immutability** (`istiocsr_types.go`, `CertManagerConfig` type and `IssuerRef` field):
Two layered rules: the type-level rule enforces that presence cannot change (both old and new must either have or lack the field), while the field-level `self == oldSelf` rule enforces value immutability. Additional field-level rules constrain `.kind` and `.group` to valid cert-manager values.

**TLS key parameter presence immutability** (`IstiodTLSConfig` type): same two-sided presence pattern for `privateKeyAlgorithm` and `privateKeySize`, preventing addition or removal post-creation while a cross-field rule validates algorithm/size compatibility at all times.

## Alternatives

**Controller-side rejection (admission webhook or reconcile-loop)**
The controller could detect prohibited changes and emit a status condition or event. Rejected because: enforcement is asynchronous (the bad state is briefly accepted), the constraint is invisible in the schema, and a controller outage removes the guard entirely.

**OpenShift ValidatingWebhook or custom admission webhook**
A separate webhook binary could enforce these rules. Rejected because: it adds operational complexity (webhook deployment, TLS bootstrap, availability requirements) for constraints that are statically known at schema design time. CEL rules require no additional infrastructure.

**Making fields pointer types with immutability in defaulting webhooks**
Using `omitempty` + defaulting to prevent changes. Rejected because it conflates defaulting logic with immutability semantics and still relies on a webhook being available.

**Documentation-only constraints**
Documenting that fields should not be changed without API enforcement. Rejected as insufficient for security-critical invariants in a PKI operator.

## Risks

- **Evolution risk**: If a legitimate need arises to disable network policies (e.g., migrating to a different CNI), there is no supported migration path short of deleting and recreating the `CertManager` resource, which disrupts the operator. The one-way latch should be designed with full awareness that it is permanent.
- **CEL expression correctness**: The `all`/`exists` predicate on `NetworkPolicies` is non-trivial; an error in its logic (e.g., off-by-one on key matching) could silently allow or silently block valid updates. There are no visible unit tests for these CEL expressions in the evidence.
- **Kubernetes version dependency**: CEL validation (`x-kubernetes-validations`) requires Kubernetes 1.25+ (GA in 1.29). Clusters running older versions would silently skip these rules, though OpenShift versions supported by this operator are expected to satisfy this requirement.
- **User confusion**: Error messages from CEL rejections surface through `kubectl` as API server validation errors, which may be unfamiliar to operators expecting controller-emitted status conditions. Message clarity in the `message=` fields partially mitigates this.
