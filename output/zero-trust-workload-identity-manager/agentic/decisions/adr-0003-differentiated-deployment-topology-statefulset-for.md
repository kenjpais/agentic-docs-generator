---
id: ADR-0003
title: "Differentiated Deployment Topology: StatefulSet for Server, DaemonSet for Agent/CSI, Deployment for OIDC"
date: 2025-05-27
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Differentiated Deployment Topology: StatefulSet, DaemonSet, and Deployment for SPIRE Components

## Executive Summary
The operator deploys SPIRE Server as a StatefulSet, SPIRE Agent and SPIFFE CSI Driver as DaemonSets, and the OIDC Discovery Provider as a Deployment. This mapping is not arbitrary: it directly reflects each component's operational contract with the cluster—stateful CA persistence, per-node socket presence, and stateless scalable HTTP serving, respectively. Choosing the wrong workload kind for any component would break core SPIRE guarantees around identity continuity, workload attestation, and certificate delivery.

## What
Four controllers each manage one workload kind:
- `pkg/controller/spire-server/statefulset.go` — `appsv1.StatefulSet` named `spire-server`
- `pkg/controller/spire-agent/daemonset.go` — `appsv1.DaemonSet` named `spire-agent`
- `pkg/controller/spiffe-csi-driver/daemonset.go` — `appsv1.DaemonSet` named `spire-spiffe-csi-driver`
- `pkg/controller/spire-oidc-discovery-provider/deployments.go` — `appsv1.Deployment` named `spire-spiffe-oidc-discovery-provider`

Each file exposes a `generate*` function that builds the full workload manifest and a `reconcile*` function that applies a create-or-update loop with a `createOnlyMode` guard.

## Why
SPIRE's security model imposes hard operational constraints on each component:

- **SPIRE Server** holds the signing CA private key and issues SVIDs. Losing that state across restarts breaks the entire trust chain. A PVC-backed `VolumeClaimTemplate` in the StatefulSet guarantees `/run/spire/data` survives pod restarts without relying on external storage coordination.
- **SPIRE Agent** performs node attestation by inspecting host-level metadata (`HostPID: true`, `HostNetwork: true`). It must run on every node to attest workloads on that node. A DaemonSet is the only primitive that guarantees exactly-one-per-node scheduling, including on nodes added later.
- **SPIFFE CSI Driver** exposes the SPIFFE workload API socket to pods via a CSI volume mount. Because CSI node plugins must register with kubelet on each host (writing to `/var/lib/kubelet/plugins_registry`), they must co-locate with the agent on every node via DaemonSet.
- **OIDC Discovery Provider** serves a stateless HTTPS endpoint (`/.well-known/openid-configuration`). It can run multiple replicas for availability and consumes SVID material via the CSI volume (`Driver: csi.spiffe.io`), requiring no per-node presence.

## Goals
- Guarantee SPIRE Server CA state survives restarts via PVC-backed StatefulSet.
- Ensure every cluster node runs exactly one SPIRE Agent instance for complete workload attestation coverage.
- Ensure every cluster node runs one CSI Driver instance so any pod can receive SPIFFE credentials via a CSI volume.
- Allow the OIDC Discovery Provider to scale horizontally without node affinity constraints.
- Enforce config-driven rolling updates via annotation-injected config map hashes on each workload.

## Non-Goals
- Multi-replica SPIRE Server HA (replica count is hardcoded to `ptr.To(int32(1))`).
- External CA or HSM integration for Server persistence.
- Per-node agent scaling controls (DaemonSet scheduling is delegated to NodeSelector/Tolerations/Affinity fields on the spec).

## How

**SPIRE Server (`statefulset.go`):** `GenerateSpireServerStatefulSet` builds a `StatefulSet` with `Replicas: 1`. The `VolumeClaimTemplate` names `spire-data`, sized from `config.Persistence.Size` (default `1Gi`), mounts at `/run/spire/data`. A sidecar container `spire-controller-manager` shares the pod, communicating via the `spire-server-socket` EmptyDir volume. Config drift is detected by hashing the two config maps and storing them as pod annotations (`ztwim.openshift.io/spire-server-config-hash`, `ztwim.openshift.io/spire-controller-manager-config-hash`), which triggers a rollout when configs change. Optional database TLS is injected by appending a Secret volume/mount when `config.Datastore.TLSSecretName != ""`.

**SPIRE Agent (`daemonset.go`):** `generateSpireAgentDaemonSet` sets `HostPID: true` and `HostNetwork: true` with `DNSClusterFirstWithHostNet`, required for node attestation. The SPIFFE socket is mounted from the host via `HostPath` at `config.SocketPath` (type `DirectoryOrCreate`). A projected `ServiceAccountToken` volume with audience `spire-server` and 2-hour expiry provides the bootstrap join token. Kubelet CA mounts for workload attestor verification are conditionally added by `getHostCertMountPath`, which handles `hostCert`, `auto`, and `skip` modes. `RollingUpdate` with `MaxUnavailable: 1` limits disruption during upgrades.

**SPIFFE CSI Driver (`daemonset.go`):** `generateSpiffeCsiDriverDaemonSet` runs two containers: `spiffe-csi-driver` and `node-driver-registrar`. The CSI socket is a HostPath at `/var/lib/kubelet/plugins/<pluginName>`. The `mountpoint-dir` HostPath (`/var/lib/kubelet/pods`) uses `MountPropagationBidirectional` so volume mounts propagate to workload pods. An init container runs `chcon` to set SELinux context on the agent socket directory—an OpenShift-specific requirement. `node-driver-registrar` registers the plugin with kubelet via `/var/lib/kubelet/plugins_registry`.

**OIDC Discovery Provider (`deployments.go`):** `generateDeployment` respects `config.Spec.ReplicaCount` (falls back to `1`). It consumes the SPIFFE workload API through a CSI volume (`Driver: csi.spiffe.io`, ReadOnly), removing any HostPath dependency. TLS termination uses a Secret volume (`oidc-serving-cert`). Proxy configuration is applied via `utils.AddProxyConfigToPod` (without the internal `NO_PROXY` additions used for the Agent).

All four reconcilers share the same create-or-update pattern: check for existence, create if absent, call `needsUpdate` (delegating to `utils.ResourceNeedsUpdate`) and skip mutation if `createOnlyMode` is set.

## Alternatives

**StatefulSet for Agent:** Would allow stable network identities per node but cannot enforce one-per-node scheduling. Without DaemonSet, new nodes joining the cluster would not automatically receive an agent, breaking attestation for workloads on those nodes.

**Deployment for Agent/CSI:** A Deployment with `replicas == nodeCount` is fragile—it cannot guarantee placement or react automatically to node additions. It also cannot guarantee the CSI plugin registers with each local kubelet.

**StatefulSet for OIDC Provider:** Unnecessary: the provider is stateless and horizontally scalable. A StatefulSet would introduce ordering constraints and prevent smooth horizontal scaling.

**Deployment for SPIRE Server with external storage:** Possible with a shared external database, but the current design uses the simpler embedded SQLite-on-PVC path. A Deployment would require a `ReadWriteMany` PVC or an external DB, adding operational complexity outside the operator's current scope.

## Risks

- **StatefulSet PVC lifecycle:** Deleting the StatefulSet does not delete its PVC. CA state may persist unintentionally after uninstall, or conversely be lost if the PVC is manually deleted before the Server has re-issued trust bundles.
- **DaemonSet rolling updates:** `MaxUnavailable: 1` means one node at a time loses its agent during upgrades. Workloads on that node cannot renew SVIDs during the window, which is acceptable for short upgrades but risky on slow image pulls.
- **Single-replica Server:** No HA. A Server pod restart causes a brief identity issuance outage. Expanding to HA would require changing the workload kind or adding a shared datastore, both of which are non-trivial changes.
- **HostPath coupling:** Both the Agent and CSI Driver depend on host filesystem paths (`config.SocketPath`, `/var/lib/kubelet/*`). Changes to OpenShift node layout or kubelet plugin paths require coordinated updates across the operator and node configuration.
- **SELinux init container:** The `chcon` init container in the CSI DaemonSet is OpenShift-specific and will fail or be unnecessary on vanilla Kubernetes clusters, limiting portability.
