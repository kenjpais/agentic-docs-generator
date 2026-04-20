# ADR-3574229: Rebase Cluster Network Operator (CNO) Kubernetes Dependencies to 1.35.0

**File location:** `agentic/decisions/adr-3574229-cno-rebase-k8s-1.35.0.md`

---

## Metadata

| Field | Value |
|---|---|
| **ADR Number** | 3574229 |
| **Jira** | CORENET-6561 |
| **Date** | 2025 |
| **Status** | Accepted |
| **Decision-makers** | CNO maintainers (yingwang-0320) |
| **PR** | #3574229 |

---

## Context

The Cluster Network Operator (CNO) vendors Kubernetes client libraries and associated ecosystem dependencies. These must be periodically rebased to align with the Kubernetes release train that OpenShift targets. This rebase moves CNO from a prior Kubernetes version to **k8s.io 1.35.0**.

Staying current with the upstream Kubernetes API machinery is a hard operational requirement: OpenShift API types, admission webhooks, storage backends, and controller-runtime all depend on a coherent, version-matched set of k8s.io libraries. Falling behind causes API incompatibilities with the cluster control plane and blocks feature adoption.

**Scope of change (from PR diff):**
- `go.mod` / `go.sum`: 4 dependency version changes
- `vendor/`: 3,010 files modified across `k8s.io/*`, `github.com/openshift/*`, `go.opentelemetry.io/*`, `google.golang.org/grpc`, `github.com/google/cel-go`, and others
- `manifests/`: 2 CRD YAML files updated
- `pkg/`: 2 production Go files updated (`fake_client.go`, `sync_vips.go`)

---

## Decision

**Rebase all vendored `k8s.io/*` and dependent ecosystem libraries to the versions compatible with Kubernetes 1.35.0.**

Key library changes included in this rebase:

| Library | Change Type |
|---|---|
| `k8s.io/api`, `k8s.io/apimachinery`, `k8s.io/client-go` | Kubernetes 1.35.0 release |
| `k8s.io/apiserver` | Updated (flagz/statusz endpoints moved; impersonation refactored) |
| `k8s.io/component-base` | Updated (compatibility registry, zpages) |
| `github.com/openshift/api` | Updated (new: `etcd/v1alpha1`, `config/v1alpha2`, `operator/v1alpha1/clusterapi`) |
| `github.com/openshift/client-go` | Updated (new: CrioCredentialProviderConfig, ClusterAPI informers/listers) |
| `go.opentelemetry.io/otel` | Updated (semconv v1.39.0 added; v1.37.0 retained) |
| `google.golang.org/grpc` | Updated |
| `github.com/google/cel-go` | Updated (CEL environment/optimizer changes) |
| `sigs.k8s.io/controller-runtime` | Updated (conversion registry refactored, hub-spoke split) |

**Notable structural changes vendored:**

1. **`k8s.io/apiserver` impersonation refactor**: `pkg/endpoints/filters/impersonation/` is now a sub-package (`constrained_impersonation.go`, `cache.go`, `mode.go`). Previous `impersonation.go` moved from `filters/` to `filters/impersonation/`.

2. **`k8s.io/api/storagemigration`**: `v1alpha1` promoted to `v1beta1` with full file renames (`register.go`, `types.go`, `zz_generated.*`).

3. **`k8s.io/client-go` certificates**: `PodCertificateRequest` moved from `v1alpha1` to `v1beta1`.

4. **`k8s.io/apiserver` flagz/statusz**: Moved from `k8s.io/component-base/zpages` into `k8s.io/apiserver/pkg/server/flagz` and `statusz` with new typed API (`v1alpha1` types, `zz_generated.model_name.go`).

5. **`sigs.k8s.io/controller-runtime` webhook conversion**: Split into `conversion_hubspoke.go`, `conversion_registry.go`, `decoder.go` from a single file.

6. **`github.com/openshift/api`**: Added `etcd/v1alpha1` package (`PacemakerCluster` type), `config/v1alpha2` (`InsightsDataGather`), and `operator/v1alpha1/ClusterAPI`.

---

## Rationale

| Option | Assessment |
|---|---|
| **Rebase to k8s 1.35.0 (chosen)** | Required to ship on OCP release that targets k8s 1.35. Keeps CNO API-compatible with control plane. |
| Stay on prior k8s version | Blocks OCP release. API incompatibilities with 1.35 control plane would cause runtime failures. |
| Partial rebase (selective deps) | Not viable: `k8s.io/*` libraries are tightly coupled; partial updates cause type mismatch compile errors. |

The rebase is mechanical and non-discretionary for an OpenShift z-stream/minor release targeting Kubernetes 1.35.0.

---

## Consequences

### Positive
- CNO is compatible with the Kubernetes 1.35.0 API server running in the target OCP release.
- New OpenShift API types (`etcd/v1alpha1`, `config/v1alpha2`, `operator/v1alpha1/ClusterAPI`) available for future feature work.
- Updated OTel semconv (v1.39.0) and gRPC keep observability stack current.

### Negative / Risk
- **3,010 vendored files changed**: large diff surface area; any upstream bug introduced in this range of k8s.io versions is now present.
- **API promotions** (`storagemigration/v1alpha1→v1beta1`, `certificates PodCertificateRequest v1alpha1→v1beta1`) may require downstream consumer updates if CNO code references these types directly.
- **`k8s.io/apiserver` impersonation refactor**: any CNO code importing `filters.impersonation` directly must be updated to the new package path.

### Files requiring attention post-merge

| File | Reason |
|---|---|
| `pkg/client/fake/fake_client.go` | Updated for controller-runtime API changes |
| `pkg/controller/infrastructureconfig/sync_vips.go` | Updated for k8s API changes |
| `manifests/0000_70_cluster-network-operator_01_pki_crd.yaml` | CRD schema updated |
| `manifests/0000_70_network_01_networks.crd.yaml` | CRD schema updated |

---

## Alternatives Considered

None viable. Kubernetes library rebases in CNO are not architecturally optional; they are release-gated synchronization points with the OpenShift control plane version.

---

## References

- Jira: [CORENET-6561](https://issues.redhat.com/browse/CORENET-6561)
- PR: #3574229 (`yingwang-0320/CORENET-6561-rebase`)
- Upstream: `k8s.io` 1.35.0 release
- Related manifests: `manifests/0000_70_cluster-network-operator_01_pki_crd.yaml`, `manifests/0000_70_network_01_networks.crd.yaml`
- Production code changed: `pkg/client/fake/fake_client.go`, `pkg/controller/infrastructureconfig/sync_vips.go`