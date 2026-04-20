# ADR-4373406: Add ValidatingAdmissionPolicy to Prevent Duplicate EgressIP Mark Annotations

**File path:** `agentic/decisions/adr-4373406-egressip-duplicate-mark-vap.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 4373406 |
| **Date** | 2025-08-20 |
| **Status** | Accepted |
| **Jira** | [OCPBUGS-60670](https://issues.redhat.com/browse/OCPBUGS-60670) |
| **PR** | [#2837](https://github.com/openshift/cluster-network-operator/pull/2837) |
| **Decision Makers** | arghosh93, OVN-Kubernetes networking team |
| **Affected Component** | `ovnkube-control-plane`, EgressIP admission, CNO (cluster-network-operator) |

---

## Context

When `ovnkube-control-plane` starts, it reads existing `EgressIP` CRs and attempts to reserve the mark ID stored in the `k8s.ovn.org/egressip-mark` annotation. If two or more `EgressIP` CRs carry the **same mark value**, the reservation logic fails on the second object with:

```
factory.go:1301] Failed (will retry) while processing existing *v1.EgressIP items:
  failed to reserve mark for EgressIP <name>: failed to reserve mark: id 0 is already reserved by another resource
```

This retry loop prevents the pod from completing startup, causing it to enter `CrashLoopBackOff`. Because `ovnkube-control-plane` is cluster-wide, **all OVN-Kubernetes networking** is disrupted.

### Root Cause

Duplicate `egressip-mark` annotation values can appear on `EgressIP` objects (the exact write path that produces duplicates is not fully understood as of this ADR). Once duplicates exist in etcd, every subsequent `ovnkube-control-plane` restart will crash.

### Prior Workaround

Operators had to manually strip the annotation from all EgressIP objects:

```bash
oc annotate egressip -A --all k8s.ovn.org/egressip-mark-
```

This allowed the control plane to restart and re-allocate marks without collision. Clusters managed by GitOps/ArgoCD required pausing application sync to prevent the duplicate annotation from being re-applied.

---

## Decision

Introduce a **Kubernetes `ValidatingAdmissionPolicy`** (VAP) that rejects any `EgressIP` create or update operation that would result in a duplicate `k8s.ovn.org/egressip-mark` annotation value across the cluster.

The policy is deployed as static bindata managed by CNO.

**Primary artifact:**
```
bindata/network/ovn-kubernetes/common/egressip-admission-policy.yaml  (+39 lines)
```

**Test coverage update:**
```
pkg/network/ovn_kubernetes_test.go  (4 lines changed)
```

---

## Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| **Heal duplicates at startup in `ovnkube-control-plane`** | Masks the root cause; control-plane startup code should not repair data corruption. Upstream fix deferred. |
| **Webhook-based admission** | VAP is GA in Kubernetes 1.30+ (OpenShift 4.17+), requires no additional webhook server, lower operational overhead. |
| **Manual runbook only** | Already the existing workaround; does not prevent recurrence. Customer clusters have hit this bug in production. |
| **Remove annotation entirely** | Annotation is load-bearing for mark reservation; removing it changes the protocol between components. |

---

## Consequences

### Positive

- **Prevents crash**: Duplicate marks are rejected at admission time before they can reach etcd, eliminating the crash trigger.
- **Zero runtime overhead**: VAP is evaluated by the API server; no additional pod or webhook server is required.
- **Cluster-scoped enforcement**: All `EgressIP` writes cluster-wide pass through the policy.
- **Operationally transparent**: Rejection surfaces as a clear API error to the caller, including GitOps controllers, making the failure visible rather than silent.

### Negative / Trade-offs

- **Does not fix existing duplicates**: Clusters already in a broken state still require the manual annotation-strip workaround before the policy can be applied.
- **Does not identify the write path**: The upstream code path that produces duplicate annotations is still unknown; this is a defensive guard, not a root-cause fix.
- **CNO-managed lifecycle**: The VAP lives in CNO bindata, meaning updates require a CNO upgrade cycle rather than an in-cluster config change.

### Risks

| Risk | Mitigation |
|---|---|
| VAP blocks legitimate mark reuse during EgressIP migration | Policy must be scoped to reject only **concurrent** duplicates across distinct EgressIP objects, not sequential reuse after deletion. Validate with test coverage in `ovn_kubernetes_test.go`. |
| Policy not applied to clusters already on affected versions | Backport ADR and VAP to relevant z-stream branches. |

---

## Implementation Details

### Files Changed

| File | Change | Purpose |
|---|---|---|
| `bindata/network/ovn-kubernetes/common/egressip-admission-policy.yaml` | +39 lines | Defines `ValidatingAdmissionPolicy` and `ValidatingAdmissionPolicyBinding` for EgressIP mark uniqueness |
| `pkg/network/ovn_kubernetes_test.go` | +4 / -4 lines | Updates test fixtures to account for new VAP bindata being rendered |

### Policy Placement

The YAML is in `bindata/network/ovn-kubernetes/common/` — the shared (non-platform-specific) OVN-Kubernetes resource directory rendered by CNO on all supported platforms.

### Enforcement Scope

- **Resource:** `EgressIP` (cluster-scoped)
- **Operations guarded:** `CREATE`, `UPDATE`
- **Annotation key:** `k8s.ovn.org/egressip-mark`
- **Invariant enforced:** No two `EgressIP` objects may share the same annotation value at admission time.

---

## References

- Jira: OCPBUGS-60670 — *ovnkube-control-plane pods crashing when egressip-mark annotation duplicated on egressip*
- Upstream (OVN-Kubernetes) PR: referenced in Jira as u/s merged prior to this CNO downstream PR
- Related workaround command: `oc annotate egressip -A --all k8s.ovn.org/egressip-mark-`
- Kubernetes VAP documentation: `ValidatingAdmissionPolicy` (GA, Kubernetes 1.30+)

---

## Status History

| Date | Status | Note |
|---|---|---|
| 2025-08-20 | **Accepted** | PR #2837 merged; upstream OVN-Kubernetes PR previously merged |