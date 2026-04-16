---
id: ADR-0004
title: "Image injection via environment variables rather than spec fields or image streams"
date: 2026-03-13
status: accepted
deciders: [bharath-b-rh, swghosh, TrilokGeer, mytreya-rh]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Image Injection via Environment Variables for Operand Container Images

## Executive Summary
The operator injects operand container images (trust-manager, istio-csr, cert-manager) into reconciled Deployments by reading environment variables set on the operator pod at startup, rather than exposing image fields in the CRD API or resolving them through OpenShift ImageStreams. This aligns with the OLM `related-images` convention, enabling digest-pinned, air-gapped-safe image delivery without expanding the public API surface or creating runtime image resolution dependencies.

## What
- **Components touched:** `pkg/controller/trustmanager/deployments.go` (`updateImage`), `pkg/controller/istiocsr/deployments.go` (`updateImage`, `updateImageInStatus`), and equivalent logic for cert-manager components.
- **Decision:** Operand images are sourced exclusively from environment variables (`TRUST_MANAGER_IMAGE`, `ISTIOCSR_IMAGE`, and related `RELATED_IMAGE_*` names) injected into the operator pod, never from CRD spec fields or runtime image stream lookups.

## Why
OLM bundles for OpenShift operators are expected to declare `relatedImages` in their bundle metadata. OLM substitutes digest-pinned references and injects them as environment variables into the operator pod before it starts. Without this pattern, images embedded in operator binary assets or CRD defaults would diverge from what OLM audited and pinned, breaking disconnected/air-gapped cluster installations. Exposing image fields in the CRD would also create an attack surface for accidental or malicious image substitution by cluster users, and would require API versioning every time an image reference changes.

## Goals
- Enable OLM digest pinning and disconnected installation without any CRD API changes.
- Fail fast and irrecoverably at reconciliation time if an expected image env var is absent, preventing silent deployment of wrong or empty images.
- Surface the resolved image reference in CR status (`IstioCSR.Status.IstioCSRImage`) for observability and auditability.
- Keep image selection entirely within operator-controlled configuration, not user-controlled spec fields.

## Non-Goals
- Allowing cluster administrators to override operand images via the CRD spec.
- Supporting OpenShift ImageStream-based image resolution or tag tracking.
- Managing image pull secrets or registry credentials.
- Providing a mechanism to roll out image updates without redeploying the operator pod itself.

## How
During each reconciliation loop, the `getDeploymentObject` functions in both `pkg/controller/trustmanager/deployments.go` and `pkg/controller/istiocsr/deployments.go` build a `*appsv1.Deployment` from an embedded bindata manifest (`assets.MustAsset(deploymentAssetName)`), then mutate it through a pipeline of `update*` functions.

The image injection step calls `os.Getenv(trustManagerImageNameEnvVarName)` (trustmanager) or `os.Getenv(istiocsrImageNameEnvVarName)` (istiocsr). If the variable is empty, both return a non-nil error immediately wrapped as `common.NewIrrecoverableError`, which prevents the reconciler from applying a deployment with no image and stops the retry loop for a configuration-level failure.

When the variable is populated, the function iterates `deployment.Spec.Template.Spec.Containers` and sets `.Image` only on the container matching the known name constant (`trustManagerContainerName`, `istiocsrContainerName`). All other container fields remain as declared in the bindata manifest.

For istiocsr, `updateImageInStatus` additionally writes the resolved image string back to `IstioCSR.Status.IstioCSRImage` after the deployment is created or updated, giving operators a status-level record of which image is in use.

The operator pod receives these env vars via its own Deployment spec in the OLM bundle, where OLM substitutes digest-pinned values from the `relatedImages` manifest section before pod scheduling.

## Alternatives

**Image field in CRD spec:** Adding an `image` field to `TrustManagerConfig` or `IstioCSRConfig` would give administrators direct control but would expose image selection to unprivileged users, require API versioning, and break OLM's digest-pinning contract since OLM only injects into operator pod env vars, not CR fields.

**OpenShift ImageStreams:** The operator could resolve a tag from an ImageStream at reconciliation time. This was common in older OpenShift operators but adds a runtime dependency on the image registry, breaks in disconnected environments without careful mirroring configuration, and introduces time-of-check/time-of-use races when tags move.

**Hardcoded image references in bindata manifests:** Embedding image references in the baked-in YAML assets makes sense for development defaults but prevents OLM from substituting digests and would require rebuilding the operator binary to change images, making patch releases expensive.

**ConfigMap or Secret for image references:** A cluster-scoped ConfigMap could hold image references, decoupling them from the operator binary. However, this is non-standard, requires RBAC to protect the ConfigMap, and OLM has no mechanism to populate it automatically.

## Risks

- **Silent misconfiguration:** If the operator pod is deployed without the expected env vars (e.g., manual installation outside OLM), reconciliation fails with an irrecoverable error. The error message names the missing variable, but diagnosing this requires inspecting operator logs rather than CR status conditions.
- **No user override path:** Administrators who need to substitute an image (e.g., a patched build for a CVE) have no supported mechanism short of patching the operator Deployment itself and breaking OLM management.
- **Env var name drift:** The constant names (`trustManagerImageNameEnvVarName`, `istiocsrImageNameEnvVarName`) must stay in sync with the OLM bundle's `relatedImages` and env injection stanzas. A rename in one place without updating the other silently breaks image injection with an irrecoverable reconciliation error.
- **Testing surface:** Unit tests must inject env vars via `os.Setenv` before calling `updateImage`, making test isolation dependent on correct setup/teardown and creating potential test pollution in parallel test runs.
