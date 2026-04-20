# Execution Plan: Add Config Override for Allow-ICMP Network Policy

**File**: `agentic/exec-plans/completed/corenet-6813-allow-icmp-netpol-config-override.md`

---

```markdown
# Execution Plan: CORENET-6813 — Add Config Override for Allow-ICMP Network Policy

**PR**: #2920  
**Jira**: CORENET-6813  
**Status**: Completed  
**Affected Components**: `bindata/network/ovn-kubernetes`, `pkg/network`  
**Total Changes**: +74 lines, 0 deletions across 3 files  

---

## Problem Statement

OVN-Kubernetes manages ICMP traffic handling through network policies. Operators
needed a mechanism to override the default `allow-icmp-network-policy` behavior
via cluster network operator (CNO) configuration, enabling per-cluster control
without modifying upstream OVN-Kubernetes directly.

---

## Solution Summary

Introduced a new configuration field in the OVN-Kubernetes network configuration
struct that maps to an environment variable injected into the OVN-Kubernetes
script library. The override propagates from the CNO config → OVN-K script
environment → runtime ICMP policy behavior.

---

## Implementation Steps

### Step 1: Expose the Config Field in the OVN-K Operator Package

**File**: `pkg/network/ovn_kubernetes.go`  
**Changes**: +11 lines  

Added handling for a new `AllowICMPNetworkPolicy` configuration override field.
The implementation reads the field from the operator's OVN-Kubernetes config
struct and, when set, appends the corresponding environment variable
(`OVN_ALLOW_ICMP_NETWORK_POLICY`) to the environment passed to the OVN-K
DaemonSet/Deployment manifests rendered from bindata.

**Pattern followed**: Mirrors the existing pattern used by other OVN-K feature
flag overrides in the same file (e.g., existing gateway-mode and IPsec overrides).

Key code location:
```
pkg/network/ovn_kubernetes.go  →  renderOVNKubernetes() or equivalent render func
```

The field is conditionally applied — if the config value is unset, no environment
variable is injected and existing default behavior is preserved.

---

### Step 2: Wire the Environment Variable into the Script Library ConfigMap

**File**: `bindata/network/ovn-kubernetes/common/008-script-lib.yaml`  
**Changes**: +8 lines  

Added `OVN_ALLOW_ICMP_NETWORK_POLICY` to the script library ConfigMap that is
sourced by OVN-K node scripts. The variable is read with a shell default
expression so it is backward-compatible when the environment variable is absent:

```yaml
# Pattern used (shell default):
OVN_ALLOW_ICMP_NETWORK_POLICY="${OVN_ALLOW_ICMP_NETWORK_POLICY:-}"
```

This configmap is mounted into OVN-K pods and sourced at runtime, making the
override available to the bash logic that governs ICMP network policy behavior.

**Key constraint**: The default value must preserve existing behavior
(empty/unset = no change to current ICMP policy handling).

---

### Step 3: Add Unit Tests

**File**: `pkg/network/ovn_kubernetes_test.go`  
**Changes**: +55 lines  

Added test coverage validating:

1. **No-op path**: When `AllowICMPNetworkPolicy` is not set in config, the
   rendered manifests do NOT contain `OVN_ALLOW_ICMP_NETWORK_POLICY` in the
   environment.

2. **Override path**: When the field is explicitly set to `true` or `false`,
   the environment variable is present in the rendered output with the correct
   value.

3. **Isolation**: Other OVN-K environment variables are unaffected by the new
   field.

Test structure follows existing table-driven patterns in `ovn_kubernetes_test.go`.

---

## Data Flow

```
CNO OperatorConfig (spec.defaultNetwork.ovnKubernetesConfig)
        │
        ▼
pkg/network/ovn_kubernetes.go
  renderOVNKubernetes()
  → reads AllowICMPNetworkPolicy field
  → conditionally sets OVN_ALLOW_ICMP_NETWORK_POLICY env var
        │
        ▼
bindata/network/ovn-kubernetes/common/008-script-lib.yaml (ConfigMap)
  → OVN_ALLOW_ICMP_NETWORK_POLICY exported to script environment
        │
        ▼
OVN-Kubernetes node pods
  → script-lib sourced at startup
  → ICMP network policy behavior governed by variable value
```

---

## Testing Approach

| Layer | File | What Is Tested |
|-------|------|----------------|
| Unit | `pkg/network/ovn_kubernetes_test.go` | Config field → env var rendering |
| Integration | Existing e2e suite (network policy tests) | Runtime ICMP policy behavior |

Unit tests are the primary validation gate for this change. The bindata YAML
change is structural and validated by the existing manifest rendering tests.

---

## Verification Steps

1. **Unit tests pass**:
   ```bash
   go test ./pkg/network/... -run TestOVNKubernetes
   ```

2. **Bindata renders cleanly** — confirm the script-lib ConfigMap YAML is valid:
   ```bash
   go generate ./bindata/...   # if applicable to repo build process
   ```

3. **Manual cluster verification** (post-deploy):
   - Set `AllowICMPNetworkPolicy` override in the cluster network config.
   - Confirm the `OVN_ALLOW_ICMP_NETWORK_POLICY` env var appears in
     OVN-K node pods (`kubectl exec ... env | grep ICMP`).
   - Confirm ICMP network policy behavior matches the configured value.

4. **Negative verification**:
   - On a cluster without the override set, confirm OVN-K pods do NOT have
     `OVN_ALLOW_ICMP_NETWORK_POLICY` in their environment (or it is empty).

---

## Rollback Plan

This change is fully backward-compatible:

- The new config field is **optional**. Existing clusters without the field set
  experience zero behavioral change.
- To roll back: revert the three files to their pre-PR state and redeploy CNO.
  OVN-K pods will restart without the environment variable.
- No CRD schema changes were made; no migration is required.

---

## Key Invariants

- **Default behavior preserved**: Absence of the config field MUST NOT alter
  existing ICMP network policy handling.
- **Single source of truth**: The override originates from CNO config only;
  no out-of-band mechanism sets this variable.
- **Script-lib backward compatibility**: The shell default in `008-script-lib.yaml`
  ensures pods function correctly even when the env var is absent from the
  container environment.

---

## Related Files

| File | Role |
|------|------|
| `pkg/network/ovn_kubernetes.go` | Config field reading and env var injection |
| `pkg/network/ovn_kubernetes_test.go` | Unit test coverage |
| `bindata/network/ovn-kubernetes/common/008-script-lib.yaml` | Runtime env var export |

---

## Decisions Made

- **No new CRD field** was added at the top-level `Network` CRD for this
  override; it lives within the existing `ovnKubernetesConfig` sub-object,
  consistent with how other OVN-K overrides are structured.
- **Conditional injection** (only inject when explicitly set) was chosen over
  always-inject-with-default to keep the rendered manifests clean and auditable.
- Tests placed in the existing `ovn_kubernetes_test.go` rather than a new file
  to stay consistent with the file-per-component test pattern in `pkg/network/`.
```