# ADR-2897: Handle Zero-Worker HyperShift Clusters in Daemonset Rollout

**File location:** `agentic/decisions/adr-2897-zero-worker-hypershift-daemonset-rollout.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 2897 |
| **Date** | 2025 |
| **Status** | Accepted |
| **PR** | #2897 (GitHub PR ID: #10844976) |
| **Jira** | CORENET-6871 |
| **Decision Makers** | weliang1 (author) |
| **Files Affected** | `pkg/network/ovn_kubernetes.go`, `pkg/network/ovn_kubernetes_test.go` |

---

## Context

HyperShift is an OpenShift hosting model where the control plane runs as pods in a management cluster, with worker nodes optionally absent (zero-worker topology). In this configuration, a hosted cluster can exist with no worker nodes at all — only control-plane components running in the management cluster's namespace.

The existing OVN-Kubernetes daemonset rollout logic did not account for this topology. When computing rollout progress or determining rollout completion for a daemonset, the code assumed at least one worker node would be present. In a zero-worker HyperShift cluster, this assumption caused incorrect rollout state evaluation — the rollout could be misreported as stuck, incomplete, or erroring because denominators or node counts were derived from an assumed non-zero worker pool.

**Key constraint:** The daemonset rollout path in `pkg/network/ovn_kubernetes.go` is shared across standard OCP clusters and HyperShift hosted clusters. Any fix must not regress standard cluster behavior.

---

## Problem

The control-plane rollout logic in `pkg/network/ovn_kubernetes.go` failed to handle the case where a HyperShift hosted cluster has **zero worker nodes**. Specifically:

- Rollout completion checks that divide by or iterate over worker node counts produce incorrect results (division by zero, vacuous loops, or false-negative readiness signals) when the worker count is `0`.
- There was no explicit guard or branch for the zero-worker case, meaning the code path was exercised with an invalid assumption.
- No test coverage existed for this topology prior to this change (`pkg/network/ovn_kubernetes_test.go` had `+141` lines added, all net-new).

---

## Decision

**Add an explicit guard in the OVN-Kubernetes daemonset rollout logic to detect and correctly handle zero-worker HyperShift clusters.**

The production change is minimal and surgical (`pkg/network/ovn_kubernetes.go`: `+1 -1`) — a single line replacement that introduces the zero-worker guard in the rollout evaluation path. The bulk of the change (`+141` lines) is comprehensive test coverage validating correct behavior across both zero-worker and non-zero-worker topologies.

### Specific change rationale

| Aspect | Choice | Rationale |
|---|---|---|
| **Scope of change** | Single-line guard in production code | Minimizes regression risk; zero-worker is a narrow edge case requiring a narrow fix |
| **Test strategy** | 141 lines of net-new tests | Zero-worker is a topology with no prior coverage; correctness must be mechanically verified |
| **Location** | `pkg/network/ovn_kubernetes.go` | Rollout logic is centralized here; fix belongs at the evaluation site, not at call sites |
| **Approach** | Handle at rollout evaluation, not at cluster creation | Cluster topology may change; evaluation-time guard is more robust |

---

## Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| Skip daemonset rollout entirely for zero-worker clusters | Too broad; daemonset rollout still applies to control-plane node components in some HyperShift topologies |
| Guard at the caller (upstream of rollout logic) | Multiple callers exist; fixing at the evaluation site avoids N-site fixes and future regression |
| Treat zero-worker as an error/abort condition | Zero-worker is a valid, supported HyperShift topology — it must succeed, not abort |

---

## Consequences

### Positive

- Zero-worker HyperShift hosted clusters no longer produce incorrect rollout state during OVN-Kubernetes daemonset updates.
- 141 lines of new tests provide regression coverage for this topology going forward.
- The production change is a one-line fix, keeping review surface minimal and merge risk low.

### Negative / Trade-offs

- The guard is a special-case branch, adding a small amount of conditional complexity to the rollout path.

### Risks

- **Low.** The production delta is `+1 -1`. The zero-worker branch is exercised only when worker count is explicitly zero, leaving all other code paths untouched.

---

## Code Locations

| Purpose | File |
|---|---|
| Rollout evaluation logic (fix site) | `pkg/network/ovn_kubernetes.go` |
| Test coverage for zero-worker topology | `pkg/network/ovn_kubernetes_test.go` |

---

## Links

- **PR:** [#2897](https://github.com/openshift/cluster-network-operator/pull/2897)
- **Jira:** [CORENET-6871](https://issues.redhat.com/browse/CORENET-6871) — *Implement handling zero-worker HyperShift clusters*
- **Related design:** `agentic/design-docs/components/ovn-kubernetes.md` *(if it exists)*
- **HyperShift topology reference:** `agentic/references/hypershift-llms.txt` *(if it exists)*

---

## Validation

- [ ] CI passes with new test suite (`pkg/network/ovn_kubernetes_test.go`)
- [ ] Zero-worker topology tested in integration/e2e against a real HyperShift hosted cluster
- [ ] No regression in standard OCP cluster rollout behavior
- [ ] Jira CORENET-6871 story points added (required before moving to *In Progress/Code Review* per discussion note)