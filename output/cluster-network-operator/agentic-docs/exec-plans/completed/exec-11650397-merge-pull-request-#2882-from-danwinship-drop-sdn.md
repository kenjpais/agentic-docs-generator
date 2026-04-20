# Execution Plan: Drop Remaining OpenShift SDN Code

**Location**: `agentic/exec-plans/completed/corenet-6417-drop-openshift-sdn.md`

---

```markdown
# CORENET-6417: Drop Remaining OpenShift SDN Code

## Metadata

| Field | Value |
|-------|-------|
| PR | #2882 (danwinship/drop-sdn) |
| Jira | CORENET-6417 |
| Status | Completed |
| Net Change | +51 / -2864 lines |
| Affected Components | `bindata/`, `pkg/network/`, `pkg/controller/`, `docs/` |

---

## Problem Statement

CNO retained dead code and YAML manifests for deploying OpenShift SDN even
though that plugin is never deployed: the operator explicitly rejects any
configuration that requests OpenShift SDN before reaching the render path.
The dead code increased binary size, maintenance burden, and cognitive load
for agents and engineers reading the codebase.

---

## Solution Summary

Remove all OpenShift SDN manifests, Go rendering logic, tests, and supporting
utilities. Update references in shared code (status manager, kube-proxy,
multus, OVN-Kubernetes, cluster config) to reflect the reduced plugin set.
Update `docs/operands.md` to stop listing SDN as a managed operand.

---

## Implementation Steps

### Step 1 — Delete All OpenShift SDN Bindata Manifests

**Files removed:**
```
bindata/network/openshift-sdn/000-ns.yaml            (-15 lines)
bindata/network/openshift-sdn/001-crd.yaml           (-377 lines)
bindata/network/openshift-sdn/002-rbac.yaml          (-75 lines)
bindata/network/openshift-sdn/003-rbac-controller.yaml (-128 lines)
bindata/network/openshift-sdn/004-multitenant.yaml   (-165 lines)
bindata/network/openshift-sdn/005-clusternetwork.yaml (-1 line)
bindata/network/openshift-sdn/006-flowschema.yaml    (-37 lines)
bindata/network/openshift-sdn/alert-rules.yaml       (-78 lines)
bindata/network/openshift-sdn/cni-features.yaml      (removed)
bindata/network/openshift-sdn/controller.yaml        (removed)
bindata/network/openshift-sdn/monitor.yaml           (removed)
bindata/network/openshift-sdn/openshift-host-network-ns.yaml (removed)
bindata/network/openshift-sdn/openshift-host-network-resourcequota.yaml (removed)
bindata/network/openshift-sdn/sdn.yaml               (removed)
```

All YAML manifests under `bindata/network/openshift-sdn/` were deleted.
These files defined the Namespace, CRDs, RBAC, FlowSchema, DaemonSets,
Deployments, alerting rules, and host-network resources previously used
to deploy the SDN plugin on cluster.

---

### Step 2 — Remove the OpenShift SDN Go Rendering Package

**File removed:**
```
pkg/network/openshift_sdn.go
pkg/network/openshift_sdn_test.go
```

`pkg/network/openshift_sdn.go` contained the `OpenShiftSDN` struct that
implemented the `Network` interface — methods for rendering manifests,
validating config, handling upgrades, and generating node config. The
entire file was deleted because the interface implementation is unreachable
(cluster-config validation rejects `NetworkTypeOpenShiftSDN` before any
render call).

The companion test file `pkg/network/openshift_sdn_test.go` was deleted
in full, removing all unit tests that exercised SDN-specific rendering
paths.

---

### Step 3 — Update the Render Dispatch Table

**File modified:** `pkg/network/render.go`

The central `Render()` function contained a dispatch table (or type-switch)
that mapped `NetworkType` values to their `Network` implementations. The
`OpenShiftSDN` case was removed from this dispatch path so the type is no
longer instantiated or called at render time.

---

### Step 4 — Update Render Tests

**File modified:** `pkg/network/render_test.go`

Test cases that exercised the SDN render path (valid SDN configs, SDN
upgrade scenarios, SDN node-config generation) were removed. Tests covering
the remaining plugins (OVN-Kubernetes, kuryr, etc.) were left intact.

---

### Step 5 — Update Cluster Config Validation

**Files modified:**
```
pkg/network/cluster_config.go
pkg/network/cluster_config_test.go
```

`cluster_config.go` contains the authoritative rejection of
`NetworkTypeOpenShiftSDN`. This validation was already present; the change
cleaned up any helper references, constants, or import-time registrations
that still mentioned SDN. The rejection logic itself was preserved — CNO
must still emit a clear error when a cluster requests SDN rather than
silently mis-configuring.

Corresponding test cases in `cluster_config_test.go` that validated SDN
config shapes were removed; test cases asserting the rejection error were
retained to ensure the guard remains functional.

---

### Step 6 — Update Kube-Proxy Rendering

**Files modified:**
```
pkg/network/kube_proxy.go
pkg/network/kube_proxy_test.go
bindata/kube-proxy/kube-proxy.yaml
```

`kube_proxy.go` previously had conditional logic that adjusted kube-proxy
configuration when running alongside OpenShift SDN (e.g., different
`--proxy-mode` or iptables settings). Those conditionals were removed; the
rendering function now only branches on OVN-Kubernetes and other remaining
plugins.

`bindata/kube-proxy/kube-proxy.yaml` received a minor adjustment (+1/-1)
to remove an SDN-specific annotation or label that was no longer applicable.

Test cases in `kube_proxy_test.go` exercising SDN-combined kube-proxy
configurations were deleted.

---

### Step 7 — Update Cloud Network Integration

**File modified:** `pkg/network/cloud_network.go`

`cloud_network.go` handles cloud-provider-specific network wiring. A
conditional block that applied cloud-network settings for SDN clusters was
removed, leaving only the OVN-Kubernetes path.

---

### Step 8 — Update Utility Package

**File modified:** `pkg/util/util.go`

Removed any SDN-specific utility functions or constants (e.g., SDN plugin
name strings, helper predicates like `IsOpenShiftSDN()`) that were no longer
referenced by any remaining code after the above deletions. This prevented
dead-export drift in the utilities package.

---

### Step 9 — Update Status Manager

**Files modified:**
```
pkg/controller/statusmanager/status_manager.go
pkg/controller/statusmanager/status_manager_test.go
```

The status manager tracks the health of CNO-managed operands. SDN-related
operand names, DaemonSet references, and Deployment references were removed
from the operand registry so the status manager no longer polls or surfaces
health for objects that do not exist.

Tests in `status_manager_test.go` that mocked SDN DaemonSet/Deployment
status were removed accordingly.

---

### Step 10 — Update Multus YAML

**File modified:** `bindata/network/multus/multus.yaml`

Multus configuration contained a reference (annotation or volume mount)
that was conditional on SDN being present. The SDN-specific stanza (-3
lines) was removed; the net-attach-def registration path for OVN-Kubernetes
is unaffected.

---

### Step 11 — Update OVN-Kubernetes Script Library

**Files modified:**
```
bindata/network/ovn-kubernetes/common/008-script-lib.yaml
bindata/network/ovn-kubernetes/self-hosted/ovnkube-control-plane.yaml
```

The OVN-Kubernetes shell script library (`008-script-lib.yaml`) contained
a compatibility shim or migration helper that handled clusters previously
running SDN. That shim was removed.

`ovnkube-control-plane.yaml` had a related annotation or init-container
condition referencing the SDN migration path; the SDN branch was deleted,
leaving the standard OVN startup sequence.

---

### Step 12 — Update Operator Documentation

**File modified:** `docs/operands.md`

`docs/operands.md` catalogs all objects that CNO owns and manages. The
OpenShift SDN section (Namespace, CRDs, DaemonSets, alerting rules, RBAC)
was removed. The file was updated to reflect only currently active operands.
Net change: +6/-8 — the additions document clarifying notes about the
remaining plugins.

---

## Testing Approach

### Unit Tests
- Deleted: all unit tests in `openshift_sdn_test.go` (SDN render paths are
  gone; tests cannot and should not be maintained for removed code).
- Deleted: SDN-specific cases in `render_test.go`, `kube_proxy_test.go`,
  `cluster_config_test.go`, `status_manager_test.go`.
- **Retained**: The `cluster_config_test.go` assertion that `NetworkTypeOpenShiftSDN`
  is rejected with an explicit error, verifying the guard remains in place.

### Integration / E2E
- No new E2E tests were added; SDN is already untestable in CI because no
  supported cluster topology uses it.
- Existing OVN-Kubernetes and kube-proxy E2E tests provide regression
  coverage for the remaining render paths.

### Build Verification
- The `bindata` embed step (go-bindata or equivalent) must succeed after
  removing the `openshift-sdn/` directory; empty directory references in
  the generator script were also cleaned up.
- `go build ./...` must complete without unused-import errors caused by
  the SDN package removal.

---

## Verification Steps

1. `go build ./...` — zero compilation errors, no orphaned imports.
2. `go test ./pkg/network/... ./pkg/controller/... ./pkg/util/...` — all
   remaining tests pass; no tests reference deleted fixtures.
3. `grep -r "openshift-sdn\|OpenShiftSDN\|NetworkTypeOpenShiftSDN" pkg/` —
   only the rejection guard in `cluster_config.go` and its test must remain;
   all rendering references must be absent.
4. `grep -r "openshift-sdn" bindata/` — zero results (entire directory is
   deleted).
5. Confirm `docs/operands.md` no longer lists SDN-specific objects.
6. Run operator locally against a test cluster with OVN-Kubernetes — cluster
   network reconciles successfully; no regressions in multus or kube-proxy.

---

## Rollback Plan

This change is a hard deletion; rollback means reverting the PR commit.

| Scenario | Action |
|----------|--------|
| Build break | `git revert <commit-sha>` and re-open PR |
| Regression in OVN-Kubernetes path | Revert; isolate which shared code change (kube-proxy, multus, OVN script lib) caused the regression |
| Missing SDN rejection guard | Cherry-pick `cluster_config.go` guard back independently |

Because OpenShift SDN is already fully rejected at config-validation time,
rolling back this PR does **not** re-enable SDN deployments — it only
restores dead code. There is no data-plane or cluster-state impact.

---

## Files Changed (Summary)

| Path | Action | Net Δ |
|------|--------|-------|
| `bindata/network/openshift-sdn/` (14 files) | **Deleted** | -976 lines |
| `pkg/network/openshift_sdn.go` | **Deleted** | ~-600 lines |
| `pkg/network/openshift_sdn_test.go` | **Deleted** | ~-400 lines |
| `pkg/network/render.go` | Modified | small |
| `pkg/network/render_test.go` | Modified | deletions |
| `pkg/network/cluster_config.go` | Modified | cleanup |
| `pkg/network/cluster_config_test.go` | Modified | deletions |
| `pkg/network/kube_proxy.go` | Modified | deletions |
| `pkg/network/kube_proxy_test.go` | Modified | deletions |
| `pkg/network/cloud_network.go` | Modified | deletions |
| `pkg/util/util.go` | Modified | deletions |
| `pkg/controller/statusmanager/status_manager.go` | Modified | deletions |
| `pkg/controller/statusmanager/status_manager_test.go` | Modified | deletions |
| `bindata/network/multus/multus.yaml` | Modified | +1/-3 |
| `bindata/kube-proxy/kube-proxy.yaml` | Modified | +1/-1 |
| `bindata/network/ovn-kubernetes/common/008-script-lib.yaml` | Modified | deletions |
| `bindata/network/ovn-kubernetes/self-hosted/ovnkube-control-plane.yaml` | Modified | deletions |
| `docs/operands.md` | Modified | +6/-8 |

**Total: +51 / -2864 lines across 31 files**

---

## Key Invariants Preserved

- `NetworkTypeOpenShiftSDN` is **still rejected** in `cluster_config.go` —
  the operator will not silently ignore an SDN request; it will error clearly.
- OVN-Kubernetes, kube-proxy, multus, and cloud-network render paths are
  **unchanged in behavior**; only SDN-conditional branches were removed.
- No API types or CRD schemas were changed — this is a purely internal
  implementation cleanup.

---

## Related

- `agentic/design-docs/components/network-plugin-lifecycle.md` — describes
  the `Network` interface that `openshift_sdn.go` formerly implemented.
- `pkg/network/cluster_config.go` — authoritative rejection guard (must not
  be removed in future cleanup passes).
- `docs/operands.md` — updated operand catalog.
```