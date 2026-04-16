---
id: ADR-0006
title: "Optional API discovery pattern for infrastructure-specific informers (e.g., OpenShift Infrastructure API)"
date: 2026-04-06
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [pkg/controller, pkg/operator]
jira: CM-871
supersedes: ""
superseded-by: ""
---

# Optional API Discovery Pattern for Infrastructure-Specific Informers

## Executive Summary
The operator uses a GVR-scoped discovery abstraction (`ResourceDiscoverer` / `OptionalInformer`) to probe the API server at startup for optional OpenShift APIs—specifically the Infrastructure and FeatureGate GroupVersionResources. When an API is absent the informer factory is held as `nil` and controllers adapt accordingly, allowing the operator to run unchanged on plain Kubernetes, MicroShift, and full OpenShift clusters without startup failures or panics.

## What
- `pkg/operator/utils/apidiscovery.go` defines `ResourceDiscoverer`, `OptionalInformer[T]`, `NewResourceDiscoverer`, and `InitInformerIfAvailable`.
- `pkg/controller/certmanager/cert_manager_cainjector_deployment.go` (and its siblings) accept `utils.OptionalInformer[configinformers.SharedInformerFactory]` as a constructor parameter instead of a concrete informer factory.
- The decision being made is: *how* the operator discovers and conditionally wires optional OpenShift API informers—using a typed, nullable wrapper rather than build-time feature flags or panic-on-missing registration.

## Why
The operator must run on clusters that do not serve `config.openshift.io` APIs (MicroShift, vanilla Kubernetes). Unconditionally registering informers against absent GroupVersionResources causes the informer cache sync to stall or crash. At the same time, silently treating transient discovery errors as "API absent" would incorrectly enable or suppress controllers (e.g., TrustManager gated on FeatureGates). A discoverer that distinguishes "404 not found" from "unexpected error" is needed to be both resilient and fail-safe.

## Goals
- Allow the operator binary to start successfully on clusters missing OpenShift-specific APIs.
- Differentiate between "API definitively absent" (HTTP 404) and "discovery failed" (other errors, treated as fatal).
- Provide a reusable, generic abstraction so future optional APIs (FeatureGate, Infrastructure) follow the same pattern.
- Let controllers introspect API availability at reconcile time via `OptionalInformer.Applicable()` rather than embedding environment checks throughout business logic.

## Non-Goals
- Runtime re-discovery if an API appears or disappears after startup (discovery is one-shot).
- Graceful degradation for *required* APIs—only optional, environment-specific APIs use this pattern.
- Feature-flag management beyond binary present/absent semantics.

## How
**Discovery layer** (`pkg/operator/utils/apidiscovery.go`):
`apiResourceDiscoverer` calls `discovery.DiscoveryInterface.ServerResourcesForGroupVersion(groupVersion)` for a specific GVR. A `k8s.io/apimachinery/pkg/api/errors.IsNotFound` response returns `(false, nil)`; any other error propagates up. This intentionally uses `ServerResourcesForGroupVersion` (precise, single GV call) rather than the broader `ServerPreferredResources` to avoid over-fetching and to get a deterministic 404 for missing API groups.

**Conditional informer wiring** (`InitInformerIfAvailable[T]`):
The generic function calls `Discover()`, invokes the factory constructor only on success, and stores the result in `OptionalInformer[T].InformerFactory`. If absent, the pointer stays `nil`. The `Applicable()` method provides a readable guard for controllers.

**Controller integration** (`cert_manager_cainjector_deployment.go`):
`NewCertManagerCAInjectorDeploymentController` accepts `infraInformers utils.OptionalInformer[configinformers.SharedInformerFactory]` by value. Inside `newGenericDeploymentController`, a guard on `infraInformers.Applicable()` decides whether to register Infrastructure informer event handlers or skip them. Controllers that need Infrastructure data (e.g., proxy, cloud credentials) simply no-op those code paths on non-OpenShift clusters.

**Startup wiring** (operator entrypoint, not shown in snippets):
`NewResourceDiscoverer` is called once per optional GVR during `RunOperator`, and the resulting `OptionalInformer` is threaded into every controller constructor that needs it—keeping discovery logic out of the reconcile loop.

## Alternatives
**Build-time tags / environment variables**: Would require separate builds or explicit cluster-type configuration. Rejected because the operator should be a single binary that auto-adapts.

**Attempting to start all informers and recovering panics/errors**: Informer cache sync failures are not easily recoverable; this would produce degraded operator states that are hard to diagnose.

**`ServerPreferredResources` instead of `ServerResourcesForGroupVersion`**: Fetches all API groups and is more expensive. Also aggregates partial errors, making it harder to distinguish "this specific GV is absent" from "some unrelated discovery call failed."

**Interface injection without the generic wrapper**: Passing `nil` interface values or `*configinformers.SharedInformerFactory` pointers directly loses the semantic distinction between "not initialized yet" and "intentionally absent," and requires nil checks scattered across call sites without a named contract.

## Risks
- **One-shot discovery**: If the API server is temporarily unavailable at startup, the operator may permanently treat a real API as absent for the lifetime of the pod, requiring a restart to recover.
- **Silent no-op behaviour**: When `Applicable()` returns false, features silently degrade. This can be confusing during debugging if an operator is accidentally pointed at a cluster missing expected APIs.
- **Generic type constraints**: `OptionalInformer[T]` uses Go generics. Controllers must pass the correct concrete factory type; a mismatch is a compile error but can lead to multiple near-duplicate `OptionalInformer` instantiations if future APIs are added carelessly.
- **Evolution**: Adding a new optional API requires threading a new `OptionalInformer` parameter through potentially many constructor call sites, increasing boilerplate as the number of optional APIs grows.
