---
id: ADR-0002
title: "Dual controller framework strategy: library-go static resource controllers for core cert-manager, controller-runtime reconcilers for addon components"
date: 2021-07-05
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Dual Controller Framework Strategy: library-go for Core cert-manager, controller-runtime for Addon Components

## Executive Summary
The cert-manager-operator uses two distinct controller frameworks simultaneously: OpenShift's library-go `StaticResourceController` and factory-based controllers for the core cert-manager operand (controller, webhook, cainjector), and controller-runtime `Reconciler` implementations for newer addon components (TrustManager, IstioCSR). This hybrid reflects a deliberate incremental adoption strategy—the core was built to OpenShift operator conventions at founding in 2021, while addons introduced later adopted the broader Kubernetes ecosystem's standard reconciler pattern, which better handles the complex, dynamic watch graphs these components require.

## What
- **Core cert-manager** (controller, webhook, cainjector): managed via `staticresourcecontroller.NewStaticResourceController` and `newGenericDeploymentController` wrappers in `pkg/controller/certmanager/` (e.g., `cert_manager_cainjector_deployment.go`). Returns `factory.Controller` interfaces from library-go.
- **Addon components** (TrustManager, IstioCSR): managed via `controller-runtime` `Reconciler` structs in `pkg/controller/trustmanager/controller.go` and `pkg/controller/istiocsr/controller.go`. Registered via `ctrl.NewControllerManagedBy(mgr)`.
- The decision covers how each subsystem's reconciliation loop is structured, how watches are wired, and how resources are applied.

## Why
The core cert-manager operand consists of a predictable, stable set of static YAML assets (ClusterRole, ClusterRoleBinding, ServiceAccount, Service, Deployment) that map directly to the library-go `StaticResourceController` model: embed assets, apply them idempotently, report status through `v1helpers.OperatorClient`. This pattern is mandated by OpenShift's operator maturity requirements and integrates cleanly with `VersionGetter`, cluster infrastructure informers, and the operator status API.

The addon components (TrustManager, IstioCSR) have meaningfully different requirements: namespace-scoped CRs (IstioCSR is namespace-scoped, unlike the cluster-singleton cert-manager), complex conditional resource creation, cross-resource label-based watch routing, finalizer-driven cleanup, and integration with cert-manager CRDs (`Certificate`, `Issuer`, `ClusterIssuer`) that library-go has no native understanding of. controller-runtime's `SetupWithManager` / `Watches` API handles this with significantly less boilerplate.

## Goals
- Preserve full OpenShift operator compliance (status reporting, version tracking, infrastructure awareness) for the core operand.
- Allow addon controllers to watch arbitrary resource types, including cert-manager CRDs, without fighting library-go's informer model.
- Enable per-instance namespace routing for IstioCSR (multiple namespace-scoped instances).
- Support finalizer-based cleanup for addon CR deletion without requiring library-go finalizer machinery.
- Allow addon controllers to be added independently without modifying the core operand's wiring.

## Non-Goals
- Unifying both subsystems onto a single framework.
- Backporting the addon pattern to the core cert-manager controllers.
- Cross-framework status aggregation (each subsystem manages its own status pathway).

## How
**Core (library-go path):** `NewCertManagerCAInjectorStaticResourcesController` in `cert_manager_cainjector_deployment.go` calls `staticresourcecontroller.NewStaticResourceController`, passing `assets.Asset` (embedded FS) and `certManagerCAInjectorAssetFiles` (a slice of YAML paths). The controller reconciles these files against the cluster on every informer event. The deployment is managed separately via `newGenericDeploymentController`, which injects runtime configuration (trusted CA configmap, cloud credentials, target version). Both return `factory.Controller` and are started by the operator's main run loop alongside other library-go controllers.

**Addon (controller-runtime path):** `pkg/controller/trustmanager/controller.go` defines `Reconciler` embedding `common.CtrlClient`. `SetupWithManager` wires 13+ watches using `handler.EnqueueRequestsFromMapFunc`, all routing to the singleton TrustManager CR name. Predicate stacks (`controllerManagedResources`, `withIgnoreStatusUpdatePredicates`, `injectedCABundleConfigMapPredicate`) prevent reconcile storms. `IstioCSR`'s `SetupWithManager` in `pkg/controller/istiocsr/controller.go` adds a second label key (`IstiocsrResourceWatchLabelName`) that encodes `namespace_name` to support namespace-scoped instance routing—a pattern that would be very awkward to express in library-go.

Both addon `Reconcile` methods follow the same skeleton: fetch CR, handle deletion via `cleanUp` + `removeFinalizer`, add finalizer on first reconcile, then delegate to `processReconcileRequest`.

**Coexistence:** Both frameworks run inside the same process. The library-go controllers use their own goroutine/work-queue model; controller-runtime controllers use the manager's shared work queue. They share no reconcile state but may share informer caches through their respective `SharedInformerFactory` instances.

## Alternatives
**Migrate core to controller-runtime:** Would eliminate the dual-framework complexity but require rebuilding OpenShift-specific integrations (infrastructure config informers, `VersionGetter`, operator status API, `v1helpers.OperatorClientWithFinalizers`) from scratch. The library-go versions are tested and audited by the OpenShift operator team; rebuilding them carries significant regression risk for a component in the critical path of cluster TLS.

**Migrate addons to library-go:** The `StaticResourceController` has no native concept of conditional resource creation, finalizer lifecycle, or watching cert-manager CRDs. Expressing IstioCSR's namespace-routing logic via library-go factory predicates would require significant custom plumbing, eliminating the main benefit of adopting library-go.

**Single unified framework (e.g., pure controller-runtime for everything):** Viable long-term but would require abandoning library-go's `status.VersionGetter` and operator condition machinery, which are required for OpenShift cluster version operator integration.

## Risks
- **Maintenance burden:** Engineers must understand two controller lifecycles, two informer cache models, and two event-delivery guarantees. Bugs that manifest differently across the two frameworks are hard to diagnose.
- **Predicate complexity in addon controllers:** The multi-predicate stacks in `SetupWithManager` (especially IstioCSR's dual-label routing) are subtle. A wrong predicate causes silent reconcile suppression with no obvious failure signal.
- **Framework divergence over time:** As library-go and controller-runtime evolve independently, shared assumptions (e.g., how leader election interacts with work queues) may drift, creating subtle race conditions in the combined process.
- **Inconsistent status reporting:** Core and addon components report status through different mechanisms. Aggregating health signals across the two subsystems requires understanding both pathways, increasing risk of incomplete operator status during partial failures.
