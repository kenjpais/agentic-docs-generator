---
id: ADR-0003
title: "Three-Controller Architecture with Hierarchical Status Aggregation"
date: 2025-06-13
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [api/v1alpha1, pkg/controller]
jira: ESO-53
supersedes: ""
superseded-by: ""
---

# Three-Controller Architecture with Hierarchical Status Aggregation

## Executive Summary
The operator separates concerns across three controllers—`external_secrets_manager`, `external_secrets`, and `crd_annotator`—each owning a distinct responsibility, with `ExternalSecretsManager` acting as a singleton top-level dashboard that aggregates status from subordinate controllers via watch-driven reconciliation. This produces a clean observability surface for cluster administrators without coupling operand lifecycle management to global config or cert-manager annotation concerns.

## What
- Three controllers registered with a shared manager: `external_secrets_manager` (global config, status aggregation), `external_secrets` (operand deployment lifecycle), `crd_annotator` (cert-manager CA injection on CRDs).
- Two custom resource kinds: `ExternalSecretsManager` (singleton, `name=cluster`) and `ExternalSecretsConfig` (operand config, the subordinate CR).
- `ExternalSecretsManagerStatus.ControllerStatuses []ControllerStatus` in `api/v1alpha1/external_secrets_manager_types.go` is the aggregated status surface.
- The `external_secrets_manager` controller watches `ExternalSecretsConfig` status changes via a predicate that fires only when `.Status` differs (`reflect.DeepEqual`).

## Why
A single monolithic controller reconciling the operand, global config, and cert-manager annotations would conflate three orthogonal failure domains. Operators need a stable top-level object (`ExternalSecretsManager`) for `kubectl get esm cluster` health checks, separate from the per-operand config (`ExternalSecretsConfig`). The cert-manager CA injection is optional and cluster-environment-dependent, making it wrong to block operand reconciliation on its availability.

## Goals
- Provide a single, stable CRD (`ExternalSecretsManager`) as a health dashboard for the entire operator.
- Isolate operand lifecycle (deployments, RBAC, webhooks) in `external_secrets` controller so failures there don't affect global config reads.
- Gate cert-manager annotation work entirely in `crd_annotator`, which no-ops when `IsInjectCertManagerAnnotationEnabled` returns false.
- Avoid reconcile storms: `external_secrets_manager` only re-reconciles when `ExternalSecretsConfig.Status` actually changes.

## Non-Goals
- `ExternalSecretsManager` does not directly manage any operand Kubernetes resources (Deployments, Services, etc.).
- The architecture does not currently aggregate status from `crd_annotator` into `ExternalSecretsManager` (only `ExternalSecretsConfig` conditions are propagated).
- No cross-controller locking or ordered startup sequencing is enforced.

## How

**Controller registration**: All three controllers are registered against the same `ctrl.Manager`. Each builds its own cache client with label-scoped informers to limit watch traffic.

**`external_secrets` controller** (`pkg/controller/external_secrets/controller.go`): Owns operand resources. Uses a label-filtered cache (`app=external-secrets`) configured via `NewCacheBuilder()` injected at manager construction. Writes conditions to `ExternalSecretsConfig.Status`. Also holds an `UncachedClient` for resources not covered by the cache.

**`crd_annotator` controller** (`pkg/controller/crd_annotator/controller.go`): Builds its own `cache.Cache` via `BuildCustomClient()` watching `CustomResourceDefinition` objects filtered by `external-secrets.io/component=controller` and `ExternalSecretsConfig`. A `mapFunc` normalizes both CRD and config events into a single request queue. It writes a `UpdateAnnotation` condition back to `ExternalSecretsConfig.Status`.

**`external_secrets_manager` controller** (`pkg/controller/external_secrets_manager/controller.go`): Declared primary owner of `ExternalSecretsManager`. Its `SetupWithManager` adds a secondary `Watches` on `ExternalSecretsConfig` with a `statusUpdatePredicate` (using `reflect.DeepEqual` on `.Status`) to trigger reconciliation only on status changes. In `processReconcileRequest`, it iterates `r.esc.Status.Conditions`, calling `updateStatusCondition` which upserts into `ExternalSecretsManagerStatus.ControllerStatuses` keyed by `externalSecretsControllerId` (a composite string of group/version). Status writes use `retry.RetryOnConflict` to handle concurrent updates safely.

**Data flow**: `ExternalSecretsConfig` conditions (written by `external_secrets` and `crd_annotator`) → status change event → `external_secrets_manager` reconcile → `ExternalSecretsManager.Status.ControllerStatuses` updated.

**Singleton enforcement**: `ExternalSecretsManager` carries a CEL validation rule `self.metadata.name == 'cluster'` enforced at the CRD level.

## Alternatives

**Single controller managing everything**: Simpler wiring but couples cert-manager optionality to the operand reconcile path. A cert-manager API not being installed would block or error the entire reconciliation loop.

**Status written directly by each sub-controller to `ExternalSecretsManager`**: Avoids the intermediate `ExternalSecretsConfig` hop but creates concurrent writers on the same resource, increasing conflict rates and making ownership ambiguous.

**Separate operator binaries per concern**: Maximum isolation but impractical for an OpenShift operator that must ship as a single container image and share RBAC/leader election.

## Risks

- **Aggregation lag**: `ExternalSecretsManager` status reflects `ExternalSecretsConfig` status with at least one reconcile cycle of delay. Debugging failures requires inspecting both CRs.
- **`crd_annotator` status not aggregated**: Conditions written by `crd_annotator` to `ExternalSecretsConfig` are not currently reflected in `ExternalSecretsManager.ControllerStatuses` under a distinct controller key—they appear merged under the same `externalSecretsControllerId`. Adding a second controller's conditions requires extending the aggregation logic.
- **Singleton rigidity**: The `name=cluster` CEL constraint means tooling that creates `ExternalSecretsManager` with a different name fails at admission, not at reconcile time. CI pipelines must be aware.
- **Multiple custom caches**: Both `external_secrets` and `crd_annotator` build separate cache instances registered with the manager. Memory footprint grows with the number of controllers; a cache miss or startup race before the manager starts caches will return stale or empty results.
