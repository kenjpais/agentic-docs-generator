# Execution Plan: CNO Kubernetes Dependency Rebase to 1.35.0

**Location:** `agentic/exec-plans/completed/`
**File:** `agentic/exec-plans/completed/CORENET-6561-k8s-rebase-1.35.0.md`

---

```markdown
# Exec Plan: CORENET-6561 — CNO Rebase Kubernetes to 1.35.0

| Field | Value |
|-------|-------|
| PR | #2887 (internal), merged as #3574229 |
| Jira | CORENET-6561 |
| Status | Completed |
| Author | yingwang-0320 |
| Type | Dependency Rebase |
| Risk | Medium — 3,020 files changed, transitive API surface impacts |

---

## Summary

Rebased the cluster-network-operator (CNO) vendor tree to Kubernetes 1.35.0, updating
all direct and transitive dependencies. The change involved updating `go.mod`/`go.sum`,
vendoring updated upstream Kubernetes and OpenShift libraries, and adapting CNO-owned
code to consume the new APIs.

---

## Problem Statement

CNO was pinned to a Kubernetes client/API version predating 1.35.0. Running against
newer clusters risks version skew in API types, generated protobuf messages, and
feature-gate semantics. The rebase synchronizes CNO with the Kubernetes 1.35.0 release
train carried by OpenShift.

---

## Implementation Steps

### Step 1 — Update Go Module Declarations

| File | Change |
|------|--------|
| `go.mod` | Bumped `k8s.io/*`, `sigs.k8s.io/*`, `github.com/openshift/*` versions (+4 -4 lines) |
| `go.sum` | Updated checksums for new module versions (+9 -8 lines) |
| `vendor/modules.txt` | Re-pinned all vendored module metadata |

The module graph was resolved via `go mod tidy` followed by `go mod vendor` to
materialize the full vendor tree.

---

### Step 2 — Vendor Core Kubernetes Libraries

Updated the following upstream Kubernetes modules in `vendor/`:

#### `vendor/k8s.io/api/`
- All API groups (`core`, `apps`, `batch`, `certificates`, `storage`, `resource`, etc.)
  regenerated with updated protobuf message files (`generated.pb.go`,
  `generated.protomessage.pb.go`) and model-name helpers (`zz_generated.model_name.go`).
- **Notable new/graduated APIs:**
  - `k8s.io/api/storagemigration/v1beta1/` — promoted from `v1alpha1`; old `v1alpha1`
    files retained for compatibility period.
  - `k8s.io/api/resource/v1/` — new stable DRA (Dynamic Resource Allocation) types.
  - `k8s.io/api/scheduling/v1alpha1/` — new `Workload` type added.
  - `k8s.io/api/certificates/v1beta1/` — `PodCertificateRequest` moved from v1alpha1.

#### `vendor/k8s.io/apimachinery/`
- Updated `labels/selector.go`, `sets/set.go`, `util/diff/`, `util/validation/`
- New `api/validate/` package added: content validators for DNS, paths, identifiers,
  decimals and structured field validation helpers.

#### `vendor/k8s.io/apiserver/`
- `pkg/endpoints/filters/impersonation/` — impersonation handler extracted into a
  dedicated sub-package (`cache.go`, `constrained_impersonation.go`, `mode.go`);
  original `impersonation.go` moved there.
- `pkg/server/flagz/` — new flagz endpoint implementation added (API types, registry,
  serializer, negotiation).
- `pkg/server/statusz/` — new statusz endpoint implementation added (mirroring flagz
  structure).
- `pkg/storage/etcd3/stats.go` — new etcd storage statistics file.
- `pkg/storage/etcd3/metrics/` — OWNERS file added.
- `pkg/cel/`, `pkg/admission/plugin/` — CEL library and admission plugin updates
  tracking upstream k8s 1.35 feature set.

#### `vendor/k8s.io/client-go/`
- `applyconfigurations/` — regenerated for all API groups including new `v1beta1`
  storagemigration and `v1alpha1` scheduling workload types.
- `informers/` — updated informer factories for new/graduated resources.
- `kubernetes/` clientset updated: `storagemigration/v1beta1`, `scheduling/v1alpha1`
  (Workload), `certificates/v1beta1` (PodCertificateRequest).
- `listers/` — updated listers parallel to informer changes.
- `tools/cache/` — `the_real_fifo.go` introduced as new queue backing.

#### `vendor/k8s.io/component-base/`
- `compatibility/` — new registry file + OWNERS.
- `zpages/` — `flagz/`, `statusz/`, `httputil/` added as zpages infrastructure.
  Content moved from component-base into `apiserver/pkg/server/flagz|statusz`.

---

### Step 3 — Vendor OpenShift Libraries

#### `vendor/github.com/openshift/api/`
- Updated to pick up new CRD manifests and types:
  - `etcd/v1alpha1/` — new `PacemakerCluster` type added.
  - `operator/v1alpha1/` — new `ClusterAPI` installer types.
  - `config/v1alpha1/` — new `CRIOCredentialProviderConfig` type.
  - `features/` — updated feature gate lists (`features.go`, `legacyfeaturegates.go`).
  - Multiple CRD manifests regenerated under `operator/v1/zz_generated.crd-manifests/`.
- `vendor/github.com/openshift/api/Makefile` — bumped generator version.

#### `vendor/github.com/openshift/client-go/`
- Regenerated apply-configurations for all config and operator API groups.
- New client surfaces for `operator/v1alpha1/ClusterAPI` and
  `config/v1alpha1/CRIOCredentialProviderConfig`.
- Factory/generic informer registrations updated for new resource types.

#### `vendor/github.com/openshift/library-go/`
- `pkg/crypto/crypto.go` — minor update.

---

### Step 4 — Vendor Third-Party Libraries

| Library | Change |
|---------|--------|
| `github.com/go-openapi/jsonpointer` | Updated; NOTICE added, LICENSE updated |
| `github.com/go-openapi/jsonreference` | Updated; NOTICE/editorconfig added |
| `github.com/go-openapi/swag` | Major restructure: split into sub-packages (`conv/`, `fileutils/`, `jsonname/`, `jsonutils/`, `loading/`, `mangling/`, `netutils/`, `stringutils/`, `typeutils/`, `yamlutils/`) with interface files |
| `github.com/stoewer/go-strcase` | LICENSE removed (changed upstream); updated |
| `github.com/google/cel-go` | Updated CEL evaluator, type system, and extensions |
| `github.com/grpc-ecosystem/grpc-gateway/v2` | Updated handler and mux |
| `google.golang.org/grpc` | Updated transport, balancer, encoding, stats layers |
| `google.golang.org/protobuf` | Updated reflection and codec |
| `go.opentelemetry.io/otel` | Updated to newer version; semconv `v1.39.0` added; moved internal `env` package |
| `golang.org/x/net` | HTTP/2 transport updates, HTML iter support |
| `golang.org/x/sys` | CPU feature detection, syscall updates |
| `golang.org/x/text` | Unicode tables updated to Unicode 17.0.0 |
| `golang.org/x/tools` | AST inspector cursor, stdlib manifest, typesinternal updates |
| `github.com/prometheus/procfs` | CPU info, proc maps, smaps, vm updates |
| `github.com/sirupsen/logrus` | Terminal check files, formatter updates |
| `github.com/spf13/cobra` | Command updates |
| `github.com/onsi/gomega` | Matcher updates |
| `go.uber.org/zap` | Logger, field, and core updates |
| `go.etcd.io/etcd/api/v3` | Version bump |
| `sigs.k8s.io/controller-runtime` | Cache, client, webhook, conversion, controller updates |
| `sigs.k8s.io/controller-tools` | CRD, deepcopy, marker, schema updates |
| `sigs.k8s.io/structured-merge-diff/v6` | Schema elements, typed remove |

---

### Step 5 — Update CNO-Owned Code

Only a small number of CNO-owned files required changes:

| File | Change |
|------|--------|
| `pkg/client/fake/fake_client.go` | Adapted to updated `sigs.k8s.io/controller-runtime` fake client API |
| `pkg/controller/infrastructureconfig/sync_vips.go` | Updated import path for infrastructure config types |
| `manifests/0000_70_cluster-network-operator_01_pki_crd.yaml` | CRD schema regenerated |
| `manifests/0000_70_network_01_networks.crd.yaml` | CRD schema regenerated |

---

### Step 6 — Update CI / Build Configuration

| File | Change |
|------|--------|
| `Dockerfile` | Base image/builder version bump |
| `.github/workflows/*.yml` (10 files) | Workflow toolchain version updates |
| `vendor/k8s.io/code-generator/kube_codegen.sh` | Generator script updated |
| Various `Makefile` files in vendor | Version pin updates |

---

## API Changes Consumed (Kubernetes 1.35.0)

| API | Direction |
|-----|-----------|
| `storagemigration/v1beta1` | Graduated from v1alpha1 |
| `resource/v1` (DRA) | New stable version |
| `certificates/v1beta1/PodCertificateRequest` | Moved from v1alpha1 |
| `scheduling/v1alpha1/Workload` | New type |
| `apiserver/flagz` and `statusz` endpoints | New server infrastructure |
| `apiserver/filters/impersonation` | Refactored into sub-package |
| `component-base/compatibility` | New registry |
| `openshift/api/etcd/v1alpha1/PacemakerCluster` | New type |
| `openshift/api/operator/v1alpha1/ClusterAPI` | New type |
| `openshift/api/config/v1alpha1/CRIOCredentialProviderConfig` | New type |

---

## Testing Approach

### Unit Tests
- `pkg/client/fake/` — fake client must pass existing unit tests with updated
  controller-runtime fake client API.
- `pkg/controller/infrastructureconfig/` — sync_vips tests validate infrastructure
  config type consumption.

### Integration / E2E Tests
- CNO CI pipelines run full cluster installation tests against the target OCP version.
- VIP sync, PKI management, and network operator reconciliation loops are covered by
  existing e2e test suites.

### Vendor Consistency
```
go mod verify
go build ./...
go vet ./...
```

---

## Verification Steps

1. **Build succeeds:** `make build` produces a valid CNO binary.
2. **Unit tests pass:** `make test` runs without failures.
3. **Vendor consistency:** `go mod verify` reports no tampered modules.
4. **CRD schema integrity:** Manifests in `manifests/` match the updated API types.
5. **CI green:** All OpenShift CI jobs (unit, integration, e2e) pass on the PR.
6. **No import cycle regressions:** `go build ./...` completes without cycle errors.

---

## Rollback Plan

1. Revert the PR (git revert or reopen previous base branch).
2. Restore `go.mod` and `go.sum` to pre-rebase versions.
3. Re-run `go mod vendor` to restore the old vendor tree.
4. The two CNO-owned files (`fake_client.go`, `sync_vips.go`) need manual revert to
   their pre-rebase import paths.
5. Restore `manifests/` CRD YAML files from the previous commit.

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| API type incompatibility at runtime | Medium | Validated by CI e2e against target OCP |
| Generated code drift | Low | go.mod pin + vendor lock |
| New API feature gates not enabled | Low | Feature gates carried by openshift/api features.go |
| Third-party library behavior change | Low | Unit tests cover all exercised code paths |
| storagemigration v1alpha1 → v1beta1 transition | Medium | Both versions vendored; CNO uses client-go which handles both |

---

## Critical Code Locations

| Purpose | Path |
|---------|------|
| CNO fake client (updated) | `pkg/client/fake/fake_client.go` |
| VIP sync controller (updated) | `pkg/controller/infrastructureconfig/sync_vips.go` |
| Module declarations | `go.mod`, `go.sum` |
| CRD manifests | `manifests/0000_70_*.yaml` |
| K8s API types | `vendor/k8s.io/api/` |
| K8s apimachinery | `vendor/k8s.io/apimachinery/` |
| K8s apiserver | `vendor/k8s.io/apiserver/` |
| K8s client-go | `vendor/k8s.io/client-go/` |
| OpenShift API | `vendor/github.com/openshift/api/` |
| OpenShift client-go | `vendor/github.com/openshift/client-go/` |
| controller-runtime | `vendor/sigs.k8s.io/controller-runtime/` |
| Vendor manifest | `vendor/modules.txt` |
```