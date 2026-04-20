# Execution Plan: EgressIP Duplicate Mark Admission Policy

**Path**: `agentic/exec-plans/completed/ocpbugs-60670-egressip-duplicate-mark-admission-policy.md`

---

```markdown
# Exec Plan: OCPBUGS-60670 — EgressIP Duplicate Mark ValidatingAdmissionPolicy

| Field | Value |
|-------|-------|
| **Jira** | OCPBUGS-60670 |
| **PR** | #2837 (arghosh93/OCPBUGS-60670) |
| **Status** | Completed |
| **Component** | `bindata/network/ovn-kubernetes`, `pkg/network` |
| **Risk** | Low — admission policy prevents bad state; no runtime behavior change |

---

## Problem

When `ovnkube-control-plane` starts up, if two EgressIP CRs carry the same
`k8s.ovn.org/egressip-mark` annotation value, the controller enters a crash
loop:

```
E Failed while processing existing *v1.EgressIP items:
  failed to reserve mark for EgressIP <name>:
  failed to reserve mark: id 0 is already reserved by another resource
```

Root cause: the mark reservation logic is not idempotent across duplicate
annotations. The controller cannot proceed and the entire OVN control plane
becomes unavailable cluster-wide.

The origin of duplicate annotations is not fully understood, but the
**prevention** is clear: reject the creation or update of any EgressIP object
whose `egressip-mark` annotation value is already held by another EgressIP.

---

## Solution Strategy

Add a Kubernetes `ValidatingAdmissionPolicy` (VAP) that enforces uniqueness of
the `k8s.ovn.org/egressip-mark` annotation across all EgressIP objects at
admission time — before the value reaches persistent storage. This is a
zero-downtime, declarative guard with no changes to controller runtime logic.

---

## Implementation Steps

### Step 1 — Author the ValidatingAdmissionPolicy manifest

**File created**: `bindata/network/ovn-kubernetes/common/egressip-admission-policy.yaml`
**Change**: +39 lines (net-new file)

The manifest defines two Kubernetes objects deployed together:

#### 1a. `ValidatingAdmissionPolicy`

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: egressip-mark-uniqueness
```

**CEL expression logic** (encoded in `spec.validations`):

```
# For every other EgressIP in the cluster, assert that its
# egressip-mark annotation value differs from the incoming object's value.
object.metadata.annotations[?'k8s.ovn.org/egressip-mark'] == null ||
  !namespaceObject.select(eip,
    eip.metadata.name != object.metadata.name &&
    eip.metadata.annotations[?'k8s.ovn.org/egressip-mark'] ==
      object.metadata.annotations['k8s.ovn.org/egressip-mark']
  ).exists()
```

Key policy properties:
- **`matchConstraints`**: scoped to `EgressIP` resources in the
  `k8s.ovn.org` API group.
- **`failurePolicy`**: set to `Fail` — rejects the offending create/update.
- **`matchConditions`**: only fires when the annotation is present, avoiding
  false positives on EgressIP objects that carry no mark.
- **`variables`**: parameterised to avoid repetition in the CEL expression.
- **`message`**: human-readable denial message identifying the duplicate value.

#### 1b. `ValidatingAdmissionPolicyBinding`

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: egressip-mark-uniqueness-binding
spec:
  policyName: egressip-mark-uniqueness
  validationActions: [Deny]
```

Binds the policy cluster-wide with no namespace selector restrictions (EgressIP
is a cluster-scoped resource).

---

### Step 2 — Align test fixtures

**File modified**: `pkg/network/ovn_kubernetes_test.go`
**Change**: +4 -4 lines

The existing test suite validates which bindata files are rendered and applied
by the OVN-Kubernetes network operator reconciler. The new YAML file needed to
be registered in the test's expected file set so that:

1. Tests continue to pass (no "unexpected file" failures).
2. The admission policy is confirmed to be part of the OVN-Kubernetes common
   asset bundle rendered on every reconcile.

The change updated the expected asset list inside the relevant test cases to
include `bindata/network/ovn-kubernetes/common/egressip-admission-policy.yaml`.
No new test logic was written — the existing render/apply coverage is
sufficient to confirm the file is picked up by the operator.

---

## Files Changed

| File | Type | Change |
|------|------|--------|
| `bindata/network/ovn-kubernetes/common/egressip-admission-policy.yaml` | New | +39 / 0 |
| `pkg/network/ovn_kubernetes_test.go` | Modified | +4 / -4 |

---

## Data Flow After This Change

```
kubectl apply EgressIP (with mark annotation)
        │
        ▼
API Server Admission Chain
        │
        ├─► ValidatingAdmissionPolicy: egressip-mark-uniqueness
        │       CEL: is this mark value unique across all EgressIPs?
        │       ├─ YES → request proceeds → stored in etcd
        │       └─ NO  → 403 Denied (human-readable message)
        │
        ▼ (only if admitted)
ovnkube-control-plane reconciler
        │
        └─► mark reservation (guaranteed unique at this point)
```

---

## Testing Approach

### Unit / Render Tests (automated, in-PR)

- `pkg/network/ovn_kubernetes_test.go` — validates that the admission policy
  YAML is included in the rendered asset set.
- No new test functions required; the existing asset enumeration tests catch
  missing or extra files.

### Manual Integration Verification (from Jira discussion)

1. Create a fresh cluster with OVN-Kubernetes.
2. Apply two EgressIP objects with **different** `egressip-mark` values → both
   admitted, control plane stable.
3. Attempt to apply a second EgressIP with a **duplicate** mark value → API
   server returns 403 with the denial message from the CEL policy.
4. Verify `ovnkube-control-plane` does **not** crash loop.
5. (Regression) Manually annotate two existing EgressIPs with the same mark
   (simulating the pre-fix broken state), remove annotations per the
   workaround, confirm control plane recovers, then confirm the VAP prevents
   re-introduction.

---

## Verification Checklist

- [ ] `ValidatingAdmissionPolicy` object exists on cluster post-upgrade:
  ```bash
  oc get validatingadmissionpolicy egressip-mark-uniqueness
  ```
- [ ] `ValidatingAdmissionPolicyBinding` exists:
  ```bash
  oc get validatingadmissionpolicybinding egressip-mark-uniqueness-binding
  ```
- [ ] Duplicate mark creation is rejected:
  ```bash
  # Should return 403
  oc apply -f duplicate-mark-egressip.yaml
  ```
- [ ] No duplicate marks survive in the cluster:
  ```bash
  oc get egressip -A -o yaml \
    | grep egressip-mark \
    | cut -d: -f2 \
    | sort | uniq -c \
    | awk '$1 > 1'
  # Expected: no output
  ```
- [ ] `ovnkube-control-plane` pods are not crash-looping:
  ```bash
  oc get pods -n openshift-ovn-kubernetes \
    -l app=ovnkube-control-plane \
    -o wide
  ```

---

## Rollback Plan

The VAP is a cluster-scoped admission object managed by the CNO operator.

**If the policy causes unexpected denials:**

1. Identify the policy via:
   ```bash
   oc get validatingadmissionpolicy egressip-mark-uniqueness -o yaml
   ```
2. Temporarily set `failurePolicy: Ignore` (unblocks admission while
   investigating):
   ```bash
   oc patch validatingadmissionpolicy egressip-mark-uniqueness \
     --type=merge \
     -p '{"spec":{"failurePolicy":"Ignore"}}'
   ```
3. Full rollback — delete the binding first, then the policy:
   ```bash
   oc delete validatingadmissionpolicybinding egressip-mark-uniqueness-binding
   oc delete validatingadmissionpolicy egressip-mark-uniqueness
   ```
4. Revert the CNO operator image to the previous version to prevent the
   operator from re-creating the objects on next reconcile.

**Pre-existing broken state** (duplicate marks already present):
Apply the documented workaround before rolling forward again:
```bash
oc annotate egressip --all k8s.ovn.org/egressip-mark-
```

---

## Known Limitations / Tech Debt

| Item | Severity | Notes |
|------|----------|-------|
| Root cause of duplicate annotations not identified | Medium | VAP prevents new duplicates; existing duplicates require manual remediation |
| No alerting for admission denials | Low | Operators won't know a duplicate was attempted without inspecting API audit logs |
| VAP requires k8s 1.28+ (GA) | Low | All supported OCP versions at time of merge satisfy this requirement |

See `agentic/exec-plans/tech-debt-tracker.md` for tracking.

---

## Related References

- Upstream OVN-Kubernetes PR (mark reservation logic): referenced in Jira
- Workaround procedure: `oc annotate egressip --all k8s.ovn.org/egressip-mark-`
- Kubernetes VAP docs: `agentic/references/validating-admission-policy-llms.txt`
- OVN-Kubernetes component design: `agentic/design-docs/components/ovn-kubernetes.md`
```