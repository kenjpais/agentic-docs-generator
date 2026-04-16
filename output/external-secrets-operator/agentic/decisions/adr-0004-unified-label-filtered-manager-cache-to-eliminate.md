---
id: ADR-0004
title: "Unified Label-Filtered Manager Cache to Eliminate Dual-Cache Race Condition"
date: 2025-03-04
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [cmd/external-secrets-operator, docs/anti-patterns, pkg/controller]
supersedes: ""
superseded-by: ""
---

# Unified Label-Filtered Manager Cache to Eliminate Dual-Cache Race Condition

## Executive Summary
The external-secrets-operator replaced a dual-cache architecture—where the manager cache triggered reconciliation and a separate custom cache served reads—with a single manager cache configured with `app=external-secrets` label selectors. This eliminates a startup race condition where reconcilers could read from an unsynced secondary cache, halving watch connections and memory overhead while following the same pattern validated in the OpenShift cert-manager-operator.

## What
- **`cmd/external-secrets-operator/main.go`**: Passes `NewCache: escontroller.NewCacheBuilder(restConfig)` to `ctrl.NewManager`, injecting label-filtered cache configuration at manager initialization.
- **`pkg/controller/external_secrets/controller.go`**: Implements `NewCacheBuilder()`, `buildCacheObjectList()`, and a simplified `NewClient()` that wraps `m.GetClient()` directly instead of constructing a custom cache client. The `Reconciler` retains a separate `UncachedClient` for objects not managed by the controller.
- **`docs/anti-patterns/DUAL_CACHE_FIX.md`**: Documents the race condition, the fix, and the architectural comparison for future maintainers.

## Why
The previous design maintained two independent caches: the manager's default cache (for watch events and reconcile triggering) and a custom label-filtered cache (for Get/List reads during reconciliation). Because these caches synchronized independently from the API server, a reconcile loop triggered by the manager cache could execute before the custom cache had synced the same objects, producing spurious "object not found" errors. Controller-runtime only guarantees that its own cache is synced before reconciliation begins—a guarantee that cannot extend to an externally managed cache.

## Goals
- Eliminate the race between reconcile trigger and object read by ensuring both use the same cache instance.
- Reduce API server watch connections and in-memory object storage by ~50%.
- Remove ~100 lines of custom cache management code (`BuildCustomClient` and associated logic).
- Preserve label-filtered watching so the cache only holds objects with `app=external-secrets`, avoiding unbounded memory growth.
- Handle the optional cert-manager `Certificate` CRD by pre-checking CRD existence before cache construction and registering informers conditionally via `checkAndRegisterCertificates()`.

## Non-Goals
- Does not change the operator's external API or CRD schema.
- Does not address objects that legitimately bypass the cache; those continue to use the `UncachedClient` (`NewUncachedClient` wraps a raw `client.New`).
- Does not eliminate leader election or other manager-level concerns.

## How
**Cache construction** (`NewCacheBuilder` in `controller.go`): Called before `ctrl.NewManager`, it pre-checks for the cert-manager CRD via `isCRDInstalled` using a discovery client against `restConfig`. It returns a `cache.NewCacheFunc` closure that calls `buildCacheObjectList(certManagerExists)` to populate `cache.Options.ByObject`. Each entry in `controllerManagedResources` (Deployments, RBAC types, Services, Secrets, ConfigMaps, NetworkPolicies, ValidatingWebhookConfigurations, etc.) is mapped to a `cache.ByObject` with a label selector requiring `app=external-secrets`. If cert-manager is present, the `Certificate` type is added to the same map.

**Manager wiring** (`main.go`): `ctrl.NewManager` receives the cache builder via `ctrl.Options{NewCache: cacheBuilder}`. From this point, `mgr.GetClient()` reads through this label-filtered cache, and controller-runtime's internal sync barrier guarantees the cache is populated before any reconcile loop starts.

**Reconciler client** (`New` in `controller.go`): `NewClient` now returns `&operatorclient.CtrlClientImpl{Client: m.GetClient()}` directly. The previous `BuildCustomClient` function, which instantiated a separate `cache.Cache`, is deleted entirely. The `UncachedClient` field, constructed by `NewUncachedClient`, remains for reads that must bypass the cache.

**Event filtering** (`SetupWithManager`): Watch predicates continue to use `requestEnqueueLabelKey`/`requestEnqueueLabelValue` (`app`/`external-secrets`) to filter reconcile events, consistent with the cache selector.

## Alternatives

**Keep the dual-cache with explicit sync waiting**: The reconciler could call `cache.WaitForCacheSync` on the custom cache before reading. This is fragile—it adds blocking startup logic, is difficult to test, and still requires maintaining two cache lifecycles. Controller-runtime's existing sync guarantee makes this unnecessary when using a single cache.

**Use the manager's default unfiltered cache**: Removing label selectors would eliminate the dual-cache problem without a custom builder. This was rejected because an unfiltered cache would watch every Deployment, Secret, and Service cluster-wide, creating unbounded memory usage and excessive API server load unsuitable for an operator running on shared clusters.

**Per-reconcile uncached reads**: Bypassing the cache entirely for all reads removes synchronization concerns but eliminates the performance and rate-limiting benefits of caching and reintroduces the risk of hitting API server rate limits under load.

## Risks

**Label discipline**: Any controller-managed resource missing the `app=external-secrets` label will be invisible to the cached client and produce "not found" errors that are difficult to distinguish from genuine absence. Additions to `controllerManagedResources` must be paired with correct label application.

**Optional CRD timing**: The cert-manager CRD check runs once at startup via `isCRDInstalled`. If cert-manager is installed after the operator starts, the `Certificate` informer will not be registered until the operator restarts. This is a known operational limitation.

**Cache filter expansion**: Adding a new resource type to `controllerManagedResources` requires coordinating both the list entry and the label selector. Missing either silently degrades behavior rather than failing loudly.

**Debugging opacity**: When the cache returns no results, it may be due to label mismatch, cache unsync, or genuine absence—all presenting identically to a caller. Operators debugging reconciliation failures need awareness of the label filter contract.
