---
id: ADR-0008
title: "Fork of upstream cert-manager imported as a Go module replace directive to an OpenShift-maintained fork"
date: 2021-06-17
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [api/operator]
supersedes: ""
superseded-by: ""
---

# OpenShift Fork of cert-manager via Go Module Replace Directive

## Executive Summary
The operator replaces the canonical `github.com/cert-manager/cert-manager` module with `github.com/openshift/jetstack-cert-manager` at an identical version tag using a single `replace` directive in `go.mod`. This allows all Go source files—including the `IstioCSR` CRD API types in `api/operator/v1alpha1/istiocsr_types.go`—to import cert-manager types under the upstream import path while transparently resolving to an OpenShift-maintained fork, enabling OpenShift-specific patches without duplicating the operator's integration surface.

## What
- **`go.mod`**: A single `replace` directive redirects `github.com/cert-manager/cert-manager` to `github.com/openshift/jetstack-cert-manager` at the same version tag.
- **`api/operator/v1alpha1/istiocsr_types.go`**: Imports `certmanagerv1 "github.com/cert-manager/cert-manager/pkg/apis/meta/v1"` and uses `certmanagerv1.ObjectReference` as the type for `CertManagerConfig.IssuerRef`, embedding cert-manager's issuer reference directly in the `IstioCSR` CRD spec.

## Why
OpenShift distributions of upstream projects routinely require patches (FIPS compliance, OpenShift-specific TLS configuration, backported CVE fixes) that cannot be upstreamed immediately or at all. Without the fork, the operator would be pinned to unpatched upstream binaries. The `replace` directive is the standard Go module mechanism for this: source code imports remain stable and identical to upstream, so no churn propagates to the API types or controller logic when the fork diverges.

## Goals
- Allow OpenShift-specific patches to cert-manager to be applied without changing import paths anywhere in operator source code.
- Embed canonical cert-manager API types (`certmanagerv1.ObjectReference`) in the `IstioCSR` CRD so the schema is consistent with cert-manager's own API surface.
- Keep version alignment explicit: the fork tag mirrors the upstream tag, making it clear which upstream release is the base.
- Limit the operator's exposure to the fork—only the API types package is imported; runtime cert-manager components are deployed separately.

## Non-Goals
- Patching or replacing the cert-manager controller or webhook deployments managed by this operator (those are deployed as separate workloads, not linked as Go packages).
- Upstreaming OpenShift patches to `cert-manager/cert-manager`.
- Maintaining a divergent API schema—the goal is schema identity with upstream, not extension.

## How
The `replace` directive in `go.mod`:
```
replace github.com/cert-manager/cert-manager => github.com/openshift/jetstack-cert-manager v1.19.4
```
is the sole coupling point between the operator build and the fork. The Go toolchain resolves any import of `github.com/cert-manager/cert-manager/...` to the OpenShift fork's module at build time.

In `api/operator/v1alpha1/istiocsr_types.go`, the import alias `certmanagerv1` refers to the meta/v1 package from the (transparently replaced) cert-manager module. The `CertManagerConfig` struct uses `certmanagerv1.ObjectReference` for the `IssuerRef` field, which maps directly to cert-manager's own `ObjectReference` type used by `Issuer` and `ClusterIssuer` resources. This means the CRD schema for `issuerRef` is structurally identical to what cert-manager itself expects, avoiding translation layers or custom type definitions.

No other operator source files need to be aware of the fork. The replacement is invisible to the compiler; engineers reading source code see only the canonical upstream import path.

## Alternatives

**Vendor the cert-manager API types directly (copy/paste into the repo):** Would eliminate the module dependency entirely but creates a maintenance burden of manually syncing type definitions and risks schema drift. Rejected because the `replace` directive achieves the same decoupling with zero duplication.

**Depend directly on `github.com/openshift/jetstack-cert-manager` by import path:** Would require changing all import statements in source files whenever the fork relationship changes, and would make the CRD schema visibly diverge from upstream cert-manager documentation. Rejected because it leaks the fork into the API surface.

**Define custom `IssuerRef` types in the operator's own API package:** Avoids the external dependency entirely but produces a schema incompatible with standard cert-manager tooling and documentation. Rejected because `IstioCSR` users are expected to already have cert-manager issuers and should use familiar field shapes.

**Pin to upstream without a fork:** Acceptable only if no OpenShift-specific patches are needed. Given the distribution requirements (FIPS, security patches), this is not viable for a supported OpenShift product.

## Risks

- **Upstream divergence:** If `github.com/cert-manager/cert-manager` releases a new version and the fork lags behind, the operator is blocked on upgrades until the fork is rebased. Version skew between the tag in `go.mod` and the actual fork content is invisible to the Go toolchain.
- **Fork maintenance burden:** The OpenShift team must continuously rebase `jetstack-cert-manager` against upstream releases, apply patches, and publish matching tags. A lapse breaks the operator's build pipeline.
- **Opaque build provenance:** Engineers inspecting source imports see the upstream path and may not realize a fork is in use, leading to confusion when debugging behaviour differences. The `replace` directive in `go.mod` is the only visible signal.
- **API type skew risk:** If the fork modifies types in `pkg/apis/meta/v1` (e.g., `ObjectReference`), the CRD schema generated from `istiocsr_types.go` will silently diverge from what upstream cert-manager controllers expect, breaking interoperability without a compile-time error.
