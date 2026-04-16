---
id: ADR-0005
title: "Optional cert-manager Integration via Runtime CRD Discovery"
date: 2025-03-04
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [cmd/external-secrets-operator, pkg/controller]
supersedes: ""
superseded-by: ""
---

# Optional cert-manager Integration via Runtime CRD Discovery

## Executive Summary
The operator implements optional cert-manager integration by probing the Kubernetes API server for the cert-manager `Certificate` CRD at startup rather than requiring it as a hard dependency. This allows the operator to deploy and function in clusters without cert-manager while transparently enabling CA injection annotation management on external-secrets CRDs when cert-manager is present.

## What
- `pkg/controller/external_secrets/controller.go`: CRD probe logic (`isCRDInstalled`, `checkAndRegisterCertificates`), conditional Certificate informer registration, and `NewCacheBuilder` which decides whether to include cert-manager objects in the manager cache.
- `pkg/controller/crd_annotator/controller.go`: The `crd-annotator` controller, conditionally activated, reconciles `cert-manager.io/inject-ca-from` annotations onto external-secrets CRDs.
- `cmd/external-secrets-operator/main.go`: Wires the pre-startup CRD check into the manager's `NewCache` option via `escontroller.NewCacheBuilder`.
- The `operatorv1alpha1.ExternalSecretsConfig` CR's `IsInjectCertManagerAnnotationEnabled` gate controls whether `crd-annotator` reconciliation is active at runtime.

## Why
External-secrets-operator must run on OpenShift clusters where cert-manager may or may not be installed. Hardcoding cert-manager as a required dependency would fail manager startup when cert-manager CRDs are absent—`controller-runtime`'s cache panics if it attempts to create an informer for an unregistered API group. Conversely, silently skipping the annotation means webhook CA rotation breaks in clusters that do have cert-manager. The design thread-needles this by making the dependency detectable and harmlessly absent.

## Goals
- Allow the operator to start and operate fully in clusters without cert-manager installed.
- Automatically enable CA injection annotation reconciliation when cert-manager is detected.
- Prevent cache startup failures from attempting to watch non-existent CRDs.
- Gate annotation logic behind a user-controlled field in `ExternalSecretsConfig`, giving operators explicit opt-in control.
- Keep cert-manager types registered in the scheme (`certmanagerv1.AddToScheme`) for type-safe API interactions when present.

## Non-Goals
- Installing or managing cert-manager itself.
- Dynamically re-detecting cert-manager after the operator has started (detection is startup-only).
- Handling cert-manager version incompatibilities beyond CRD group/version presence.
- Providing a fallback CA injection mechanism when cert-manager is absent.

## How
**Startup probe (before cache creation):**
`main.go` calls `escontroller.NewCacheBuilder(restConfig)` before `ctrl.NewManager`. Inside `NewCacheBuilder`, `isCRDInstalled` issues a direct discovery call against the API server checking for the `certificateCRDName` in `certificateCRDGroupVersion`. The result (`certManagerExists bool`) is captured in a closure.

**Cache configuration:**
The closure returned by `NewCacheBuilder` is passed as `ctrl.Options.NewCache`. When the manager initializes its cache, `buildCacheObjectList(certManagerExists)` is called. If cert-manager was detected, `certmanagerv1.Certificate` is added to the `cache.ByObject` map; otherwise it is omitted entirely, preventing the informer registration that would crash on a missing API group.

**Controller initialization:**
In `pkg/controller/external_secrets/controller.go`'s `New()`, `checkAndRegisterCertificates` runs a second probe and, if cert-manager is present, registers a `Certificate` informer with the already-configured manager cache and adds `certmanagerv1.Certificate` watch targets to the controller's watch list.

**Annotation reconciliation:**
The `crd-annotator` controller (`pkg/controller/crd_annotator/controller.go`) maintains its own label-filtered custom cache (`BuildCustomClient`) over `CustomResourceDefinition` and `ExternalSecretsConfig` objects. Its `Reconcile` method checks `common.IsInjectCertManagerAnnotationEnabled(esc)` before acting. When enabled, `updateAnnotations` applies the `cert-manager.io/inject-ca-from` annotation via a `MergePatch` to each CRD labeled `external-secrets.io/component=controller`. Changes to `ExternalSecretsConfig` trigger full re-annotation via `updateAnnotationsInAllCRDs`.

**Conditional controller registration:**
`operator.StartControllers` (called from `main.go`) is where the `crd-annotator` controller is conditionally added to the manager—only when cert-manager was detected at startup.

## Alternatives
**Hard dependency / always-required cert-manager:** Simplest code path but breaks installations without cert-manager, which is not acceptable in the OpenShift ecosystem where cert-manager is optional.

**Operator flag (`--enable-cert-manager`):** A CLI flag would make the choice explicit but requires cluster administrators to know cert-manager status at deploy time and keep the flag synchronized with actual cluster state—an operational burden. Runtime detection is self-healing.

**Webhook-based CA injection (OLM/service-ca):** OpenShift's service-ca operator provides an alternative CA injection mechanism. The design does not preclude this but the cert-manager path supports non-OLM and upstream Kubernetes deployments where service-ca is absent.

**Polling/re-detection loop:** Continuously checking for cert-manager post-startup would handle late installations but adds complexity and could cause informer churn. The startup-only model is simpler and restart-on-change is acceptable for an operator-level dependency shift.

## Risks
- **Stale detection state:** cert-manager installed or removed after operator startup requires an operator restart to take effect. This is undocumented behavior that can confuse operators.
- **Dual probe redundancy:** `isCRDInstalled` is called twice—once in `NewCacheBuilder` and once in `checkAndRegisterCertificates`—with a race window between them. A cert-manager installation or removal in this window could produce inconsistent cache vs. informer state.
- **Silent annotation gap:** If the `ExternalSecretsConfig` flag is enabled but cert-manager was absent at startup, the `crd-annotator` controller is never registered, yet no error surfaces to the user—the CRDs simply never get annotated.
- **Discovery API availability:** The startup probe uses the discovery client directly; transient API server unavailability at startup causes cert-manager to be treated as absent for the lifetime of the process.
- **Scheme registration unconditional:** `certmanagerv1.AddToScheme` always runs in `init()` regardless of detection, meaning the scheme carries cert-manager types even when the feature is inactive—a minor memory cost but not a correctness risk.
