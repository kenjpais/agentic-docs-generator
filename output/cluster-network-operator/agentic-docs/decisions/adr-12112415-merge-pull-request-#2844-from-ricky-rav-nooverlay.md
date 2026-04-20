# ADR-2844: Add No-Overlay Mode Support for OVN-Kubernetes Default Network in CNO

**File path:** `agentic/decisions/adr-2844-ovn-kubernetes-no-overlay-mode.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 2844 |
| **Date** | 2025 |
| **Status** | Accepted |
| **PR** | #2844 |
| **Jira** | CORENET-6100 |
| **Decision-Makers** | CNO / Network team (ricky-rav) |
| **Affects** | `pkg/network/ovn_kubernetes.go`, `pkg/controller/operconfig/operconfig_controller.go`, `manifests/`, `bindata/network/ovn-kubernetes/self-hosted/` |

---

## Context

OVN-Kubernetes supports a **no-overlay** networking mode in which pods communicate over the underlay network directly, without VXLAN/Geneve encapsulation. This mode is desirable for environments where encapsulation overhead is unacceptable or where the underlying network fabric can enforce pod-level routing natively.

Prior to this change, the Cluster Network Operator (CNO) had no mechanism to configure OVN-K in no-overlay mode for the **default network**. The capability existed in OVN-K itself, but CNO did not expose a knob in the `Network` operator API, meaning operators could not declaratively enable this mode through the standard OpenShift API surface.

### Drivers

- Users running performance-sensitive workloads need to eliminate encapsulation overhead.
- The underlay-routing topology requires OVN-K to operate without overlay tunnels on the default network.
- CNO is the authoritative controller for OVN-K deployment configuration; the feature must be exposed through the `operator.openshift.io/v1` `Network` CRD.

### Technical State Before This ADR

- `operator/v1/types_network.go` had no `NoOverlayConfig` type.
- `bindata/network/ovn-kubernetes/self-hosted/` manifests did not conditionally set OVN-K no-overlay flags.
- The `OVNKubernetesConfig` struct lacked a `NoOverlay` field.
- CRD manifests (`manifests/0000_70_network_01_networks-*.crd.yaml`) did not include the no-overlay schema.

---

## Decision

**Introduce a `NoOverlayConfig` knob in the `OVNKubernetesConfig` API and wire it through CNO to the OVN-K deployment manifests.**

Specifically:

1. **Extend the `operator/v1` Network API** — add `NoOverlayConfig` struct and a `NoOverlay` field inside `OVNKubernetesConfig` in `vendor/github.com/openshift/api/operator/v1/types_network.go`.

2. **Regenerate CRD manifests** — update all feature-gated CRD variants:
   - `manifests/0000_70_network_01_networks-Default.crd.yaml`
   - `manifests/0000_70_network_01_networks-TechPreviewNoUpgrade.crd.yaml`
   - `manifests/0000_70_network_01_networks-DevPreviewNoUpgrade.crd.yaml`
   - `manifests/0000_70_network_01_networks-CustomNoUpgrade.crd.yaml`
   - `manifests/0000_70_network_01_networks-OKD.crd.yaml`

3. **Propagate the flag through CNO rendering** — `pkg/network/ovn_kubernetes.go` reads `NoOverlay` from the operator config and injects the corresponding argument into OVN-K pods.

4. **Update self-hosted bindata manifests** — `bindata/network/ovn-kubernetes/self-hosted/004-config.yaml`, `ovnkube-control-plane.yaml`, and `ovnkube-node.yaml` conditionally include the no-overlay flag when the knob is enabled.

5. **Add apply-configuration support** — `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/nooverlayconfig.go` and the updated `ovnkubernetesconfig.go` apply-configuration enable server-side apply workflows for the new field.

6. **Update operconfig controller** — `pkg/controller/operconfig/operconfig_controller.go` handles the new field during reconciliation.

---

## Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| Expose no-overlay only via OVN-K DaemonSet annotations/env vars directly | Bypasses CNO's reconciliation loop; creates drift between desired and actual state; not observable via the standard operator API. |
| Add no-overlay as a cluster-wide feature gate only | Feature gates are coarse-grained; this needs to be a per-network-operator knob under `OVNKubernetesConfig` to follow existing API patterns (e.g., `BGPManagedConfig`). |
| Defer to a standalone admission webhook | Over-engineered; CNO already owns OVN-K lifecycle and is the correct layer for this configuration. |

---

## Consequences

### Positive

- Operators can declaratively enable no-overlay mode for the default network via the standard `operator.openshift.io/v1` `Network` CR — no manual DaemonSet patching required.
- CNO's reconciliation loop ensures the no-overlay flag is enforced and drift-corrected automatically.
- The API extension follows the established pattern of `OVNKubernetesConfig` sub-structs (consistent with `BGPManagedConfig`).
- All feature-gated CRD variants are updated consistently, preserving upgrade compatibility.

### Negative / Risks

- No-overlay mode changes the fundamental dataplane topology; misconfiguration on an overlay-dependent cluster will cause network disruption. **Mitigation**: field is opt-in; default value is off.
- The feature adds surface area to the `Network` CRD across all feature gate tiers, which must be kept in sync with `openshift/api` upstream.

### Neutral

- Vendor bump of `github.com/openshift/api` and `github.com/openshift/client-go` is required (`go.mod`, `go.sum`, `vendor/modules.txt` updated). This is a routine vendoring update.
- Generated files (`zz_generated.*`) in the vendored API are updated as a consequence; no manual editing of generated code.

---

## Key File Locations

| Purpose | Path |
|---|---|
| OVN-K operator API types | `vendor/github.com/openshift/api/operator/v1/types_network.go` |
| CNO OVN-K rendering logic | `pkg/network/ovn_kubernetes.go` |
| Operconfig controller | `pkg/controller/operconfig/operconfig_controller.go` |
| No-overlay apply-config | `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/nooverlayconfig.go` |
| Self-hosted node manifest | `bindata/network/ovn-kubernetes/self-hosted/ovnkube-node.yaml` |
| Self-hosted control-plane manifest | `bindata/network/ovn-kubernetes/self-hosted/ovnkube-control-plane.yaml` |
| OVN-K config bindata | `bindata/network/ovn-kubernetes/self-hosted/004-config.yaml` |
| CRD manifests (all tiers) | `manifests/0000_70_network_01_networks-*.crd.yaml` |
| Unit tests | `pkg/network/ovn_kubernetes_test.go`, `pkg/network/ovn_kubernetes_dpu_host_test.go` |

---

## References

- Jira: [CORENET-6100](https://issues.redhat.com/browse/CORENET-6100) — Cluster Network Operator integration for no-overlay mode
- PR: #2844 (`ricky-rav/nooverlay`)
- Related API pattern: `BGPManagedConfig` in `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/bgpmanagedconfig.go`