# Execution Plan: CORENET-6605 — Fix Transient Error Conditions Causing Degraded Status

**File:** `agentic/exec-plans/completed/corenet-6605-fix-transient-degraded-conditions.md`

---

```markdown
# Exec Plan: CORENET-6605 — Fix Transient Error Conditions Causing Degraded Status

## Metadata

| Field         | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| PR            | #2896                                                                 |
| Jira          | CORENET-6605                                                          |
| Status        | Completed                                                             |
| Author        | jluhrsen                                                              |
| Affects       | `pkg/controller/`, `pkg/network/`, `pkg/controller/statusmanager/`   |
| Risk Level    | Medium — touches status reporting across all major controllers        |

---

## Problem

During serial e2e payload jobs (e.g., `periodic-ci-openshift-release-master-ci-4.18-e2e-gcp-ovn-techpreview-serial`),
the network-operator transiently set `Degraded=True` with reasons `ApplyOperatorConfig` or `RolloutHung`.
These blips are not caused by real failures — they are caused by transient error conditions that the controllers
were not handling gracefully (e.g., temporary API unavailability, requeue races, or recoverable reconciliation errors).

This caused a blanket exception to be added in OpenShift's origin test suite
(`pkg/monitortests/clusterversionoperator/legacycvomonitortests/operators.go`).
The goal of this plan is to fix the root causes so the exception can be removed.

---

## Root Cause Analysis

Transient errors during controller reconciliation were being immediately surfaced as `Degraded=True`
rather than being retried or suppressed until they exceeded a meaningful threshold. Two failure categories
were observed:

1. **`ApplyOperatorConfig`** — Errors from short-lived API conflicts or missing objects during config application.
2. **`RolloutHung`** — False positives when pods were mid-rollout and transiently unavailable.

---

## Implementation

### Step 1 — Harden Status Manager Error Classification

**Files:**
- `pkg/controller/statusmanager/status_manager.go`
- `pkg/controller/statusmanager/status_manager_test.go`
- `pkg/controller/statusmanager/pod_status.go`

**What was done:**

The status manager was updated to distinguish between transient and persistent error conditions
before emitting `Degraded=True`. This is the foundational change that all per-controller fixes
depend upon.

- Added or extended logic in `status_manager.go` to track whether an error has persisted
  across reconcile cycles before escalating to `Degraded`.
- Updated `pod_status.go` to avoid marking pod rollout as hung on the first detected stall —
  allowing in-progress rollouts to complete before triggering degraded status.
- Added test coverage in `status_manager_test.go` for the new transient-suppression logic.

---

### Step 2 — Fix `operconfig` Controller Error Handling

**Files:**
- `pkg/controller/operconfig/operconfig_controller.go` (+7 -9)
- `pkg/controller/operconfig/cluster.go` (+7 -1)

**What was done:**

The `operconfig` controller is the primary reconciler for `ApplyOperatorConfig` degradation.
Changes here improved how reconcile errors are returned and classified:

- In `operconfig_controller.go`: Reduced noise from errors that are safe to requeue without
  marking the operator degraded. Refactored error return paths so that recoverable errors
  trigger a requeue rather than immediately setting degraded status.
- In `cluster.go`: Extended error wrapping/classification so callers can distinguish
  transient infrastructure errors from configuration errors requiring human intervention.

---

### Step 3 — Fix `clusterconfig` Controller

**Files:**
- `pkg/controller/clusterconfig/clusterconfig_controller.go` (+12 -2)
- `pkg/network/cluster_config.go` (+lines)
- `pkg/network/cluster_config_test.go` (+lines)

**What was done:**

The cluster config controller was updated to handle cases where the cluster network config
object is momentarily unavailable or returns a transient API error:

- `clusterconfig_controller.go`: Added error type inspection before propagating errors
  to the status manager. Transient errors (e.g., `IsNotFound`, `IsConflict`,
  `IsServiceUnavailable`) now return early with a requeue rather than degrading.
- `pkg/network/cluster_config.go`: Updated helper functions to return typed/wrapped errors
  so that callers can make informed retry decisions.
- `pkg/network/cluster_config_test.go`: Added unit tests covering transient-error paths.

---

### Step 4 — Fix Remaining Controllers (Uniform Pattern)

**Files:**
- `pkg/controller/configmap_ca_injector/controller.go` (+2 -2)
- `pkg/controller/dashboards/dashboard_controller.go` (+2 -2)
- `pkg/controller/egress_router/egress_router_controller.go` (+1 -1)
- `pkg/controller/infrastructureconfig/infrastructureconfig_controller.go` (+2 -2)
- `pkg/controller/pki/pki_controller.go` (+1 -1)
- `pkg/controller/proxyconfig/controller.go` (+8 -8)
- `pkg/controller/signer/signer-controller.go` (+2 -2)

**What was done:**

A uniform fix was applied across all remaining controllers to align with the improved
error classification model established in Steps 1–3:

- Each controller's reconcile loop was audited for error return paths that could
  prematurely trigger `Degraded=True`.
- Where a controller was passing raw errors directly to the status manager, those paths
  were updated to either:
  - Classify the error before passing it, or
  - Use a requeue-with-delay pattern for known-transient conditions.
- `proxyconfig/controller.go` had the largest change (+8 -8) due to multiple reconcile
  paths that each needed independent correction.

---

## Testing

### Unit Tests

| File | Coverage Added |
|------|----------------|
| `pkg/controller/statusmanager/status_manager_test.go` | Transient error suppression, degraded escalation thresholds |
| `pkg/network/cluster_config_test.go` | Transient API error handling in cluster config helpers |

### Integration / E2E Validation

- The fix is verified against the serial e2e job:
  `periodic-ci-openshift-release-master-ci-4.18-e2e-gcp-ovn-techpreview-serial`
- Target: zero `Degraded=True` blips with reason `ApplyOperatorConfig` or `RolloutHung`
  during normal operation and upgrade sequences.
- After validation, the exception in
  `openshift/origin: pkg/monitortests/clusterversionoperator/legacycvomonitortests/operators.go`
  should be removed in a follow-up PR.

---

## Verification Steps

1. **Run unit tests locally:**
   ```bash
   go test ./pkg/controller/statusmanager/...
   go test ./pkg/network/...
   ```

2. **Run all controller tests:**
   ```bash
   go test ./pkg/controller/...
   ```

3. **Observe serial job run** — confirm no `Degraded=True` blips with `ApplyOperatorConfig`
   or `RolloutHung` reasons appear in the Prow job timeline.

4. **Confirm exception removal is unblocked** — after job passes cleanly for ≥2 consecutive
   runs, open a follow-up PR to remove the origin exception.

---

## Rollback Plan

| Scenario | Action |
|----------|--------|
| New `Degraded=True` blip introduced | Revert PR #2896; re-add origin exception if needed |
| Transient errors now silently swallowed | Inspect status manager logs; ensure requeue is occurring |
| Upgrade regression | Revert PR #2896; file new Jira under CORENET for root cause |

Rollback command:
```bash
git revert <merge-commit-sha>
```
The revert is safe because all changes are confined to error-handling paths with no
schema, API, or CRD changes.

---

## Affected Components Summary

```
pkg/
├── controller/
│   ├── statusmanager/          ← Core fix: transient error classification
│   ├── operconfig/             ← Primary ApplyOperatorConfig degradation source
│   ├── clusterconfig/          ← Cluster network config transient errors
│   ├── configmap_ca_injector/  ← Uniform fix
│   ├── dashboards/             ← Uniform fix
│   ├── egress_router/          ← Uniform fix
│   ├── infrastructureconfig/   ← Uniform fix
│   ├── pki/                    ← Uniform fix
│   ├── proxyconfig/            ← Uniform fix (largest change)
│   └── signer/                 ← Uniform fix
└── network/
    └── cluster_config.go       ← Typed error helpers
```

---

## Follow-up Work

| Task | Owner | Tracking |
|------|-------|---------|
| Remove origin exception after clean job runs | Network team | CORENET-6605 follow-up |
| Audit remaining operators in the blip list for similar patterns | Network team | CORENET epic |
| Add CI gate to prevent future raw-error-to-degraded patterns | Tooling | Tech debt |

**Tech debt reference:** `agentic/exec-plans/tech-debt-tracker.md` → entry: `no-raw-error-to-degraded`
```

---

**Placement:** `agentic/exec-plans/completed/corenet-6605-fix-transient-degraded-conditions.md`