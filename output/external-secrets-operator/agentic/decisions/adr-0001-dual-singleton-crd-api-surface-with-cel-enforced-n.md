---
id: ADR-0001
title: "Dual Singleton CRD API Surface with CEL-Enforced Name Constraint"
date: 2025-10-06
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [api/v1alpha1, pkg/controller]
jira: ESO-101

enhancement-refs:
  - repo: "openshift/enhancements"
    number: 1835
    title: "ESO-101: Revisits and restructures external-secrets-operator APIs for GA"
supersedes: ""
superseded-by: ""
---

# Dual Singleton CRD API Surface with CEL-Enforced Name Constraint

## Executive Summary
The operator exposes two cluster-scoped singleton CRDs — `ExternalSecretsConfig` and `ExternalSecretsManager` — each enforced to a single instance via CEL validation requiring `metadata.name == 'cluster'`. This separation divides operator-level global configuration from operand deployment configuration, and was formalized as part of the GA API revision (ESO-101) to eliminate ambiguity, reduce user confusion with upstream CRD names, and produce a well-defined, unambiguous desired-state surface.

## What
- `api/v1alpha1/external_secrets_config_types.go`: defines `ExternalSecretsConfig`, a cluster-scoped singleton describing *what* the external-secrets operand deployment should look like (app config, plugins, cert providers, network policies, component-level overrides).
- `api/v1alpha1/external_secrets_manager_types.go`: defines `ExternalSecretsManager`, a cluster-scoped singleton describing *how the operator itself* behaves globally (global labels, common configs, per-controller status roll-up).
- `pkg/controller/common/constants.go`: declares `ExternalSecretsConfigObjectName = "cluster"` and `ExternalSecretsManagerObjectName = "cluster"`, the single authoritative names controllers use when fetching either object.

## Why
Without a singleton constraint, multiple instances of either CRD would create conflicting desired states with no defined reconciliation winner. The CEL rule `self.metadata.name == 'cluster'` enforces this at admission time, making the constraint part of the API contract rather than a fragile runtime check. Additionally, the rename from `externalsecrets.operator.openshift.io` to `externalsecretsconfigs.operator.openshift.io` was driven by user-reported confusion with the upstream `externalsecrets.external-secrets.io` CRD — a naming collision that made `kubectl get externalsecrets` ambiguous in clusters running both.

## Goals
- Prevent multiple CRD instances that would produce undefined or conflicting reconciliation behavior.
- Separate operator-level global config (`ExternalSecretsManager`) from operand deployment config (`ExternalSecretsConfig`) for independent lifecycle management.
- Eliminate naming confusion with upstream external-secrets CRDs.
- Make singleton invariants enforceable at API admission time via CEL, not controller logic.
- Provide a stable, well-typed API surface for GA that controllers can rely on via the hardcoded constant `"cluster"`.

## Non-Goals
- Multi-tenancy or per-namespace operand instances are not addressed by this design.
- `ExternalSecretsManager` auto-creation logic (noted as automatic during install) is not defined within these type files.
- Migration from the previous `externalsecrets.operator.openshift.io` TP API is out of scope here.

## How
Both types carry the kubebuilder marker `+genclient:nonNamespaced` and `scope=Cluster`, making them cluster-scoped resources with no namespace qualifier. The CEL constraint is applied at the type level via `+kubebuilder:validation:XValidation:rule="self.metadata.name == 'cluster'"`, which compiles into the CRD's `x-kubernetes-validations` array in the generated manifest, enforced by the API server's admission webhook before any controller sees the object.

Controllers retrieve either singleton by name using the constants `ExternalSecretsConfigObjectName` and `ExternalSecretsManagerObjectName` from `pkg/controller/common/constants.go`, both equal to `"cluster"`. This eliminates any list-and-select logic; a `Get("cluster")` call is the canonical access pattern.

`ExternalSecretsConfig.Spec` contains three sub-structs: `ApplicationConfig` (operand tuning, operating namespace restriction, webhook config), `PluginsConfig` (Bitwarden provider), and `ControllerConfig` (labels, annotations, network policies, per-component deployment overrides). A cross-field CEL rule on `ExternalSecretsConfigSpec` enforces that Bitwarden plugin enablement requires either a `secretRef` or cert-manager configuration, keeping complex invariants in the API layer.

`ExternalSecretsManager.Spec` contains only `GlobalConfig` (common configs and global labels). Its `Status` uses a `ControllerStatuses` list keyed by controller name to aggregate health across multiple operator controllers into one observable object.

## Alternatives
**Namespace-scoped CRDs with a convention-based singleton**: Would allow `kubectl get` scoping but offers no enforcement of the singleton property and complicates cluster-admin RBAC. Rejected because enforcement would fall to controller logic, not the API server.

**Single unified CRD**: Merging `ExternalSecretsManager` and `ExternalSecretsConfig` into one type would reduce the API surface but couple operator-level global settings to operand deployment config, making independent versioning and ownership harder and bloating the spec for users who only need one concern.

**Admission webhook for name enforcement**: A validating webhook could enforce `name == 'cluster'` but adds an operational dependency on the webhook being available at install time. CEL runs natively in the API server without additional infrastructure.

**Operator-managed default instance only (no user-facing CRD)**: The operator could manage operand state internally without exposing CRDs, but this eliminates GitOps declarative control and observability via `kubectl`.

## Risks
- **CEL on `metadata.name` at type root**: CEL rules on the root object (not a field) are evaluated during admission; any API server version that does not support `x-kubernetes-validations` at the object root would silently ignore the constraint, allowing duplicate instances. This is a concern only on older clusters.
- **Two-object mental model**: Operators must understand which singleton to edit for which concern; misconfiguration of `ExternalSecretsManager.GlobalConfig` versus `ExternalSecretsConfig.ControllerConfig.Labels` could produce surprising label merge behavior.
- **Hardcoded constant coupling**: Both controller and API agree on `"cluster"` via a shared constant, but any future need for multiple instances (e.g., hosted-control-plane scenarios) would require a breaking API change rather than a config update.
- **Auto-creation of `ExternalSecretsManager`**: If the operator creates this object on install and a user deletes it, reconciliation behavior is undefined without explicit documentation of the recovery path.
