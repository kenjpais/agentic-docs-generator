# Design Document: Drop Remaining OpenShift SDN Code (CORENET-6417)

**PR:** #2882 (`danwinship/drop-sdn`)
**Status:** Completed
**Author:** Dan Winship
**Document Location:** `agentic/design-docs/drop-openshift-sdn.md`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Background & Context](#background--context)
4. [Design Rationale](#design-rationale)
5. [Solution Architecture](#solution-architecture)
6. [Component Relationships](#component-relationships)
7. [Data Flow: Before and After](#data-flow-before-and-after)
8. [Detailed Changes](#detailed-changes)
9. [Alternatives Considered](#alternatives-considered)
10. [Risk Assessment](#risk-assessment)
11. [Testing Strategy](#testing-strategy)
12. [References](#references)

---

## Executive Summary

The Cluster Network Operator (CNO) contained a substantial body of dead code — approximately **1,631 lines of YAML** and **1,225 lines of Go** — dedicated to deploying OpenShift SDN. This code was never executed at runtime because CNO had an explicit rejection gate that refused all configurations requesting OpenShift SDN before any deployment logic could run.

This document describes the architectural decision to remove that dead code completely, the rationale behind the approach, what was deleted versus preserved, and the risks managed during the removal.

**Net result:** ~2,856 lines removed, ~45 lines added (scaffolding and comments), producing a leaner, more maintainable codebase with zero behavior change for any supported configuration.

---

## Problem Statement

### The Contradiction

```
User requests OpenShift SDN
         │
         ▼
┌─────────────────────────┐
│  CNO Validation Layer   │  ◄── Explicitly rejects OpenShift SDN
│  (early in reconcile)   │      Returns error, stops processing
└─────────────────────────┘
         │
         │  ✗ NEVER REACHED
         ▼
┌─────────────────────────┐
│  OpenShift SDN Deploy   │  ◄── ~2,856 lines of YAML + Go
│  Code & Templates       │      Dead code, maintained for nothing
└─────────────────────────┘
```

CNO simultaneously:
- **Rejected** every request to use OpenShift SDN (correct, expected behavior)
- **Carried** all the machinery to deploy OpenShift SDN (wasted maintenance surface)

### Consequences of the Status Quo

| Problem | Impact |
|---|---|
| Dead YAML templates in `bindata/network/openshift-sdn/` | Increases repo size, confuses contributors |
| Dead Go code in `pkg/network/` | Adds cognitive overhead for every new maintainer |
| False signal to future contributors | Suggests OpenShift SDN is a live, valid path |
| CI compiles and lints dead code | Wastes CI resources on every PR |
| Security scanning covers dead code | Any CVE in dead imports becomes a distraction |

---

## Background & Context

### OpenShift SDN History

OpenShift SDN was the original CNI plugin for OpenShift clusters. It was superseded by OVN-Kubernetes, which became the default and eventually the only supported network plugin for new clusters. The migration path was:

```
OpenShift SDN (legacy)
        │
        │  [Migration period - both supported]
        │
        ▼
OVN-Kubernetes (current default)
        │
        │  [OpenShift SDN deprecated]
        │
        ▼
OpenShift SDN explicitly rejected by CNO
        │
        │  [This PR]
        │
        ▼
OpenShift SDN code fully removed from CNO
```

By the time this PR was authored, no supported upgrade path or cluster configuration could result in OpenShift SDN being deployed through CNO. The rejection was already enforced at the API validation layer.

### What CNO Manages

CNO is responsible for:
- Reading the `Network.operator.openshift.io` custom resource
- Validating the requested network plugin
- Deploying and managing the lifecycle of network components (OVN-K, Multus, kube-proxy, etc.)
- Rendering `bindata/` templates into live Kubernetes objects

---

## Design Rationale

### Why Remove Rather Than Leave

Three principles drove the decision to delete rather than leave the code in place:

**1. Dead code is not neutral — it is actively harmful**

Every line of dead code is a line that:
- Misleads contributors about what is active
- Must be compiled, linted, and scanned
- Can harbor latent bugs that never surface but consume review effort
- Increases the diff size of unrelated changes

**2. The rejection gate makes removal safe**

Because CNO already rejects OpenShift SDN at validation time — before any deployment logic runs — removing the deployment logic has **zero runtime impact**. The safety net was already in place; this PR simply removes the weight it was holding up.

**3. Clean removal is better than deprecation markers**

A deprecation comment saying `// TODO: remove this` is a promise. Keeping that promise immediately avoids the accumulation of tech debt and the need for a future "cleanup" PR that is harder to write the longer it waits.

### Scope Boundary: What Was Intentionally Kept

The removal was scoped precisely. The following were **not** removed:

| Retained Element | Reason |
|---|---|
| The validation/rejection logic itself | It must remain to produce clear error messages for any operator that misconfigures the network type |
| OVN-Kubernetes code | Actively used |
| Multus code | Actively used; minor cleanup only |
| kube-proxy code | Actively used; minor cleanup only |
| Error message text referencing SDN | User-facing error messages must remain informative |

---

## Solution Architecture

### Deletion Strategy

The removal followed a layered approach, working from the lowest-level assets upward:

```
Layer 3: Go business logic
  pkg/network/openshift_sdn.go         ← Deleted
  pkg/network/openshift_sdn_test.go    ← Deleted
  pkg/network/network.go               ← SDN branches removed
  pkg/network/...                      ← All SDN switch cases removed

Layer 2: Generated/rendered objects
  bindata/network/openshift-sdn/       ← Entire directory deleted
  (000-ns, 001-crd, 002-rbac, etc.)

Layer 1: Shared templates with SDN references
  bindata/kube-proxy/kube-proxy.yaml   ← SDN-conditional block removed
  bindata/network/multus/multus.yaml   ← SDN-conditional block removed
```

### File Inventory

#### Fully Deleted Files

```
bindata/network/openshift-sdn/
├── 000-ns.yaml              (-15 lines)   Namespace definition
├── 001-crd.yaml             (-377 lines)  CRDs: HostSubnet, NetNamespace, etc.
├── 002-rbac.yaml            (-75 lines)   RBAC for SDN daemonset
├── 003-rbac-controller.yaml (-128 lines)  RBAC for SDN controller
├── 004-multitenant.yaml     (-165 lines)  Multitenant network policy objects
├── 005-clusternetwork.yaml  (-1 line)     ClusterNetwork CR template
├── 006-flowschema.yaml      (-37 lines)   APF FlowSchema for SDN
└── alert-rules.yaml         (-78 lines)   Prometheus alerts for SDN

pkg/network/
├── openshift_sdn.go         (-~600 lines) Core SDN reconcile logic
└── openshift_sdn_test.go    (-~400 lines) Tests for above
```

#### Modified Files (SDN References Removed)

```
bindata/kube-proxy/kube-proxy.yaml     (+1 / -1)   Removed SDN-specific node selector logic
bindata/network/multus/multus.yaml     (+1 / -3)   Removed SDN-specific toleration/annotation
pkg/network/network.go                 (multiple)  Removed SDN case from plugin switch
docs/...                               (+6 / -8)   Updated supported plugin documentation
```

---

## Component Relationships

### Before: CNO with Dead SDN Path

```
┌──────────────────────────────────────────────────────────┐
│                  Cluster Network Operator                │
│                                                          │
│  ┌─────────────────────┐    ┌────────────────────────┐  │
│  │   Reconcile Loop    │    │   Plugin Registry      │  │
│  │                     │    │                        │  │
│  │  1. Read Network CR │    │  ┌──────────────────┐  │  │
│  │  2. Validate type   │───►│  │  OVN-Kubernetes  │  │  │
│  │  3. Dispatch to     │    │  │  (ACTIVE)        │  │  │
│  │     plugin handler  │    │  └──────────────────┘  │  │
│  │                     │    │                        │  │
│  │  ┌───────────────┐  │    │  ┌──────────────────┐  │  │
│  │  │  SDN Reject   │  │    │  │  OpenShift SDN   │  │  │
│  │  │  Gate ──────► │  │    │  │  (DEAD CODE) ░░░ │  │  │
│  │  │  Returns err  │  │    │  └──────────────────┘  │  │
│  │  └───────────────┘  │    │                        │  │
│  └─────────────────────┘    └────────────────────────┘  │
│                                                          │
│  bindata/network/                                        │
│  ├── ovn-kubernetes/   (rendered and applied)            │
│  ├── multus/           (rendered and applied)            │
│  └── openshift-sdn/    (NEVER rendered) ░░░░░░░░░░░░░░  │
└──────────────────────────────────────────────────────────┘
```

### After: CNO with SDN Code Removed

```
┌──────────────────────────────────────────────────────────┐
│                  Cluster Network Operator                │
│                                                          │
│  ┌─────────────────────┐    ┌────────────────────────┐  │
│  │   Reconcile Loop    │    │   Plugin Registry      │  │
│  │                     │    │                        │  │
│  │  1. Read Network CR │    │  ┌──────────────────┐  │  │
│  │  2. Validate type   │───►│  │  OVN-Kubernetes  │  │  │
│  │  3. Dispatch to     │    │  │  (ACTIVE)        │  │  │
│  │     plugin handler  │    │  └──────────────────┘  │  │
│  │                     │    │                        │  │
│  │  ┌───────────────┐  │    └────────────────────────┘  │
│  │  │  SDN Reject   │  │                                 │
│  │  │  Gate ──────► │  │    bindata/network/             │
│  │  │  Returns err  │  │    ├── ovn-kubernetes/           │
│  │  └───────────────┘  │    ├── multus/                   │
│  └─────────────────────┘    └── [openshift-sdn/ GONE]    │
└──────────────────────────────────────────────────────────┘
```

### Multus and kube-proxy: Reduced Surface Area

Before, both shared templates contained SDN-conditional logic:

```
multus.yaml (before)                    multus.yaml (after)
───────────────────────────────         ─────────────────────
tolerations:                            tolerations:
  - key: node-role.../master              - key: node-role.../master
    ...                                     ...
  # SDN-specific:                       # (SDN block removed)
  - key: network.operator.io/sdn
    effect: NoSchedule                  annotations:
annotations:                              networkoperator.openshift.io/...
  networkoperator.openshift.io/...
  # SDN-specific:
  openshift.io/sdn-node-ready: "false"
```

---

## Data Flow: Before and After

### Network Plugin Reconcile Flow (Before)

```
Network CR Created/Updated
         │
         ▼
┌────────────────────┐
│  Read Network CR   │
│  Spec.Type = ?     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐        ┌─────────────────────────┐
│  Validate Plugin   │──SDN──►│  Return Error:          │
│  Type              │        │  "SDN not supported"    │
└────────┬───────────┘        └─────────────────────────┘
         │ OVN-K
         ▼
┌────────────────────┐
│  Switch on Type    │
│  case "OVN-K":     │──────► OVN-K reconcile logic
│  case "SDN":       │──────► [DEAD - rejection above prevents reach]
│  default: error    │
└────────────────────┘
         │ OVN-K path only
         ▼
┌────────────────────┐
│  Render bindata/   │
│  templates         │──────► bindata/network/ovn-kubernetes/
│                    │──────► bindata/network/multus/
│                    │        bindata/network/openshift-sdn/ [NEVER]
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Apply to API      │
│  Server            │
└────────────────────┘
```

### Network Plugin Reconcile Flow (After)

```
Network CR Created/Updated
         │
         ▼
┌────────────────────┐
│  Read Network CR   │
│  Spec.Type = ?     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐        ┌─────────────────────────┐
│  Validate Plugin   │──SDN──►│  Return Error:          │
│  Type              │        │  "SDN not supported"    │
└────────┬───────────┘        └─────────────────────────┘
         │ OVN-K
         ▼
┌────────────────────┐
│  Switch on Type    │
│  case "OVN-K":     │──────► OVN-K reconcile logic
│  default: error    │        (No SDN case exists)
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Render bindata/   │
│  templates         │──────► bindata/network/ovn-kubernetes/
│                    │──────► bindata/network/multus/
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Apply to API      │
│  Server            │
└────────────────────┘
```

**Behavioral difference:** None. The output of both flows is identical for every valid (non-SDN) input, and both return the same error for SDN input.

---

## Detailed Changes

### Go Code Changes (`pkg/`)

#### `pkg/network/network.go`

Removed all `case NetworkTypeOpenShiftSDN:` branches from the plugin dispatch switch statements. These branches were:

1. **`renderNetworkConfig()`** — Removed SDN render call
2. **`validateNetworkConfig()`** — Removed SDN-specific validation (rejection gate remains)
3. **`isNetworkPluginSupported()`** — Removed SDN from the supported list (it was only