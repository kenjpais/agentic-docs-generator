# ADR-2882: Drop OpenShift SDN Dead Code from CNO

**File location:** `agentic/decisions/adr-2882-drop-openshift-sdn.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 2882 |
| **Date** | 2025 |
| **Status** | Accepted |
| **Jira** | CORENET-6417 |
| **PR** | #2882 |
| **Decision-Makers** | danwinship, CNO maintainers |
| **Affected Components** | `pkg/network/`, `bindata/network/openshift-sdn/`, `pkg/controller/statusmanager/` |

---

## Context

CNO (Cluster Network Operator) retained a full deployment codepath for OpenShift SDN — including YAML manifests, RBAC definitions, CRDs, alert rules, and Go controller logic — despite OpenShift SDN being **actively rejected** at the configuration validation layer. Any cluster attempting to request OpenShift SDN as its network type receives an explicit rejection before the deployment path is ever reached.

This created a growing body of dead code:

- **16 YAML bindata files** under `bindata/network/openshift-sdn/` (namespace, CRDs, RBAC, multitenant, flowschema, alert rules, CNI features, controllers, monitors, SDN manifests)
- **Go source files** implementing the SDN network plugin: `pkg/network/openshift_sdn.go`, `pkg/network/openshift_sdn_test.go`
- **Supporting logic** in `pkg/network/render.go`, `pkg/network/cluster_config.go`, `pkg/network/kube_proxy.go`, `pkg/network/cloud_network.go`, and `pkg/util/util.go`
- **Status manager references** in `pkg/controller/statusmanager/status_manager.go`

The dead code carried real costs:
- Maintenance burden: changes to shared interfaces required updating SDN code paths that are never executed
- Security surface: unmaintained manifests (RBAC, CRDs) represent latent risk
- Cognitive load: agents and engineers must reason about code paths that cannot be reached
- Binary/image size: bindata embeds all YAML at compile time regardless of reachability

---

## Decision

**Remove all OpenShift SDN deployment code and templates from CNO.**

The explicit configuration rejection (already in place) is the enforcement boundary. No cluster can reach the SDN deployment path; therefore the deployment code itself provides zero value and should be deleted.

Scope of removal:

| Area | Action |
|---|---|
| `bindata/network/openshift-sdn/` | Delete all 16 manifest files |
| `pkg/network/openshift_sdn.go` | Delete |
| `pkg/network/openshift_sdn_test.go` | Delete |
| `pkg/network/render.go` | Remove SDN render branch |
| `pkg/network/cluster_config.go` | Remove SDN config handling |
| `pkg/network/kube_proxy.go` | Remove SDN-conditional kube-proxy logic |
| `pkg/network/cloud_network.go` | Remove SDN references |
| `pkg/util/util.go` | Remove SDN utility references |
| `pkg/controller/statusmanager/status_manager.go` | Remove SDN status tracking |
| `docs/operands.md` | Remove OpenShift SDN operand entry |
| `bindata/network/ovn-kubernetes/` (2 files) | Remove SDN-conditional sections |
| `bindata/kube-proxy/kube-proxy.yaml` | Remove SDN-conditional section |
| `bindata/network/multus/multus.yaml` | Remove SDN-conditional section |

Net change: **−1,225 lines of Go**, **−1,631 lines of YAML**.

---

## Alternatives Considered

### 1. Keep code, add build tag to exclude from compilation
- **Rejected**: Does not reduce cognitive load or maintenance burden. Bindata embedding still compiles YAML. The rejection layer is already the canonical enforcement point — parallel enforcement via build tags adds complexity without benefit.

### 2. Deprecation period / soft removal
- **Rejected**: OpenShift SDN is already hard-rejected at configuration time. There is no user-facing migration path to protect; the deployment code is already unreachable. A deprecation period for dead code provides no value.

### 3. Keep YAML manifests, remove Go code only
- **Rejected**: Orphaned YAML manifests in `bindata/` are still embedded in the binary and still require review during security audits. Partial removal is harder to reason about than complete removal.

---

## Consequences

### Positive

- **Reduced attack surface**: RBAC, CRD, and FlowSchema manifests for OpenShift SDN are no longer present in the operator binary or cluster
- **Lower maintenance cost**: Shared interface changes (e.g., `NetworkPlugin` interface) no longer require SDN stub updates
- **Smaller binary**: ~1,631 fewer lines of embedded YAML removed from bindata compilation
- **Cleaner render path**: `pkg/network/render.go` dispatch table loses a dead branch; control flow is simpler
- **Documentation accuracy**: `docs/operands.md` no longer lists a non-functional operand

### Negative / Risks

- **Irreversible without history**: If OpenShift SDN support is ever re-introduced (considered extremely unlikely), this code must be reconstructed from git history
- **Test coverage delta**: Deletion of `openshift_sdn_test.go` removes test lines; coverage tooling should not regress on this as a false negative

### Neutral

- The configuration rejection layer (`NetworkType: OpenShiftSDN` → explicit error) is **unchanged**. User-facing behavior is identical.
- OVN-Kubernetes and other supported plugins are unaffected except where SDN-conditional sections in shared manifests (`multus.yaml`, `kube-proxy.yaml`, `ovnkube-control-plane.yaml`, `008-script-lib.yaml`) are cleaned up.

---

## Enforcement

The removal is self-enforcing: once deleted, the code cannot be accidentally re-introduced without a deliberate PR. The existing configuration validation rejection (not modified by this PR) continues to be the architectural boundary for OpenShift SDN support.

**CI gates that validate this decision holds:**
- Compilation: `pkg/network/openshift_sdn.go` no longer exists; any re-introduction breaks the build unless re-integrated with the render dispatch table
- Unit tests: `openshift_sdn_test.go` deleted; no orphaned test references remain

---

## Related

| Reference | Location |
|---|---|
| Network plugin architecture | `pkg/network/render.go` |
| Operands documentation | `docs/operands.md` |
| OVN-Kubernetes self-hosted config | `bindata/network/ovn-kubernetes/self-hosted/ovnkube-control-plane.yaml` |
| Jira epic | CORENET-6417 |