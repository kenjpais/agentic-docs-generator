# Design Document: Transient Error Handling for Network Operator Degraded State

**Feature:** CORENET-6605 — Fix Transient Error Conditions Causing `Degraded=True`
**PR:** #2896 (`jluhrsen/CORENET-6605`)
**Status:** Implemented
**Component:** `pkg/controller/` (Network Operator Controllers)
**Author:** jluhrsen
**Date:** 2024

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Background and Context](#background-and-context)
4. [Goals and Non-Goals](#goals-and-non-goals)
5. [Architecture Overview](#architecture-overview)
6. [Design Decisions](#design-decisions)
7. [Component Relationships](#component-relationships)
8. [Data Flow](#data-flow)
9. [Implementation Reference](#implementation-reference)
10. [Alternatives Considered](#alternatives-considered)
11. [Risks and Mitigations](#risks-and-mitigations)
12. [Testing Considerations](#testing-considerations)

---

## Executive Summary

The Network Operator was intermittently setting `Degraded=True` during normal e2e test runs and upgrades due to transient error conditions — specifically errors categorized as `ApplyOperatorConfig` or `RolloutHung`. These are not genuine degraded states; they are temporary reconciliation failures that self-resolve.

This document describes the architectural approach taken to distinguish transient errors from persistent failures across all affected controllers, ensuring the operator only signals `Degraded=True` when a real, sustained problem exists.

---

## Problem Statement

### Observed Behavior

During OpenShift payload job runs (e.g., `periodic-ci-openshift-release-master-ci-4.18-e2e-gcp-ovn-techpreview-serial`), the Network Operator intermittently transitioned to `Degraded=True` with reasons:

- `ApplyOperatorConfig`
- `RolloutHung`

These blips were not caused by genuine operator failures — they were **transient reconciliation errors** surfaced prematurely as degraded states visible to the Cluster Version Operator (CVO) and cluster health monitors.

### Impact

| Stakeholder | Impact |
|---|---|
| CI/CD Pipeline | False positives in health checks, masking real failures |
| Upgrade Process | CVO may halt upgrades if it sees `Degraded=True` mid-reconciliation |
| Oncall Engineers | Alert fatigue from non-actionable degraded signals |
| Test Framework | Required workaround exceptions in `origin/pkg/monitortests/` |

### Workaround in Place (Pre-Fix)

An exception was added in the `origin` repository to suppress these specific blips in test evaluation:

```
origin/pkg/monitortests/clusterversionoperator/legacycvomonitortests/operators.go:L105
```

This exception is **expected to be removed** after the fix is verified.

---

## Background and Context

### How the Network Operator Reports Health

The Network Operator uses the standard OpenShift operator SDK pattern where each controller reconciles state and reports conditions to the `clusteroperator` resource. The CVO monitors these conditions.

Key condition types:
- `Available` — is the operator functional?
- `Progressing` — is the operator making changes?
- `Degraded` — is the operator in a failure state?

Setting `Degraded=True` signals to the entire cluster that something is broken. During normal operations (startup, config reload, upgrade), controllers may encounter transient API errors, lock contention, or timing issues that are **expected to be self-healing** and must not be promoted to a cluster-level degraded signal.

### Controller Architecture

The Network Operator uses multiple specialized controllers, each responsible for a domain:

```
pkg/controller/
├── clusterconfig/          ← Cluster network configuration
├── configmap_ca_injector/  ← CA bundle injection
├── dashboards/             ← Grafana dashboard management
├── egress_router/          ← Egress router lifecycle
├── infrastructureconfig/   ← Infrastructure configuration sync
├── operconfig/             ← Core operator configuration & rollout
├── pki/                    ← PKI certificate management
├── proxyconfig/            ← Proxy configuration
├── signer/                 ← Certificate signing
└── [5 additional controllers]
```

Each controller had its own error handling logic, and many were **not consistently classifying transient vs. persistent errors** before propagating them as degraded conditions.

---

## Goals and Non-Goals

### Goals

- ✅ Prevent transient/recoverable errors from being surfaced as `Degraded=True`
- ✅ Ensure persistent, genuine failures still correctly set `Degraded=True`
- ✅ Apply consistent error classification across all affected controllers
- ✅ Enable removal of the workaround exception in `origin` repository
- ✅ Maintain existing reconciliation behavior and timing

### Non-Goals

- ❌ Changing the reconciliation loop frequency or backoff strategy
- ❌ Introducing new CRD fields or API changes
- ❌ Modifying how the CVO itself interprets degraded conditions
- ❌ Adding retry logic at the controller-manager level

---

## Architecture Overview

### Core Concept: Transient Error Classification

The solution introduces or expands **error classification** at the point where reconciliation errors are converted into operator conditions. Instead of immediately propagating any reconciliation error as `Degraded=True`, errors are first evaluated against known transient patterns.

```
                    ┌─────────────────────────────┐
                    │     Reconciliation Loop      │
                    │  (controller-runtime)        │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Error Returned?         │
                    └──────────────┬──────────────┘
                          No │             │ Yes
                             │             ▼
                             │  ┌──────────────────────┐
                             │  │  Error Classification │
                             │  │  ┌────────────────┐  │
                             │  │  │ IsTransient(e)?│  │
                             │  │  └───────┬────────┘  │
                             │  └──────────┼───────────┘
                             │     Yes │   │ No
                             │         │   │
                             │         ▼   ▼
                             │  ┌────────────────────────────────────┐
                             │  │ Transient         │ Persistent      │
                             │  │ → Log warning     │ → Set           │
                             │  │ → Requeue         │   Degraded=True │
                             │  │ → No Degraded     │ → Log error     │
                             │  └────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────────────────┐
                    │   Report Healthy Conditions  │
                    │   (Available, not Degraded)  │
                    └─────────────────────────────┘
```

### Change Scope

The fix is applied across **15 Go files** and **10+ controllers**, with a net addition of ~108 lines. This reflects the **breadth** of the problem — transient error misclassification was systemic, not isolated.

---

## Design Decisions

### Decision 1: Fix at Error Classification, Not at Retry Policy

**Chosen Approach:** Classify errors as transient/persistent at the point of condition reporting within each controller.

**Rationale:**
- The reconciliation loop already handles requeueing; we don't need a separate retry mechanism
- Classification at the reporting boundary is the least invasive change
- Keeps each controller's reconciliation logic self-contained
- Avoids introducing a centralized error-handling abstraction that could mask genuine failures

**Trade-off:** Requires touching each controller individually rather than a single central fix. This is acceptable because it allows per-controller tuning of what counts as transient.

---

### Decision 2: Distributed Fix Across All Controllers (Not Centralized)

**Chosen Approach:** Apply the fix in each affected controller's error handling path independently.

**Rationale:**
- Each controller has different semantic context for what makes an error transient
- A centralized interceptor would require all error types to be generically classifiable
- Localized fixes are easier to review, test, and revert per controller
- Consistent with the existing controller architecture pattern

**Alternative Rejected:** A middleware layer at the controller-manager level that intercepts all condition updates. See [Alternatives Considered](#alternatives-considered).

---

### Decision 3: Preserve Existing Degraded Behavior for Persistent Failures

**Chosen Approach:** Only suppress `Degraded=True` for well-understood, recoverable error patterns. All other errors continue to set `Degraded=True` as before.

**Rationale:**
- The fix must not reduce observability of real failures
- Conservative approach: if an error cannot be confirmed as transient, it is treated as persistent
- This preserves operator safety guarantees

---

### Decision 4: `operconfig` Controller Gets Enhanced Cluster State Awareness

**File:** `pkg/controller/operconfig/cluster.go` (+7 -1)

The `operconfig` controller is the primary orchestrator for network rollout. It received additional logic to better distinguish `RolloutHung` scenarios that are genuinely hung vs. those that are still in progress within acceptable time windows.

**Rationale:** The `RolloutHung` reason was the most common source of false degraded signals during upgrades, where rollout time legitimately increases. The controller needed richer cluster state context to make this determination.

---

## Component Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    Network Operator (network-operator binary)    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │               Controller Manager                         │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌─────────────────┐  ┌───────────┐  │    │
│  │  │ operconfig   │  │  clusterconfig  │  │    pki    │  │    │
│  │  │ controller   │  │  controller     │  │ controller│  │    │
│  │  │  [MODIFIED]  │  │  [MODIFIED]     │  │ [MODIFIED]│  │    │
│  │  └──────┬───────┘  └────────┬────────┘  └─────┬─────┘  │    │
│  │         │                   │                  │        │    │
│  │  ┌──────┴───────────────────┴──────────────────┘        │    │
│  │  │                                                       │    │
│  │  │  ┌─────────────────┐  ┌──────────────────┐           │    │
│  │  │  │  proxyconfig    │  │  configmap_ca_   │           │    │
│  │  │  │  controller     │  │  injector        │           │    │
│  │  │  │  [MODIFIED]     │  │  [MODIFIED]      │           │    │
│  │  │  └─────────────────┘  └──────────────────┘           │    │
│  │  │                                                       │    │
│  │  │  ┌─────────────────┐  ┌──────────────────┐           │    │
│  │  │  │  egress_router  │  │  infrastructure  │           │    │
│  │  │  │  controller     │  │  config ctrl     │           │    │
│  │  │  │  [MODIFIED]     │  │  [MODIFIED]      │           │    │
│  │  │  └─────────────────┘  └──────────────────┘           │    │
│  │  │                                                       │    │
│  │  │  ┌─────────────────┐  ┌──────────────────┐           │    │
│  │  │  │  dashboards     │  │  signer          │           │    │
│  │  │  │  controller     │  │  controller      │           │    │
│  │  │  │  [MODIFIED]     │  │  [MODIFIED]      │           │    │
│  │  │  └─────────────────┘  └──────────────────┘           │    │
│  │  └───────────────────────────────────────────────────────┘   │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             Condition Reporter                            │   │
│  │   Degraded / Available / Progressing → ClusterOperator   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   ClusterOperator Resource    │
              │   (network.operator.openshift.io)│
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Cluster Version Operator     │
              │  (CVO)                        │
              │  Monitors Degraded conditions │
              │  Gates upgrades               │
              └───────────────────────────────┘
```

### Controller Responsibility Matrix

| Controller | File | Problem Root Cause | Fix Type |
|---|---|---|---|
| `operconfig` | `operconfig_controller.go`, `cluster.go` | `RolloutHung` false positive | Enhanced state evaluation |
| `clusterconfig` | `clusterconfig_controller.go` | `ApplyOperatorConfig` on transient API error | Error classification |
| `proxyconfig` | `proxyconfig/controller.go` | Transient proxy config read errors | Error classification |
| `configmap_ca_injector` | `controller.go` | CA bundle injection timing errors | Error classification |
| `dashboards` | `dashboard_controller.go` | Dashboard sync transient failure | Error classification |
| `egress_router` | `egress_router_controller.go` | Transient CR read errors | Error classification |
| `infrastructureconfig` | `infrastructureconfig_controller.go` | Infra config sync timing | Error classification |
| `pki` | `pki_controller.go` | PKI rotation transient errors | Error classification |
| `signer` | `signer-controller.go` | Cert signing transient errors | Error classification |

---

## Data Flow

### Before Fix: Transient Error → Degraded Signal

```
Controller Reconcile()
        │
        ▼
  Error occurs (e.g., API server momentarily unavailable)
        │
        ▼
  error returned to reconcile loop
        │
        ▼
  SetDegraded("ApplyOperatorConfig", err.Error())  ← immediately
        │
        ▼
  ClusterOperator.Status.Conditions[Degraded=True]
        │
        ▼
  CVO observes Degraded=True
        │
        ▼
  ⚠️  CI job sees degraded blip / upgrade gated
```

### After Fix: Transient Error → Requeue, No Degraded

```
Controller Reconcile()
        │
        ▼
  Error occurs (e.g., API server momentarily unavailable)
        │
        ▼
  isTransientError(err) == true?
        │
       YES
        │
        ▼
  Log warning: "transient error, will retry"
        │
        ▼
  Return error (triggers controller-runtime requeue w/ backoff)
        │
        ▼
  NO Degraded condition written
        │
        ▼
  Next reconcile succeeds
        │
        ▼
  ✅  ClusterOperator remains healthy
```

### After Fix: