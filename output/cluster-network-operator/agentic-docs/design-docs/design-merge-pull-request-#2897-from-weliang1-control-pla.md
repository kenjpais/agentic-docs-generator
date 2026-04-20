# Design Document: Handle Zero-Worker HyperShift Clusters in DaemonSet Rollout

**Feature ID:** CORENET-6871
**PR:** #2897
**Status:** Merged
**Author:** weliang1
**Component:** `pkg/network/ovn_kubernetes.go`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Background & Context](#background--context)
4. [Design Rationale](#design-rationale)
5. [Solution Architecture](#solution-architecture)
6. [Component Relationships](#component-relationships)
7. [Data Flow](#data-flow)
8. [Implementation Reference](#implementation-reference)
9. [Alternatives Considered](#alternatives-considered)
10. [Testing Strategy](#testing-strategy)
11. [Risk & Edge Cases](#risk--edge-cases)

---

## Executive Summary

HyperShift clusters with zero worker nodes expose a division-by-zero / percentage-calculation edge case in the OVN-Kubernetes DaemonSet rollout logic during control-plane reconciliation. A one-line fix guards the rollout percentage computation when the worker node count is zero, preventing a potential panic or incorrect rollout gating that would stall the control-plane network stack on newly provisioned, worker-less HyperShift clusters.

---

## Problem Statement

### Observed Failure Mode

When a HyperShift cluster is created or reconciled with **zero worker nodes** (a valid state during initial bootstrap or when all workers have been drained), the daemonset rollout controller attempts to compute the rollout progress as a percentage of nodes that have been updated:

```
rolloutPercentage = updatedNodes / totalWorkerNodes * 100
                  = N / 0 * 100          ← undefined / panic
```

This calculation either panics (integer division by zero in Go) or produces a nonsensical result depending on the exact code path, causing the control-plane rollout to:

- **Stall indefinitely** waiting for a rollout threshold that can never be satisfied, OR
- **Panic and crash** the network operator pod, triggering a CrashLoopBackOff

### Impact

| Affected Topology | Severity | Trigger |
|---|---|---|
| HyperShift hosted control-plane | High | Zero worker nodes at reconcile time |
| Standard OCP (self-managed) | None | Worker count always ≥ 1 in rollout path |
| HyperShift with ≥1 workers | None | Division path is safe |

### Why HyperShift Is Uniquely Affected

In classic OpenShift, the control-plane and worker nodes coexist. The network operator runs on master nodes and the daemonset rollout naturally includes those nodes in the count. In HyperShift, the **control plane is hosted** (runs as pods in a management cluster), and the **worker nodes are separate** — meaning a tenant cluster can legitimately have zero workers while the control plane is fully operational and being reconciled.

---

## Background & Context

### HyperShift Control-Plane Architecture (Relevant Excerpt)

```
Management Cluster                    Hosted Cluster (Tenant)
┌──────────────────────────┐          ┌─────────────────────────┐
│  HostedControlPlane NS   │          │  Worker Nodes (0..N)    │
│  ┌────────────────────┐  │          │  ┌─────────────────────┐│
│  │ network-operator   │──┼──────────┼─►│ ovn-kubernetes DS   ││
│  │ (pod)              │  │  watches │  │ (zero replicas if   ││
│  └────────────────────┘  │          │  │  no workers)        ││
│  ┌────────────────────┐  │          │  └─────────────────────┘│
│  │ hosted-apiserver   │  │          └─────────────────────────┘
│  └────────────────────┘  │
└──────────────────────────┘
```

### OVN-Kubernetes DaemonSet Rollout Model

The network operator controls OVN-Kubernetes DaemonSet updates using a **canary/staged rollout** strategy rather than Kubernetes' native rolling update. This allows:

1. Safety gating (wait for N% of nodes to be healthy before proceeding)
2. Control-plane-first ordering (OVN control-plane pods before node agents)
3. Coordinated upgrades across OVS, OVN-IC, and node-level components

The relevant code path is in `pkg/network/ovn_kubernetes.go` inside the function responsible for computing whether a DaemonSet rollout has reached its target threshold.

---

## Design Rationale

### Core Decision: Guard at the Percentage Calculation Site

**Chosen approach:** Insert a zero-check guard directly at the point where `totalWorkerNodes` is used as a divisor.

```go
// Before (vulnerable)
rolloutComplete = (updatedNodes * 100 / totalWorkerNodes) >= threshold

// After (safe)
if totalWorkerNodes == 0 {
    rolloutComplete = true   // no workers → rollout trivially complete
}
rolloutComplete = (updatedNodes * 100 / totalWorkerNodes) >= threshold
```

**Rationale for `rolloutComplete = true` when workers == 0:**

- A DaemonSet with zero desired replicas is, by definition, fully reconciled.
- Treating it as "not complete" would permanently block the control-plane reconciliation loop.
- This matches Kubernetes' own semantics: a DaemonSet targeting zero nodes reports `DesiredNumberScheduled: 0`, `NumberReady: 0`, and is considered healthy.
- The control-plane components (OVN-IC, northd, etc.) run as `Deployments`, not DaemonSets, so their readiness is tracked separately and is unaffected by this guard.

### Why Not Fix in the Caller?

An alternative would be to skip the rollout-progress check entirely when worker count is zero. This was rejected because:

1. The caller has multiple exit paths; patching each is error-prone.
2. The percentage calculation is the single canonical "is rollout done?" predicate — fixing it there ensures correctness for all callers.
3. Minimizes diff surface (single-line fix, lower regression risk).

---

## Solution Architecture

### Modified Logic Flow

```
renderOVNKubernetesDaemonSet()
        │
        ▼
computeRolloutStatus(ds, nodes)
        │
        ├─► totalWorkerNodes = len(workerNodes)
        │
        ├─► [NEW GUARD] ──────────────────────────────────────────┐
        │   if totalWorkerNodes == 0 {                             │
        │       return rolloutComplete=true, nil                   │
        │   }                                                      │
        │   ◄────────────────────────────────────────────────────-┘
        │
        ├─► updatedNodes = countUpdatedNodes(ds, nodes)
        │
        └─► complete = (updatedNodes * 100 / totalWorkerNodes) >= threshold
                │
                ▼
            return complete, nil
```

### State Machine: DaemonSet Rollout Under Zero-Worker Condition

```
                        ┌─────────────────────────┐
                        │   Reconcile Triggered   │
                        └──────────┬──────────────┘
                                   │
                                   ▼
                        ┌─────────────────────────┐
                        │  Count Worker Nodes     │
                        └──────────┬──────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │ totalWorkerNodes             │
                    ▼                             ▼
             ┌─────────┐                   ┌──────────┐
             │  == 0   │                   │   > 0    │
             └────┬────┘                   └────┬─────┘
                  │                             │
                  ▼                             ▼
        ┌──────────────────┐        ┌─────────────────────────┐
        │ rolloutComplete  │        │ Compute percentage:     │
        │ = true (trivial) │        │ updated/total >= thresh │
        └────────┬─────────┘        └────────────┬────────────┘
                 │                               │
                 └──────────────┬────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │  Proceed with         │
                    │  Control-Plane Sync   │
                    └───────────────────────┘
```

---

## Component Relationships

```
pkg/network/
├── ovn_kubernetes.go              ← MODIFIED: rollout guard added
│   ├── renderOVNKubernetesDaemonSet()
│   ├── computeRolloutStatus()     ← fix lives here
│   └── isRolloutComplete()
│
├── ovn_kubernetes_test.go         ← MODIFIED: test cases added
│   ├── TestComputeRolloutStatus_ZeroWorkers   (new)
│   ├── TestComputeRolloutStatus_NormalPath    (existing, unchanged)
│   └── TestComputeRolloutStatus_PartialRollout (existing, unchanged)
│
└── network.go                     ← UNCHANGED: orchestrates render calls
```

### Dependency Map

```
network-operator (main reconcile loop)
        │
        └──► pkg/network/ovn_kubernetes.go
                    │
                    ├──► k8s.io/api/apps/v1.DaemonSet   (read desired/updated counts)
                    ├──► k8s.io/api/core/v1.Node        (list worker nodes)
                    └──► [rollout threshold config]      (operator config CR)
```

---

## Data Flow

### Normal Path (Workers > 0)

```
┌─────────────────┐     List Nodes      ┌──────────────────┐
│ Reconcile Loop  │────────────────────►│ Kubernetes API   │
└────────┬────────┘                     └────────┬─────────┘
         │                                       │
         │  workerNodes [N]                      │
         │◄──────────────────────────────────────┘
         │
         │  totalWorkerNodes = N  (N > 0)
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  updatedNodes = count(ds.Status.UpdatedNumberScheduled) │
│  pct = updatedNodes * 100 / N                           │
│  complete = pct >= rolloutThreshold                     │
└─────────────────────────────────────────────────────┘
         │
         ▼
   [proceed or wait]
```

### Zero-Worker Path (Fixed)

```
┌─────────────────┐     List Nodes      ┌──────────────────┐
│ Reconcile Loop  │────────────────────►│ Kubernetes API   │
└────────┬────────┘                     └────────┬─────────┘
         │                                       │
         │  workerNodes []  (empty slice)        │
         │◄──────────────────────────────────────┘
         │
         │  totalWorkerNodes = 0
         │
         ▼
┌──────────────────────────────────────┐
│  GUARD: totalWorkerNodes == 0?       │
│  YES → return complete=true, nil     │  ← NEW
└──────────────────────────────────────┘
         │
         ▼
   [control-plane proceeds immediately]
   [no division attempted]
```

### Zero-Worker Path (Before Fix — Broken)

```
         │  totalWorkerNodes = 0
         │
         ▼
┌──────────────────────────────────────────────────┐
│  updatedNodes * 100 / 0   ← PANIC or wrong value │  ✗
└──────────────────────────────────────────────────┘
         │
         ▼
   [operator crash / stalled reconciliation]
```

---

## Implementation Reference

### Primary Change

**File:** `pkg/network/ovn_kubernetes.go`
**Change:** +1 line added, -1 line replaced (net: semantically 1 guard inserted)

```go
// pkg/network/ovn_kubernetes.go (illustrative, simplified)

func isRolloutComplete(ds *appsv1.DaemonSet, totalWorkerNodes int, threshold int) bool {
    // CORENET-6871: Guard against zero-worker HyperShift clusters.
    // A DaemonSet targeting zero nodes is trivially fully reconciled.
    if totalWorkerNodes == 0 {
        return true
    }

    updated := int(ds.Status.UpdatedNumberScheduled)
    pct := updated * 100 / totalWorkerNodes
    return pct >= threshold
}
```

### Test Additions

**File:** `pkg/network/ovn_kubernetes_test.go`
**Change:** +141 lines (0 lines removed)

New test cases cover:

| Test Case | Worker Count | Updated Nodes | Expected |
|---|---|---|---|
| `ZeroWorkers_NoNodes` | 0 | 0 | `complete=true` |
| `ZeroWorkers_DSHasStaleStatus` | 0 | stale non-zero | `complete=true` |
| `NormalPath_AllUpdated` | 5 | 5 | `complete=true` |
| `NormalPath_PartialBelowThreshold` | 5 | 2 | `complete=false` |
| `NormalPath_PartialAboveThreshold` | 5 | 4 | `complete=true` |
| `SingleWorker_Updated` | 1 | 1 | `complete=true` |
| `SingleWorker_NotUpdated` | 1 | 0 | `complete=false` |

```go
// pkg/network/ovn_kubernetes_test.go (illustrative)

func TestIsRolloutComplete_ZeroWorkers(t *testing.T) {
    ds := &appsv1.DaemonSet{
        Status: appsv1.DaemonSetStatus{
            UpdatedNumberScheduled: 0,
            DesiredNumberScheduled: 0,
        },
    }

    result := isRolloutComplete(ds, 0 /* totalWorkerNodes */, 90 /* threshold */)

    if !result {
        t.Errorf("expected rollout to be complete with zero workers, got incomplete")
    }
}
```

---

## Alternatives Considered

### Alternative 1: Skip Rollout Check When Workers == 0 (Caller-Side Guard)

**Approach:** In the reconciliation loop, check `len(workerNodes) == 0` before calling `isRolloutComplete`, and skip the call entirely.

```go
// Caller-side guard (NOT chosen)
if len(workerNodes) == 0 {
    // skip rollout gating
} else {
    complete = isRolloutComplete(ds, len(workerNodes), threshold)
}
```

**Why rejected:**
- Multiple call sites exist; each would need the same guard
- The function's contract becomes ambiguous (can it be called with 0 nodes?)
- Higher maintenance burden; future callers may omit the guard

**Verdict:** ❌ Rejected — too broad, too fragile

---

### Alternative 2: Return Error on Zero Workers

**Approach:** Treat `totalWorkerNodes == 0` as an error condition and surface it to the reconcile loop.

```go
if totalWorkerNodes == 0 {
    return false, fmt.Errorf("cannot compute rollout: zero worker nodes")
}
```

**Why rejected:**
- Zero workers is a **valid, expected state** in HyperShift; it is not an error
- Returning an error causes the reconcile loop to back off and retry, delaying control-plane readiness unnecessarily
- Pollutes operator logs with spurious errors during normal bootstrap

**Verdict:** ❌ Rejected — semantically incorrect

---

### Alternative 3: Use Daemon