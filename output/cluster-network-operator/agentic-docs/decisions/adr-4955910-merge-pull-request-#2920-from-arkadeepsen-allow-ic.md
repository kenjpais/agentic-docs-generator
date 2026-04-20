# ADR-2920: Add Configuration Override for Allow-ICMP Network Policy

**File**: `agentic/decisions/adr-2920-allow-icmp-netpol-config-override.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 2920 |
| **Date** | 2025 |
| **Status** | Accepted |
| **PR** | #2920 |
| **Jira** | CORENET-6813 |
| **Decision Makers** | OVN-Kubernetes / CNO maintainers |
| **Directory** | `agentic/decisions/` |

---

## Title

Add configuration override knob in CNO (Cluster Network Operator) for `allow-icmp-network-policy` in OVN-Kubernetes.

---

## Context

OVN-Kubernetes has a feature flag (`allow-icmp-network-policy`) that controls whether ICMP traffic is permitted through network policies. Previously, Cluster Network Operator (CNO) had no mechanism to expose or override this OVN-Kubernetes configuration value at the operator level.

This created a gap: cluster administrators and higher-level controllers could not toggle this behavior through the CNO configuration surface without directly modifying OVN-Kubernetes internals.

**Affected components:**

| File | Role |
|---|---|
| `bindata/network/ovn-kubernetes/common/008-script-lib.yaml` | Shell script library injected into OVN-K pods; renders startup configuration |
| `pkg/network/ovn_kubernetes.go` | CNO's Go-layer integration point for OVN-Kubernetes configuration |
| `pkg/network/ovn_kubernetes_test.go` | Unit tests covering the new override behavior |

---

## Decision

Implement a configuration override in CNO that propagates an `allow-icmp-network-policy` toggle from the CNO-level configuration down into the OVN-Kubernetes script library at pod startup.

**Mechanism:**

1. **`pkg/network/ovn_kubernetes.go`** (+11 lines): Read the new config field and pass it into the OVN-K rendering pipeline.
2. **`bindata/network/ovn-kubernetes/common/008-script-lib.yaml`** (+8 lines): Template the new flag into the script library so it is available when OVN-K pods initialize.
3. **`pkg/network/ovn_kubernetes_test.go`** (+55 lines): Validate that the override is applied correctly under expected conditions.

---

## Rationale

### Why a CNO-level config knob?

- **Single control plane**: CNO is the authoritative operator for network configuration in OpenShift. Exposing behavioral flags through CNO keeps cluster network configuration in one place, consistent with existing operator patterns.
- **No direct OVN-K mutation**: Avoids requiring cluster admins to patch OVN-Kubernetes manifests directly, which would be fragile and unsupported.
- **Script-lib injection pattern**: The `008-script-lib.yaml` bindata pattern is the established mechanism for passing runtime configuration into OVN-K pods. Using this pattern is consistent with the existing codebase.

### Why ICMP specifically?

CORENET-6813 identifies a requirement to make ICMP policy enforcement configurable. ICMP behavior within network policies can affect cluster diagnostics (e.g., `ping`-based health checks) and must be tunable per deployment requirements without requiring a full OVN-K version change.

---

## Consequences

### Positive

- Cluster administrators gain a supported, CNO-managed override for ICMP network policy behavior.
- Implementation follows established bindata + Go rendering patterns; no new architectural patterns introduced.
- Unit test coverage (+55 lines) mechanically verifies the override is propagated correctly.

### Negative / Trade-offs

- Adds one more configuration field to the CNO OVN-Kubernetes configuration surface; increases the operator's configuration API footprint incrementally.
- The value is injected via shell script library at pod startup — changes require pod restart to take effect (consistent with existing behavior for script-lib values, not a new limitation).

### Neutral

- No changes to CRD schema were captured in the provided diff; if a new API field is required, that addition is tracked separately under CORENET-6813 acceptance criteria.

---

## Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| Direct OVN-K DaemonSet env-var patching by admins | Unsupported mutation path; fragile across upgrades |
| Defaulting ICMP policy to always-allow or always-deny | Removes operator flexibility; does not meet CORENET-6813 requirements |
| Separate admission webhook to enforce ICMP policy | Disproportionate complexity for a single boolean flag |

---

## Implementation Locations

```
bindata/network/ovn-kubernetes/common/008-script-lib.yaml   # Flag templated into startup script
pkg/network/ovn_kubernetes.go                               # Config read + rendering (+11 lines)
pkg/network/ovn_kubernetes_test.go                          # Unit tests (+55 lines)
```

---

## References

- Jira: [CORENET-6813 — Implement the config knob in CNO](https://issues.redhat.com/browse/CORENET-6813)
- PR: [#2920 — allow-icmp-netpol config override](../../pulls/2920)
- Related bindata pattern: `bindata/network/ovn-kubernetes/common/`