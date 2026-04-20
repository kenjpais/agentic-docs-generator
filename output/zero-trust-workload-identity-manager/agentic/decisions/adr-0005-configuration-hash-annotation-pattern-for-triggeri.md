---
id: ADR-0005
title: "Configuration hash annotation pattern for triggering rolling restarts on config changes"
date: 2025-05-27
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Configuration Hash Annotation Pattern for Rolling Restarts on Config Changes

## Executive Summary
When this operator reconciles ConfigMaps for SPIRE agent, SPIRE server, or OIDC discovery provider, it computes a hash of the generated configuration content and injects it as a pod template annotation on the corresponding workload resource. Kubernetes treats any annotation change as a pod template mutation and triggers a rolling restart, giving the operator a zero-overhead mechanism for propagating configuration changes to running pods without implementing a separate restart controller.

## What
Three workload types are affected: the SPIRE agent `DaemonSet` (`pkg/controller/spire-agent/daemonset.go`), the SPIRE server `StatefulSet` (`pkg/controller/spire-server/statefulset.go`), and the OIDC discovery provider `Deployment` (`pkg/controller/spire-oidc-discovery-provider/deployments.go`). The decision is: how does the operator ensure pods reload configuration after a ConfigMap update.

## Why
SPIRE components read their configuration files at startup, not dynamically at runtime. A ConfigMap update alone does not restart pods. Without an active restart mechanism, pods would continue running stale configuration after an operator reconcile, silently diverging from the desired state. The operator needed a declarative, Kubernetes-native way to couple configuration content to pod lifecycle.

## Goals
- Ensure pods restart automatically whenever their configuration content changes.
- Keep restart logic inside the existing reconcile loop with no additional controllers or watches.
- Make config drift visible and auditable via pod annotations.
- Leverage Kubernetes rolling update strategies already configured on each workload type.
- Support multiple independent config hashes on a single pod (e.g., SPIRE server tracks both `spire-server-config-hash` and `spire-controller-manager-config-hash`).

## Non-Goals
- Dynamic/hot configuration reloading without pod restart.
- Tracking changes to Secrets (e.g., TLS certs in `oidc-serving-cert`) via the same mechanism.
- Rollback or canary logic; that is delegated entirely to Kubernetes rolling update semantics.

## How
**Hash generation:** `generateSpireAgentConfigMap` in `pkg/controller/spire-agent/configmap.go` marshals the agent config struct to JSON, calls `utils.GenerateConfigHash(agentConfigJSON)`, and returns both the `ConfigMap` object and the hash string. The `reconcileConfigMap` function returns the hash to the caller.

**Hash injection:** The hash string is passed as a parameter into the workload generator functions. In `generateSpireAgentDaemonSet` (`pkg/controller/spire-agent/daemonset.go`), it is written into `Template.ObjectMeta.Annotations` under the key `spireAgentDaemonSetSpireAgentConfigHashAnnotationKey`. The same pattern appears in `GenerateSpireServerStatefulSet` (`pkg/controller/spire-server/statefulset.go`), which injects two annotations (`ztwim.openshift.io/spire-server-config-hash` and `ztwim.openshift.io/spire-controller-manager-config-hash`), and in `generateDeployment` (`pkg/controller/spire-oidc-discovery-provider/deployments.go`) under `spireOidcDeploymentSpireOidcConfigHashAnnotationKey`.

**Control flow:** During each reconcile loop, the ConfigMap is reconciled first; the hash is returned. The workload reconcile function (`reconcileDaemonSet`, `reconcileStatefulSet`, `reconcileDeployment`) generates the desired workload with the current hash embedded. If `needsUpdate` detects a difference from the existing resource (which will be true when the annotation value changed), the operator issues an `Update`. Kubernetes then rolls pods according to the `RollingUpdate` strategy already defined on each workload.

**Ordering guarantee:** ConfigMap reconciliation precedes workload reconciliation in the controller loop, so by the time the workload is updated, the new config content is already live in the ConfigMap.

## Alternatives

**Restarting pods imperatively via the controller:** The operator could issue a DELETE on pods or patch a `restartedAt` annotation in response to ConfigMap watch events. This adds controller complexity, requires additional RBAC, and risks double-restarts if the reconcile loop fires multiple times.

**Mounting ConfigMaps with `subPath` and relying on inotify/signal:** SPIRE does not support SIGHUP-triggered config reload, making this ineffective regardless of mount semantics.

**Version label on the ConfigMap propagated to pods via a mutating webhook:** Overly complex and introduces a webhook dependency for a problem already solvable in the reconcile loop.

**Immutable ConfigMaps with name-versioning (e.g., `spire-agent-v3`):** Requires updating volume references in the pod spec on every config change and complicates garbage collection. The annotation approach achieves the same effect with a single mutable ConfigMap.

## Risks

- **Hash collisions or instability:** If `utils.GenerateConfigHash` produces non-deterministic output (e.g., due to map iteration order in Go), spurious restarts will occur on every reconcile. The use of `json.MarshalIndent` on a `map[string]interface{}` in `generateAgentConfig` is a latent risk since Go map serialization order is not guaranteed.
- **Silent stale config on hash equality:** If two semantically different configs hash identically, no restart occurs. This is a standard hash risk but unlikely in practice with a good hash function.
- **Debugging difficulty:** An unexpected rolling restart will show only a changed annotation value in `kubectl describe`; operators must know to look at this annotation to understand why pods cycled.
- **StatefulSet restart ordering:** For the SPIRE server `StatefulSet`, a rolling restart replaces the single replica, causing a brief SPIRE server outage. There is no disruption budget configured in the evidence, so this is gated only by readiness probes.
