---
id: ADR-0006
title: "OpenShift-Native Security: SCC Management and OpenShift CA Integration"
date: 2025-05-26
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [cmd/zero-trust-workload-identity-manager, pkg/controller]
jira: SPIRE-28

enhancement-refs:
  - repo: "openshift/enhancements"
    number: 1775
    title: "SPIRE-26: Proposal for zero trust workload identity manager"
supersedes: ""
superseded-by: ""
---

# OpenShift-Native Security: Dynamic SCC Management and CA Integration

## Executive Summary
The operator dynamically reconciles SecurityContextConstraints for both the SPIRE Agent and SPIFFE CSI Driver components, treating SCCs as first-class managed resources rather than static installation artifacts. It integrates with OpenShift's service CA for metrics authentication and provides configurable kubelet TLS verification with OpenShift-specific defaults. This approach ensures security posture is continuously enforced and survives drift, at the cost of elevated operator RBAC privileges and platform lock-in.

## What
- `pkg/controller/spire-agent/controller.go`: `SpireAgentReconciler.reconcileSCC` actively creates/updates the SCC granting `hostPID` and `hostNetwork` access required by SPIRE Agent.
- `pkg/controller/spiffe-csi-driver/controller.go`: `SpiffeCsiReconciler.reconcileSCC` manages the SCC for CSI Driver mount propagation requirements.
- Both controllers register `securityv1.SecurityContextConstraints` watches in `SetupWithManager`, triggering reconciliation on SCC drift.
- `pkg/controller/spire-agent/configmap.go`: `configureKubeletVerification` selects between `skip`, `hostCert`, and `auto` (defaulting to `/etc/kubernetes/kubelet-ca.crt`) TLS modes for the workload attestor.
- `cmd/zero-trust-workload-identity-manager/main.go`: Loads `/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt` into the metrics server's `ClientCAs` pool for mTLS client verification.

## Why
SPIRE Agent requires `hostPID` and `hostNetwork` to attest workloads and communicate with the kubelet. The SPIFFE CSI Driver requires privileged volume mount propagation. OpenShift's default-deny SCC policy blocks both unless explicit SCCs are granted. Static manifests applied at install time are vulnerable to accidental deletion or manual modification by cluster administrators. Without active reconciliation, a deleted SCC causes immediate workload identity failures with no automated recovery. The OpenShift service CA integration is required because Prometheus scraping in OpenShift uses mTLS with the cluster's internal CA, not public CAs.

## Goals
- Continuously enforce required SCCs for SPIRE Agent and SPIFFE CSI Driver; auto-recover from drift or deletion.
- Prevent SCC changes from silently breaking workload attestation by surfacing `SecurityContextConstraintsAvailable` status conditions.
- Support configurable kubelet TLS verification modes without requiring operator restarts.
- Authenticate metrics consumers using OpenShift's service CA rather than self-signed or public certificates.

## Non-Goals
- Managing SCCs for workloads other than SPIRE Agent and SPIFFE CSI Driver.
- Providing a generic SCC management framework for other operators.
- Supporting non-OpenShift Kubernetes distributions (this design explicitly requires `securityv1` APIs).
- Rotating the OpenShift service CA certificate (delegated to OpenShift's cert rotation machinery).

## How
**SCC Reconciliation Loop:**
Both `SpireAgentReconciler` and `SpiffeCsiReconciler` call `reconcileSCC` as a named step in their main `Reconcile` methods, positioned after static resources (ServiceAccount, RBAC) but before DaemonSet reconciliation. The `SetupWithManager` methods in both controllers register `securityv1.SecurityContextConstraints` as a watched resource via `handler.EnqueueRequestsFromMapFunc`, filtered by `utils.ControllerManagedResourcesForComponent` predicates. Any external modification or deletion of the SCC re-triggers full reconciliation and repairs the SCC before the DaemonSet state is re-evaluated. Status is reported through the `SecurityContextConstraintsAvailable` condition constant defined in both controllers.

**Kubelet TLS Verification (`configmap.go`):**
`configureKubeletVerification` maps the `v1alpha1.WorkloadAttestorsVerification.Type` field to SPIRE's `skip_kubelet_verification` and `kubelet_ca_path` plugin options. The `auto` mode falls back to `path.Join(utils.DefaultKubeletCABasePath, utils.DefaultKubeletCAFileName)`, which resolves to `/etc/kubernetes/kubelet-ca.crt` — the standard OpenShift kubelet CA path. This is injected into the `agent.conf` ConfigMap consumed by SPIRE Agent, and a hash of the config (`spireAgentDaemonSetSpireAgentConfigHashAnnotationKey`) is propagated to the DaemonSet annotation to force pod rotation on config change.

**Metrics CA Integration (`main.go`):**
The `openshiftCACertificateFile` constant (`/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt`) is read at startup and appended to the system cert pool. This pool is set as `tls.Config.ClientCAs` on the metrics server, enabling the OpenShift monitoring stack to present its service-CA-signed certificate for mTLS. The `filters.WithAuthenticationAndAuthorization` filter provider additionally enforces RBAC on metrics access.

## Alternatives

**Static SCC manifests applied at install time:** Standard for many operators but provides no drift recovery. A cluster admin deleting the SCC would break attestation with no automated repair. Rejected because zero-trust workload identity is a security primitive — silent failure is unacceptable.

**OLM-managed SCC via operator bundle:** OLM can install SCCs as bundle objects, but OLM does not continuously reconcile them; post-install drift is not remediated. Rejected for the same drift-recovery reason.

**Using Pod Security Admission instead of SCCs:** PSA is the upstream Kubernetes mechanism but lacks the fine-grained per-ServiceAccount binding model that SCCs provide. OpenShift's SCC system is the enforced mechanism and cannot be bypassed. Not a viable alternative on OpenShift.

**Self-signed certificates for metrics:** The operator could generate its own CA, but this requires certificate lifecycle management and does not integrate with OpenShift's built-in monitoring stack trust chain. Rejected because the service CA is automatically rotated and trusted by in-cluster consumers.

## Risks

- **Elevated operator RBAC:** The operator must hold `create/update/delete` on `securityconstraintscontexts` cluster-wide. Compromise of the operator pod could allow privilege escalation via SCC manipulation.
- **OpenShift API coupling:** Importing `github.com/openshift/api/security/v1` and referencing `/etc/kubernetes/kubelet-ca.crt` make this operator non-portable to vanilla Kubernetes. Any upstream Kubernetes distribution migration requires significant rework.
- **Service CA path fragility:** The hardcoded path `openshiftCACertificateFile` and `DefaultKubeletCABasePath` will break if OpenShift changes certificate mount paths in future versions.
- **SCC reconciliation ordering:** SCCs must be fully reconciled before the DaemonSet is applied. Partial failures (SCC created but ServiceAccount binding incomplete) can leave the DaemonSet unschedulable with non-obvious error messages.
