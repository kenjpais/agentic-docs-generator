---
id: ADR-0006
title: "OpenShift-native security model using SecurityContextConstraints and OpenShift Route integration"
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

# OpenShift-Native Security Model: SCC, Routes, and Service CA Integration

## Executive Summary
The zero-trust-workload-identity-manager operator adopts a fully OpenShift-native security model, reconciling SecurityContextConstraints for privileged SPIRE components, creating OpenShift Routes for external exposure, and trusting the OpenShift service CA for metrics mTLS—rather than using generic Kubernetes equivalents. This embeds deep platform coupling as a deliberate trade-off to gain first-class OpenShift security semantics for workloads requiring node-level access and cryptographic identity.

## What
Three controllers are affected: `pkg/controller/spiffe-csi-driver/controller.go`, `pkg/controller/spire-agent/controller.go`, and `pkg/controller/spire-oidc-discovery-provider/controller.go`. The decisions are: (1) reconcile `securityv1.SecurityContextConstraints` objects for the SPIRE agent and SPIFFE CSI driver, (2) reconcile `routev1.Route` objects (not `networking.k8s.io/v1 Ingress`) for the OIDC discovery provider, and (3) load the OpenShift service CA at `/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt` to populate `ClientCAs` on the metrics TLS config in `cmd/zero-trust-workload-identity-manager/main.go`.

## Why
SPIRE agents run as DaemonSets requiring host PID, host network, and volume mounts into `/var/run/spire`. The SPIFFE CSI driver similarly requires privileged node access. On OpenShift, PodSecurityAdmission alone cannot grant these capabilities—SCCs are the enforced mechanism. Omitting SCC reconciliation would cause pod scheduling failures on any OpenShift cluster. Routes are chosen because OpenShift clusters frequently lack an Ingress controller compatible with the generic `networking.k8s.io/v1` API, and Routes provide TLS passthrough and re-encryption semantics with integrated cert management. The service CA integration for metrics avoids distributing custom PKI while enabling mTLS to the operator's metrics endpoint.

## Goals
- Ensure SPIRE agent DaemonSet and SPIFFE CSI driver DaemonSet pods are schedulable on OpenShift nodes by owning their SCCs
- Expose the OIDC discovery provider externally using OpenShift-native routing with TLS support
- Protect the metrics endpoint with mTLS verified against the cluster's service CA without external certificate management
- React to SCC and Route drift via controller watches, maintaining reconciled state

## Non-Goals
- Supporting vanilla Kubernetes clusters or providing a generic Ingress fallback
- Managing SCCs for workloads other than the SPIRE agent and SPIFFE CSI driver
- Replacing SPIRE's own SVID issuance with OpenShift certificate mechanisms

## How
**Scheme registration** (`cmd/zero-trust-workload-identity-manager/main.go`): `securityv1.AddToScheme(scheme)` and `routev1.AddToScheme(scheme)` register OpenShift CRD groups so controller-runtime can watch and patch these objects.

**SCC reconciliation**: Both `SpiffeCsiReconciler.Reconcile` and `SpireAgentReconciler.Reconcile` call `reconcileSCC` as an explicit step in their ordered reconciliation sequence. The `SetupWithManager` methods in both controllers register `securityv1.SecurityContextConstraints` watches with component-scoped predicates (`utils.ControllerManagedResourcesForComponent`), meaning SCC drift triggers re-queuing of the owning CR.

**Route reconciliation**: `SpireOidcDiscoveryProviderReconciler.Reconcile` calls `reconcileExternalCertRBAC` before `reconcileRoute` to ensure the router service account has secret-read permissions before the Route object exists. The `SetupWithManager` watch on `routev1.Route` ensures Route deletion or modification re-triggers reconciliation.

**Metrics mTLS** (`main.go`): When `secureMetrics` is true, a `tls.Config` mutator reads the service CA PEM from the well-known pod-mounted path (`openshiftCACertificateFile = "/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt"`), appends it to the system cert pool, and assigns it as `ClientCAs`. This delegates client certificate trust entirely to the OpenShift service CA injector.

**Status tracking**: Each OpenShift-specific resource has a named condition constant (`SecurityContextConstraintsAvailable`, `RouteAvailable`) surfaced through the `status.Manager`, enabling operators and GitOps tools to observe SCC and Route health independently.

## Alternatives
**PodSecurityAdmission with privileged namespace labels**: Could grant node-level access without SCCs, but PSA operates at admission time only and provides no ongoing reconciliation. Drift cannot be detected. PSA also lacks OpenShift's per-ServiceAccount SCC binding model, making least-privilege per-component assignment harder.

**Generic Ingress instead of Route**: `networking.k8s.io/v1 Ingress` is portable but requires an IngressClass to be present and configured, which is not guaranteed on OpenShift. Routes are the primary external exposure primitive on OpenShift and integrate directly with the HAProxy-based router without additional configuration.

**External certificate management for metrics**: Using cert-manager or a manually provisioned certificate would decouple the operator from the service CA but introduces an additional dependency and operational burden. The service CA mount is available on every OpenShift pod without configuration.

## Risks
- **Portability**: The operator cannot run on non-OpenShift Kubernetes distributions. Any attempt to deploy it on upstream Kubernetes will fail at scheme registration or when the API server rejects SCC and Route objects.
- **SCC API evolution**: OpenShift's `security.openshift.io/v1` SCC API is a compatibility concern across major OpenShift versions. Breaking changes would require coordinated operator updates.
- **Service CA rotation**: If the OpenShift service CA rotates, the operator process must restart to reload the new CA from the mounted file; the current implementation reads it once at startup with no reload mechanism.
- **RBAC ordering dependency**: The `reconcileExternalCertRBAC`-before-`reconcileRoute` ordering in the OIDC controller is implicit. If the RBAC step is refactored or reordered, the Route may be created before the router has secret access, causing TLS failures that are difficult to diagnose.
