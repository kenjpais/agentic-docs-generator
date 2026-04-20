---
id: ADR-0007
title: "OpenShift Service CA Used for Metrics TLS Client Verification"
date: 2025-03-04
status: accepted
deciders: [TrilokGeer, bharath-b-rh, swghosh, mytreya-rh]
components: [cmd/external-secrets-operator]
supersedes: ""
superseded-by: ""
---

# OpenShift Service CA Used for Metrics TLS Client Verification

## Executive Summary
The operator's metrics endpoint is secured using mutual TLS where the OpenShift service CA certificate (injected via the pod's service account volume) forms the client certificate authority pool. This anchors metrics scraping trust to OpenShift's built-in cluster PKI rather than managing a separate CA, ensuring only cluster-internal clients (e.g., Prometheus) can authenticate against the metrics endpoint without introducing custom certificate lifecycle management.

## What
- **File**: `cmd/external-secrets-operator/main.go`
- **Functions**: `loadOpenShiftCACertPool()`, `validateMetricsCertDir()`, and the `main()` metrics server setup block
- **Decision**: Use the OpenShift service CA certificate at the well-known path `/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt` as the `ClientCAs` trust anchor on the metrics TLS server, rather than a custom or self-managed CA.

## Why
OpenShift clusters automatically inject the service CA certificate into every pod's service account volume. Prometheus (and other cluster-internal scrapers) presents certificates signed by this same CA. By trusting this CA for client verification, the operator inherits cluster-wide PKI without managing its own certificate authority. Without this, the operator would need to either run metrics unauthenticated (a security regression) or maintain a separate CA and distribute trust to all scraping clients—a significant operational burden in a managed OpenShift environment.

## Goals
- Restrict metrics endpoint access to clients authenticated by the OpenShift cluster CA.
- Reuse OpenShift's built-in service CA injection mechanism; no custom CA provisioning needed.
- Layer client certificate verification on top of the existing `filters.WithAuthenticationAndAuthorization` filter for defense-in-depth.
- Allow the server-side certificate (`tls.crt`/`tls.key`) to be supplied separately via `--metrics-cert-dir`, keeping server and client trust concerns independent.

## Non-Goals
- Managing or rotating the service CA certificate itself (that is OpenShift's responsibility).
- Supporting non-OpenShift Kubernetes clusters where this CA path may not exist.
- Providing mutual TLS for the webhook server (only the metrics server is affected).
- Replacing the `FilterProvider` authn/authz layer—this is additive, not a substitute.

## How
In `main()`, when `--metrics-secure=true` (the default), the code calls `loadOpenShiftCACertPool()`. This function:
1. Attempts to load the system certificate pool as a base; falls back to an empty `x509.CertPool` if unavailable.
2. Reads the PEM file at the hardcoded constant `openshiftCACertificateFile` (`/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt`).
3. Appends the parsed certificate(s) to the pool; returns an error (causing `os.Exit(1)`) if the file is missing or unparseable.

The resulting `*x509.CertPool` is applied via a `metricsTLSOpts` closure that sets `tls.Config.ClientCAs`. This slice of `func(*tls.Config)` is passed into `metricsserver.Options.TLSOpts`, which controller-runtime applies when constructing the HTTPS listener.

The server-side TLS identity is handled separately: if `--metrics-cert-dir` is provided, `validateMetricsCertDir()` confirms `tls.crt` and `tls.key` exist, and the paths are set on `metricsServerOptions.CertDir/CertName/KeyName`; otherwise controller-runtime falls back to self-signed certificates for the server identity.

Authentication and authorization are further enforced by `metricsServerOptions.FilterProvider = filters.WithAuthenticationAndAuthorization`, meaning client certificate verification and RBAC-based authz are both active.

## Alternatives

**Custom CA with a Kubernetes Secret**: Generate an operator-specific CA, store it in a Secret, and mount it into the pod. Rejected because it requires CA bootstrapping logic, rotation handling, and distributing trust to Prometheus—all complexity that the OpenShift service CA mechanism provides for free.

**No client certificate verification (TLS server-only)**: Serve HTTPS without `ClientCAs`, relying solely on `filters.WithAuthenticationAndAuthorization` for access control. Rejected as it provides weaker defense-in-depth; any client that can reach the network endpoint could attempt to exploit the authn/authz layer.

**cert-manager managed CA**: Use cert-manager (already a scheme dependency) to issue a CA and rotate client certs. Rejected because it introduces a circular dependency risk (the operator manages cert-manager resources) and is unnecessary given the OpenShift service CA is already available.

**Hardcoded or embedded CA**: Bundle a CA certificate in the operator image. Rejected as it cannot rotate and breaks on cluster CA renewal.

## Risks

**Execution risks**: The path `/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt` is hardcoded as a constant. If OpenShift changes this injection path, the operator fails to start (`os.Exit(1)`). There is no flag or environment variable override.

**Operational risks**: Failure to read the CA file is fatal at startup, not at scrape time. A misconfigured pod security policy that omits the service account volume mount will prevent the operator from starting entirely, which may be difficult to diagnose without checking operator logs before the manager starts.

**Evolution risks**: This design is OpenShift-specific. Running the operator on vanilla Kubernetes (e.g., for development or testing) requires the CA file to be manually provisioned at the exact path, or the code must be patched. As the operator evolves toward multi-platform support, this tight coupling will need to be refactored into a configurable or optional code path.
