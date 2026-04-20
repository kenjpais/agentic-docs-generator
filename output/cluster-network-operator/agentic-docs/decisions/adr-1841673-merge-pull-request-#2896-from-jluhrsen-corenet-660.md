# ADR-1841673: Fix Transient Error Conditions Causing Network Operator Degraded Blips

**File:** `agentic/decisions/adr-1841673-fix-transient-network-operator-degraded-blips.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 1841673 |
| **Jira** | CORENET-6605 |
| **Date** | 2025 |
| **Status** | Accepted |
| **Decision-Makers** | jluhrsen, network-operator team |
| **PR** | #2896 |

---

## Context

The OpenShift CI payload validation effort identified that the `clusteroperator/network` operator was intermittently blipping `Degraded=True` during serial e2e test jobs under normal (non-failure) conditions. This was observed in the `periodic-ci-openshift-release-master-ci-4.18-e2e-gcp-ovn-techpreview-serial` job.

The two root causes associated with the blip were:

- `ApplyOperatorConfig` — transient errors during operator config reconciliation
- `RolloutHung` — transient detection of a hung rollout

As a short-term workaround, an exception was added in the test suite at:
```
openshift/origin: pkg/monitortests/clusterversionoperator/legacycvomonitortests/operators.go:L105
```

The requirement per the linked effort: **teams must fix the underlying cause and remove the exception**. A `Degraded=True` blip during normal operations represents a reliability regression — HA components must not be degraded by design during e2e tests or upgrades.

---

## Decision

**Fix transient error conditions in the network-operator controllers and status manager that were incorrectly promoting short-lived, retriable errors into `Degraded=True` operator status.**

Changes were applied across 15 files (+164 / -56 lines), targeting:

| Area | Files | Change |
|---|---|---|
| Controller reconciliation error handling | `pkg/controller/clusterconfig/`, `pkg/controller/configmap_ca_injector/`, `pkg/controller/dashboards/`, `pkg/controller/egress_router/`, `pkg/controller/infrastructureconfig/`, `pkg/controller/operconfig/`, `pkg/controller/pki/`, `pkg/controller/proxyconfig/`, `pkg/controller/signer/` | Transient errors no longer surface as Degraded |
| Status manager | `pkg/controller/statusmanager/status_manager.go`, `status_manager_test.go`, `pod_status.go` | Degraded condition promotion logic tightened |
| Cluster config | `pkg/network/cluster_config.go`, `cluster_config_test.go` | Transient config-read errors handled gracefully |
| Operator cluster bootstrap | `pkg/controller/operconfig/cluster.go` | RolloutHung transient condition scoped correctly |

---

## Alternatives Considered

| Alternative | Reason Rejected |
|---|---|
| Keep the test exception permanently | Explicitly prohibited by the owning effort — exceptions are a temporary measure; teams are required to fix root causes |
| Suppress `Degraded` reporting entirely | Masks real failures; violates observability requirements for operator health |
| Rate-limit Degraded status updates | Does not fix the underlying transient error propagation; would still degrade under timing conditions |

---

## Consequences

### Positive
- Removes the CI test exception at `openshift/origin:pkg/monitortests/clusterversionoperator/legacycvomonitortests/operators.go:L105`
- `clusteroperator/network` no longer blips `Degraded=True` during normal serial e2e or upgrade runs
- Consistent with the broader HA operator reliability effort across the payload
- Status manager and controller error-handling behavior is validated by updated tests (`status_manager_test.go`, `cluster_config_test.go`)

### Negative / Trade-offs
- Error conditions that were previously surfaced immediately as `Degraded` are now treated as transient; teams must ensure the retry/backoff logic does not mask real degradations

### Risks
- If the transient classification is too broad, genuine degradation events could be suppressed. Mitigation: test coverage was updated alongside the fix.

---

## Implementation Notes

**Critical code locations:**

```
pkg/controller/statusmanager/status_manager.go       # Central Degraded condition logic
pkg/controller/statusmanager/pod_status.go           # Pod-level status aggregation
pkg/controller/operconfig/operconfig_controller.go   # Primary operator config reconciler
pkg/controller/operconfig/cluster.go                 # RolloutHung handling
pkg/network/cluster_config.go                        # Cluster config read path
```

**Verification:** The CI exception in `openshift/origin` at `operators.go:L105` should be removed once this fix is confirmed in a payload run without blips.

---

## References

- Jira: [CORENET-6605](https://issues.redhat.com/browse/CORENET-6605)
- Example failing job: `periodic-ci-openshift-release-master-ci-4.18-e2e-gcp-ovn-techpreview-serial/1843057849916198912`
- Test exception location: `openshift/origin @ pkg/monitortests/clusterversionoperator/legacycvomonitortests/operators.go:L105`
- PR: `openshift-network-operator#2896`