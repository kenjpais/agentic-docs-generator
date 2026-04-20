# Design Document: No-Overlay Mode Support for OVN-Kubernetes in CNO

**Feature:** CORENET-6100 — Add support for no-overlay mode in OVN-Kubernetes default network
**PR:** #2844 (`ricky-rav/nooverlay`)
**Status:** Merged
**Author:** ricky-rav
**Document Path:** `agentic/design-docs/ovnk-no-overlay-mode.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals and Non-Goals](#3-goals-and-non-goals)
4. [Background and Context](#4-background-and-context)
5. [Architecture Overview](#5-architecture-overview)
6. [Detailed Design](#6-detailed-design)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Component Relationships](#8-component-relationships)
9. [API Design](#9-api-design)
10. [Alternatives Considered](#10-alternatives-considered)
11. [Implementation Reference](#11-implementation-reference)
12. [Risk Assessment](#12-risk-assessment)
13. [Testing Strategy](#13-testing-strategy)
14. [Open Questions](#14-open-questions)

---

## 1. Executive Summary

This feature introduces a configuration knob in the **Cluster Network Operator (CNO)** that allows operators to deploy OVN-Kubernetes (OVN-K) with **no-overlay mode** enabled on the default network. In no-overlay mode, OVN-K eliminates the overlay network encapsulation (e.g., Geneve tunnels), relying instead on the underlay network to route pod traffic directly between nodes. This reduces latency, eliminates per-packet encapsulation overhead, and is valuable in bare-metal or high-performance networking scenarios where the underlay is fully routable.

The implementation touches the CNO API (CRD), OVN-K bindata manifests, and the CNO reconciliation/rendering pipeline. It introduces a new field in the `OVNKubernetesConfig` spec and propagates it through the entire CNO stack.

---

## 2. Problem Statement

### Current State

OVN-Kubernetes in OpenShift always deploys with an **overlay network** — specifically a Geneve-based tunnel mesh between nodes. Every pod-to-pod packet crossing node boundaries is encapsulated in a Geneve header, processed by OVN, and decapsulated at the destination. This model:

- Works universally across any underlay topology
- Adds measurable encapsulation overhead (CPU, latency, MTU reduction)
- Prevents direct use of the underlay's routing fabric for pod traffic

### The Gap

In environments where the physical underlay is fully routable and operators have control over the BGP/routing infrastructure (e.g., bare-metal deployments, telco environments, performance-sensitive workloads), the overlay is unnecessary overhead. OVN-Kubernetes natively supports a **no-overlay** (or "local gateway + no encapsulation") mode, but CNO provides no mechanism to enable it.

### Impact

Operators wanting no-overlay mode must manually patch manifests, fork CNO configuration, or accept the performance penalty — all of which are unsupported, error-prone, and blocked on upgrades.

---

## 3. Goals and Non-Goals

### Goals

- ✅ Add a first-class API field in CNO's `Network` CRD to enable no-overlay mode for OVN-K
- ✅ Propagate the configuration through CNO's rendering pipeline into OVN-K manifests
- ✅ Support the field across all CRD feature-gate variants (Default, TechPreview, DevPreview, CustomNoUpgrade, OKD)
- ✅ Ensure the knob is additive and backward-compatible (disabled by default)
- ✅ Document the new field in API and operator documentation

### Non-Goals

- ❌ Supporting no-overlay mode for network types other than OVN-Kubernetes
- ❌ Automatic BGP/routing configuration of the underlay (operator responsibility)
- ❌ Runtime toggling of the mode without node/cluster disruption
- ❌ No-overlay for secondary networks (only the default network is in scope)

---

## 4. Background and Context

### OVN-Kubernetes Overlay vs. No-Overlay

```
OVERLAY MODE (default)
┌─────────────────────────────────────────────────────────┐
│  Node A                          Node B                  │
│  ┌──────────────┐                ┌──────────────┐        │
│  │  Pod (10.x)  │                │  Pod (10.x)  │        │
│  └──────┬───────┘                └──────┬───────┘        │
│         │                               │                │
│  ┌──────▼───────┐   Geneve tunnel ┌─────▼────────┐       │
│  │  ovn-k node  │◄───────────────►│  ovn-k node  │       │
│  └──────────────┘                └──────────────┘        │
│     Encap/Decap overhead; MTU reduced by ~50 bytes       │
└─────────────────────────────────────────────────────────┘

NO-OVERLAY MODE (this feature)
┌─────────────────────────────────────────────────────────┐
│  Node A                          Node B                  │
│  ┌──────────────┐                ┌──────────────┐        │
│  │  Pod (10.x)  │                │  Pod (10.x)  │        │
│  └──────┬───────┘                └──────┬───────┘        │
│         │                               │                │
│  ┌──────▼───────┐   Underlay routed ┌──▼─────────────┐  │
│  │  ovn-k node  │◄─────────────────►│  ovn-k node    │  │
│  └──────────────┘  (BGP/static)     └────────────────┘  │
│     No encapsulation; full MTU; underlay must be routable│
└─────────────────────────────────────────────────────────┘
```

### OVN-K Native Support

OVN-Kubernetes supports no-overlay via the `--no-hostsubnet-nodes` and related flags (or newer equivalents). CNO must expose this as a supported, managed configuration path.

### CRD Feature Gate Variants

OpenShift maintains multiple CRD feature-gate tiers. All five variants must receive the new field:

| File | Tier | Audience |
|------|------|----------|
| `networks-Default.crd.yaml` | Default | All clusters |
| `networks-TechPreviewNoUpgrade.crd.yaml` | Tech Preview | Preview features |
| `networks-DevPreviewNoUpgrade.crd.yaml` | Dev Preview | Development |
| `networks-CustomNoUpgrade.crd.yaml` | Custom | Custom feature sets |
| `networks-OKD.crd.yaml` | OKD | Community |

---

## 5. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OPERATOR PLANE                               │
│                                                                     │
│   User/Admin                                                        │
│       │                                                             │
│       │  kubectl edit network.operator.openshift.io cluster        │
│       │  spec.defaultNetwork.ovnKubernetesConfig.routingViaHost:   │
│       │    noOverlay: true                                          │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                Cluster Network Operator (CNO)                │   │
│  │                                                             │   │
│  │  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │   │
│  │  │ API/CRD     │───►│  Reconciler  │───►│  Renderer    │   │   │
│  │  │ Validation  │    │  (network.go)│    │ (ovn.go)     │   │   │
│  │  └─────────────┘    └──────────────┘    └──────┬───────┘   │   │
│  │                                                │            │   │
│  │                                   ┌────────────▼──────────┐ │   │
│  │                                   │  Bindata Manifests    │ │   │
│  │                                   │  (templated YAML)     │ │   │
│  │                                   └────────────┬──────────┘ │   │
│  └────────────────────────────────────────────────┼────────────┘   │
│                                                   │                │
└───────────────────────────────────────────────────┼────────────────┘
                                                    │
                        ┌───────────────────────────▼───────────────┐
                        │            DATA PLANE                      │
                        │                                            │
                        │   ┌────────────────────────────────────┐  │
                        │   │  ovnkube-control-plane (DaemonSet) │  │
                        │   │   --no-overlay flag injected        │  │
                        │   └────────────────────────────────────┘  │
                        │                                            │
                        │   ┌────────────────────────────────────┐  │
                        │   │  ovnkube-node (DaemonSet)           │  │
                        │   │   --no-overlay flag injected        │  │
                        │   └────────────────────────────────────┘  │
                        │                                            │
                        │   ┌────────────────────────────────────┐  │
                        │   │  OVN ConfigMap (004-config.yaml)   │  │
                        │   │   no-overlay: "true"               │  │
                        │   └────────────────────────────────────┘  │
                        └────────────────────────────────────────────┘
```

---

## 6. Detailed Design

### 6.1 API Layer — CRD Schema Extension

A new field is introduced in the `OVNKubernetesConfig` struct:

```go
// OVNKubernetesConfig contains the configuration parameters for networks
// using the OVN-Kubernetes network project.
type OVNKubernetesConfig struct {
    // ... existing fields ...

    // routingViaHost configures routing of pod traffic through the host
    // network stack instead of the OVN overlay.
    // +optional
    RouteViaHost *OVNKubernetesNoOverlayConfig `json:"routeViaHost,omitempty"`
}

// OVNKubernetesNoOverlayConfig defines no-overlay routing settings.
type OVNKubernetesNoOverlayConfig struct {
    // enabled, when true, disables Geneve tunnel encapsulation for pod
    // traffic. The underlay network must be configured to route pod
    // CIDRs between all nodes. This cannot be changed after cluster
    // installation without disruption.
    // +optional
    Enabled bool `json:"enabled,omitempty"`
}
```

**Field naming rationale:** `routeViaHost` is preferred over `noOverlay` because it is descriptive of the positive behavior (traffic routes via host network stack) rather than defining itself by what it removes, following OpenShift API conventions.

**Immutability:** This field must be treated as effectively immutable post-install. Changing it requires node reconfiguration and network disruption. Validation webhooks or status conditions should guard this.

### 6.2 CRD Schema (YAML)

Added to all five CRD variant files under `spec.defaultNetwork.ovnKubernetesConfig`:

```yaml
routeViaHost:
  description: >-
    routeViaHost allows pod egress traffic to exit via the ovn-k8s-mp0
    management port into the host before sending it out. This is useful
    for host-based firewall policies or when the underlay handles pod
    routing directly (no-overlay mode).
  type: object
  properties:
    enabled:
      description: >-
        enabled controls whether routing via host is active. When true,
        Geneve tunnel encapsulation is disabled and the underlay network
        must route pod CIDRs.
      type: boolean
      default: false
```

**Reference files:**
- `manifests/0000_70_network_01_networks-Default.crd.yaml` (+130 lines)
- `manifests/0000_70_network_01_networks-TechPreviewNoUpgrade.crd.yaml` (+143 lines)
- `manifests/0000_70_network_01_networks-DevPreviewNoUpgrade.crd.yaml` (+143 lines)
- `manifests/0000_70_network_01_networks-CustomNoUpgrade.crd.yaml` (+143 lines)
- `manifests/0000_70_network_01_networks-OKD.crd.yaml` (+1 line, rename + field)

### 6.3 CNO Reconciliation Pipeline

The CNO reconciliation for OVN-K follows this path:

```
pkg/network/ovn.go
    └── renderOVNKubernetes()
            ├── reads OVNKubernetesConfig.RouteViaHost.Enabled
            ├── builds renderData map
            │       └── adds "OVNKubernetesNoOverlay": true/false
            └── passes renderData to bindata renderer
                    ├── bindata/.../004-config.yaml
                    ├── bindata/.../ovnkube-control-plane.yaml
                    └── bindata/.../ovnkube-node.yaml
```

**Key Go changes** (`pkg/network/ovn.go`):

```go
// Propagate no-overlay setting into render data
noOverlay := false
if conf.RouteViaHost != nil && conf.RouteViaHost.Enabled {
    noOverlay = true
}
renderData.Data["OVNKubernetesNoOverlay"] = noOverlay
```

### 6.4 Bindata Manifest Templates

Three manifest files are templated to conditionally inject the no-overlay configuration:

#### `bindata/network/ovn-kubernetes/self-hosted/004-config.yaml`

```yaml
# OVN config map — adds no-overlay key
data:
  # ... existing keys ...
  {{- if .OVNKubernetesNoOverlay }}
  no-overlay: "true"
  {{- end }}
```

#### `bindata/network/ovn-kubernetes/self-hosted/ovnkube-control-plane.yaml`

```yaml
# Injects --no-overlay CLI flag into the control-plane container args
containers:
  - name: ovnkube-master
    args:
      # ... existing args ...
      {{- if .OVNKubernetesNoOverlay }}
      - "--no-overlay"
      {{- end }}
```

#### `bindata/network/ovn-kubernetes/self-hosted/ovnkube-node.yaml`

```yaml
# Injects --no-overlay CLI flag into the node container args
containers:
  - name: ovnkube-node
    args:
      # ... existing args ...
      {{- if .OVNKubernetesNoOverlay }}
      - "--no-overlay"
      {{- end }}
```

### 6.5 Validation Logic

New validation rules added to the CNO network validation layer:

```
pkg/network/validation.go (or ovn_validate.go)

validateOVNKubernetesConfig()
    └── if RouteViaHost.Enabled == true:
            ├── REJECT if network type != OVNKubernetes
            ├── WARN if no BGP/routing configuration detected (advisory)
            └── REJECT if attempting to change from existing cluster state
                (immutability guard — compare with current applied config)
```

**Immutability enforcement:**