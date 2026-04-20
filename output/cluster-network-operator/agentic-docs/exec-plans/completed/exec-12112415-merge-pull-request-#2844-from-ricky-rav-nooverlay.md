# Execution Plan: OVN-Kubernetes No-Overlay Mode Support (CORENET-6100)

**File**: `agentic/exec-plans/completed/ovnk-no-overlay-mode-corenet-6100.md`

---

```markdown
# Exec Plan: OVN-Kubernetes No-Overlay Mode Support

**Feature**: Add CNO knob to deploy OVN-K with no-overlay mode enabled for the default network  
**Jira**: CORENET-6100  
**PR**: #2844 (`ricky-rav/nooverlay`)  
**Status**: Completed  
**Affected Components**: `bindata`, `manifests`, `pkg/network`, `pkg/controller`, `vendor/github.com/openshift/api`, `vendor/github.com/openshift/client-go`

---

## Problem Statement

OVN-Kubernetes supports a "no-overlay" network mode where pods use the node's network directly
instead of an overlay (GENEVE/VXLAN tunnel) network. There was no mechanism in the
Cluster Network Operator (CNO) to configure or propagate this mode. This feature adds
a user-facing API field and the operator logic to wire it through to the OVN-K deployment.

---

## Implementation Steps

### Step 1: API Extension — `openshift/api` Types

**Location**: `vendor/github.com/openshift/api/operator/v1/types_network.go`

The `OVNKubernetesConfig` struct was extended with a new field to hold no-overlay
configuration. A new `NoOverlayConfig` struct was introduced to represent the knob.

**Supporting generated artifacts updated**:
- `vendor/github.com/openshift/api/operator/v1/zz_generated.deepcopy.go` — deep-copy
  methods for the new struct
- `vendor/github.com/openshift/api/operator/v1/zz_generated.swagger_doc_generated.go` — API
  documentation strings
- `vendor/github.com/openshift/api/operator/v1/zz_generated.featuregated-crd-manifests.yaml` — feature-gate
  annotations

**New client-go apply-configuration**:
- `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/nooverlayconfig.go`
  — builder/apply-config for `NoOverlayConfig`
- `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/ovnkubernetesconfig.go`
  — updated to include `NoOverlayConfig` field
- `vendor/github.com/openshift/client-go/operator/applyconfigurations/utils.go` — utility
  registration updated
- `vendor/github.com/openshift/client-go/operator/applyconfigurations/internal/internal.go`
  — internal schema updated

---

### Step 2: CRD Manifest Updates

**Location**: `manifests/` and `vendor/github.com/openshift/api/operator/v1/zz_generated.crd-manifests/`

Five CRD variant manifests were updated to include the new `noOverlay` field schema,
one per feature-gate tier:

| Manifest | Feature Gate Tier |
|---|---|
| `manifests/0000_70_network_01_networks-Default.crd.yaml` | Default (GA) |
| `manifests/0000_70_network_01_networks-TechPreviewNoUpgrade.crd.yaml` | Tech Preview |
| `manifests/0000_70_network_01_networks-DevPreviewNoUpgrade.crd.yaml` | Dev Preview |
| `manifests/0000_70_network_01_networks-CustomNoUpgrade.crd.yaml` | Custom |
| `manifests/0000_70_network_01_networks-OKD.crd.yaml` | OKD (renamed from `0000_70_network_01_networks.crd.yaml`) |

Each manifest received ~130–143 lines of new schema additions describing `noOverlay`
and its sub-fields. The OKD manifest was also renamed to be consistent with the
tiered naming convention.

---

### Step 3: Operator Core Logic — Network Package

**Location**: `pkg/network/ovn_kubernetes.go`

This is the central implementation file. Changes include:

1. **Reading the `NoOverlay` config field** from the `OVNKubernetesConfig` in the
   operator's network configuration.

2. **Propagating the no-overlay flag** to OVN-K rendered templates. The render
   path passes the setting into the template data context so bindata templates can
   consume it.

3. **Validation logic** was added or updated to reject invalid combinations (e.g.,
   no-overlay with incompatible network topologies).

4. **`BGPManagedConfig` interaction** — the `bgpmanagedconfig.go` apply-config was
   also updated (`vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/bgpmanagedconfig.go`),
   indicating no-overlay mode is related to BGP-managed / non-encapsulated routing.

---

### Step 4: OVN-K Bindata Template Updates

**Location**: `bindata/network/ovn-kubernetes/self-hosted/`

Three manifest templates were updated to conditionally set the no-overlay mode
argument on OVN-K processes:

| Template | Purpose |
|---|---|
| `004-config.yaml` | OVN-K ConfigMap — adds no-overlay configuration knob |
| `ovnkube-control-plane.yaml` | Control-plane DaemonSet/Deployment — passes flag to ovnkube-master |
| `ovnkube-node.yaml` | Node DaemonSet — passes flag to ovnkube-node |

Each template received 1–3 new lines to conditionally inject the `--no-overlay`
flag when the feature is enabled.

---

### Step 5: Operator Config Controller

**Location**: `pkg/controller/operconfig/operconfig_controller.go`

The operator config controller was updated to handle the new field during
reconciliation. This ensures the no-overlay setting is picked up from the
`Network.operator.openshift.io` CR and forwarded to the render pipeline.

---

### Step 6: Vendor Dependency Update

**Location**: `go.mod`, `go.sum`, `vendor/modules.txt`

The `openshift/api` and `openshift/client-go` module versions were bumped to
pick up the new `NoOverlayConfig` type and related generated code. All vendored
files were updated accordingly.

**Additional `openshift/api` and `openshift/client-go` vendored updates** (unrelated
upstream changes pulled in with the version bump):
- Various `config/v1alpha1` types (ClusterMonitoring, PKI, ImagePolicy)
- `machineconfiguration/v1` types
- New `client-go` listers, informers, and clientsets for `pki` resource

---

### Step 7: Test Coverage

**Locations**:
- `pkg/network/ovn_kubernetes_test.go`
- `pkg/network/ovn_kubernetes_dpu_host_test.go`

Test changes validated:

1. **No-overlay config propagation** — unit tests assert that when `NoOverlay` is
   set in the OVNKubernetes config, the rendered bindata output contains the
   expected `--no-overlay` flag in the correct containers.

2. **Validation rejection** — tests assert that invalid configurations combining
   no-overlay with incompatible settings return appropriate errors.

3. **DPU host path** — the DPU host test file was updated to confirm no-overlay
   does not incorrectly interact with DPU-host-specific rendering paths.

---

## Architecture Decisions

| Decision | Rationale |
|---|---|
| Feature introduced in all CRD tiers including Default | No-overlay is considered stable enough for GA alongside tech-preview tiers |
| OKD manifest renamed with `-OKD` suffix | Aligns with tiered naming convention used by all other variants |
| No-overlay wired through bindata templates (not hardcoded) | Follows existing CNO pattern for conditional OVN-K flag injection |
| `BGPManagedConfig` updated alongside `NoOverlayConfig` | No-overlay mode is architecturally linked to BGP-routed (non-encapsulated) pod networking |

---

## Data Flow

```
User sets Network CR
  └─► operconfig_controller.go (reconcile)
        └─► pkg/network/ovn_kubernetes.go (renderOVNKubernetes)
              ├─► reads OVNKubernetesConfig.NoOverlay
              ├─► validates config
              └─► passes flag into bindata template context
                    ├─► bindata/.../004-config.yaml       (ConfigMap)
                    ├─► bindata/.../ovnkube-control-plane.yaml
                    └─► bindata/.../ovnkube-node.yaml
```

---

## Verification Steps

1. **Unit tests pass**:
   ```bash
   go test ./pkg/network/... -run TestOVN
   ```

2. **CRD schema validates**:
   ```bash
   oc apply --dry-run=client -f manifests/0000_70_network_01_networks-Default.crd.yaml
   ```

3. **Enable no-overlay on a test cluster**:
   ```bash
   oc patch network.operator cluster --type=merge \
     -p '{"spec":{"defaultNetwork":{"ovnKubernetesConfig":{"noOverlay":{}}}}}'
   ```

4. **Verify OVN-K pods restarted with flag**:
   ```bash
   oc -n openshift-ovn-kubernetes get pods
   oc -n openshift-ovn-kubernetes logs <ovnkube-node-pod> | grep no-overlay
   ```

5. **Verify pod networking without overlay encapsulation** — pods on different nodes
   communicate without GENEVE encapsulation visible in packet captures.

---

## Rollback Plan

1. **Revert the Network CR** field to omit `noOverlay`:
   ```bash
   oc patch network.operator cluster --type=json \
     -p '[{"op":"remove","path":"/spec/defaultNetwork/ovnKubernetesConfig/noOverlay"}]'
   ```
   CNO will re-render and restart OVN-K pods without the flag.

2. **If CRD rollback is needed** — re-apply the previous CRD manifest version from
   the prior release. The field is additive and its removal is non-breaking for
   clusters that never set it.

3. **Operator rollback** — revert the CNO image version via:
   ```bash
   oc -n openshift-network-operator set image deployment/network-operator \
     network-operator=<previous-image>
   ```

---

## Files Changed Summary

| Path | Change Type | Purpose |
|---|---|---|
| `pkg/network/ovn_kubernetes.go` | Modified | Core render/validation logic |
| `pkg/network/ovn_kubernetes_test.go` | Modified | Unit tests |
| `pkg/network/ovn_kubernetes_dpu_host_test.go` | Modified | DPU host path tests |
| `pkg/controller/operconfig/operconfig_controller.go` | Modified | Reconcile loop wiring |
| `bindata/network/ovn-kubernetes/self-hosted/004-config.yaml` | Modified | ConfigMap template |
| `bindata/network/ovn-kubernetes/self-hosted/ovnkube-control-plane.yaml` | Modified | Control-plane template |
| `bindata/network/ovn-kubernetes/self-hosted/ovnkube-node.yaml` | Modified | Node template |
| `manifests/0000_70_network_01_networks-*.crd.yaml` (5 files) | Modified/Added | CRD schema per tier |
| `vendor/github.com/openshift/api/operator/v1/types_network.go` | Modified | API type definition |
| `vendor/github.com/openshift/api/operator/v1/zz_generated.*.go` | Modified | Generated API artifacts |
| `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/nooverlayconfig.go` | Added | Apply-config builder |
| `vendor/github.com/openshift/client-go/operator/applyconfigurations/operator/v1/ovnkubernetesconfig.go` | Modified | Updated apply-config |
| `go.mod`, `go.sum`, `vendor/modules.txt` | Modified | Dependency version bump |

---

## Related

- **ADR candidate**: No-overlay mode gateway routing model vs. overlay model
- **Tech debt**: `vendor/` changes from upstream `openshift/api` bump include
  unrelated PKI/ClusterMonitoring types — these should be tracked in
  `agentic/exec-plans/tech-debt-tracker.md` as opportunistic vendoring
- **Follow-up**: E2E test coverage for no-overlay pod connectivity across nodes
```