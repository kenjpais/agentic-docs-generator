---
id: ADR-0008
title: "Irrecoverable Error Pattern to Distinguish Transient from Terminal Reconciliation Failures"
date: 2025-05-31
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [pkg/controller]
jira: ESO-51
supersedes: ""
superseded-by: ""
---

# Irrecoverable Error Pattern for Terminal Reconciliation Failures

## Executive Summary
The operator introduces a typed `IrrecoverableError` to distinguish configuration errors that cannot self-heal (e.g., missing operand image environment variables) from transient API errors that benefit from automatic retry. Controllers check for this type at the reconciliation boundary and stop retry loops immediately, preventing futile exponential backoff cycles and surfacing actionable operator misconfiguration to humans.

## What
- **`common.IrrecoverableError`** type and `common.NewIrrecoverableError` constructor (in `pkg/controller/common/`)
- **`pkg/controller/external_secrets/deployments.go`**: `getDeploymentObject` returns `IrrecoverableError` when `RELATED_IMAGE_EXTERNALSECRETS` or `RELATED_IMAGE_BITWARDEN_SDK_SERVER` environment variables are absent
- **`pkg/controller/external_secrets/controller.go`**: The reconcile loop checks for `IrrecoverableError` and returns without requeueing

## Why
Kubernetes controller-runtime requeues on any non-nil error return by default. For transient failures (API server unavailable, etcd timeout) this is correct behavior. But certain failures are structural: if the operator pod was deployed without required image reference environment variables, no number of retries will succeed. Without this distinction, the controller would enter exponential backoff, consume reconcile queue capacity, and produce log noise—while providing no actionable signal to the cluster administrator. The operator manages operand image references via environment variables injected at pod startup (following the OLM `relatedImages` convention), making their absence a deployment-time misconfiguration rather than a runtime transient failure.

## Goals
- Prevent futile retry loops for configuration errors that require human intervention
- Surface a clear, actionable error condition rather than generic backoff noise
- Allow transient errors (API failures, network issues) to continue using normal retry semantics
- Maintain a single classification point per error site, keeping call sites simple

## Non-Goals
- Does not cover all categories of irrecoverable errors—only missing image env vars are classified this way in the current implementation
- Does not implement automatic remediation or alerting; classification only affects requeue behavior
- Does not replace status condition updates for surfacing error state to `kubectl` consumers

## How

**Error creation** (`pkg/controller/external_secrets/deployments.go`, `getDeploymentObject`):
```
if image == "" {
    return nil, common.NewIrrecoverableError(
        fmt.Errorf("%s environment variable ... not set", externalsecretsImageEnvVarName),
        "failed to update image in %s deployment object", deployment.GetName())
}
```
Both `externalsecretsImageEnvVarName` and `bitwardenImageEnvVarName` checks follow this pattern. The error wraps a root cause `error` plus a formatted message, preserving context for logging.

**Error interception** (`pkg/controller/external_secrets/controller.go`, reconcile function):
The reconcile loop calls `createOrApplyDeployments` through `createOrApplyDeploymentFromAsset` → `getDeploymentObject`. At the top-level `Reconcile` method, the returned error is tested with a type assertion or `errors.As` against `common.IrrecoverableError`. When matched, the controller logs the error, updates a degraded status condition, and returns `reconcile.Result{}, nil`—suppressing requeue.

**Data flow**:
`Reconcile` → `createOrApplyDeployments` → `createOrApplyDeploymentFromAsset` → `getDeploymentObject` → `common.NewIrrecoverableError` propagates up the call stack unwrapped, so the type check at the top boundary succeeds via `errors.As`.

## Alternatives

**Panic on missing env vars at startup**: Fail-fast at operator initialization if required env vars are absent. Simpler, but the operator manages multiple `ExternalSecretsConfig` instances; a missing variable is config-scoped, and panicking prevents the operator from managing other resources.

**Always requeue with a long interval**: Return a fixed `RequeueAfter` duration. This avoids the custom type but wastes cycles indefinitely and provides no semantic distinction from recoverable errors.

**Status condition only, no error return**: Set a `Degraded` condition and return `nil`. This stops retries but silently loses the error from the controller-runtime metrics and log pipeline that inspect returned errors.

## Risks

- **Maintenance burden**: Every new terminal error site must consciously choose `IrrecoverableError` vs. standard error. Developers unfamiliar with the pattern will return plain errors, causing retry loops for new structural failures.
- **Classification mistakes**: A condition incorrectly classified as irrecoverable (e.g., a temporarily missing ConfigMap) will halt reconciliation until a human-triggered restart, making the operator appear unresponsive.
- **Error unwrapping fragility**: The pattern depends on `errors.As` traversal; wrapping an `IrrecoverableError` with `fmt.Errorf("%w", ...)` at an intermediate call site would break classification if the check uses direct type assertion instead of `errors.As`.
- **Limited scope coverage**: Only image env var absence is currently classified; other terminal conditions (malformed static asset bytes, invalid CRD schema) still trigger retry loops, creating inconsistent behavior across failure modes.
