---
id: ADR-0003
title: "Differentiated workload deployment topology: StatefulSet for server, DaemonSet for agent and CSI driver, Deployment for OIDC provider"
date: 2025-05-27
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# Differentiated Workload Deployment Topology for SPIRE Components

## Executive Summary
The operator deploys each SPIRE subsystem using the Kubernetes workload type whose semantics match its operational requirements: a StatefulSet with a PersistentVolumeClaim for the SPIRE server (durable identity storage), DaemonSets for the SPIRE agent and SPIFFE CSI driver (mandatory node-local presence), and a scalable Deployment for the OIDC discovery provider (stateless HTTP service). This alignment eliminates the need for compensating workarounds and makes operational failure modes predictable.

## What
Four controllers manage four distinct workload kinds:
- `pkg/controller/spire-server/statefulset.go` — `appsv1.StatefulSet` named `spire-server`, replica count fixed at 1, with a `VolumeClaimTemplate` for `/run/spire/data`
- `pkg/controller/spire-agent/daemonset.go` — `appsv1.DaemonSet` named `spire-agent`, with `HostPID`, `HostNetwork`, and a `HostPath` socket volume
- `pkg/controller/spiffe-csi-driver/daemonset.go` — `appsv1.DaemonSet` named `spire-spiffe-csi-driver`, with bidirectional `MountPropagation` into `/var/lib/kubelet/pods`
- `pkg/controller/spire-oidc-discovery-provider/deployments.go` — `appsv1.Deployment` named `spire-spiffe-oidc-discovery-provider`, replica count driven by `config.Spec.ReplicaCount` (default 1)

## Why
Each SPIRE component has fundamentally different runtime constraints:
- The **server** is the root of trust; it must retain its CA key material and registration state across restarts. A Deployment with an EmptyDir would lose that state on pod eviction.
- The **agent** must run on every node to intercept workload API calls via a Unix socket on the host filesystem (`config.SocketPath`). A Deployment cannot guarantee one replica per node.
- The **CSI driver** must register with each node's kubelet plugin registry (`/var/lib/kubelet/plugins_registry`) and propagate SPIFFE volume mounts into pod sandboxes. This is inherently per-node.
- The **OIDC provider** is a stateless HTTPS service that reads credentials via the SPIFFE CSI volume; horizontal scaling is safe and desirable for availability.

## Goals
- Match Kubernetes scheduling semantics to component operational requirements without compensating logic
- Ensure the SPIRE server's CA and datastore survive pod restarts and rescheduling
- Guarantee a SPIRE agent and CSI driver instance on every schedulable node
- Allow the OIDC provider to scale independently of the trust plane components
- Surface health through per-workload-type status checks (`CheckStatefulSetHealth`, `CheckDaemonSetHealth`, `CheckDeploymentHealth`)

## Non-Goals
- High-availability for the SPIRE server (replica count is hardcoded to 1; HA server federation is not addressed)
- Automatic horizontal scaling of the OIDC provider (replica count is operator-spec-driven, not HPA-driven)
- Node filtering logic beyond `NodeSelector`, `Affinity`, and `Tolerations` passed through from CRD specs

## How
Each controller follows an identical reconcile loop structure: generate desired state → set owner reference → get existing resource → create if absent, update if `needsUpdate` returns true, skip if `createOnlyMode` is set → check health via the `status.Manager`.

**StatefulSet (server):** `GenerateSpireServerStatefulSet` in `statefulset.go` produces a StatefulSet with `Replicas: ptr.To(int32(1))` and a `VolumeClaimTemplate` that provisions a PVC sized from `config.Persistence.Size` with the configured `StorageClass`. The pod co-locates `spire-server` and `spire-controller-manager` containers sharing a Unix socket via an EmptyDir volume (`spire-server-socket`). Config changes are propagated via pod annotation hashes (`ztwim.openshift.io/spire-server-config-hash`) to trigger rolling restarts.

**Agent DaemonSet:** `generateSpireAgentDaemonSet` in `daemonset.go` sets `HostPID: true`, `HostNetwork: true`, and `DNSPolicy: ClusterFirstWithHostNet`. The agent socket is placed on the host at `config.SocketPath` via a `HostPathDirectoryOrCreate` volume. An optional kubelet CA hostPath mount is added conditionally via `getHostCertMountPath` for workload attestation. Proxy config is injected with internal service exclusions via `AddProxyConfigToPodWithInternalNoProxy`.

**CSI Driver DaemonSet:** `generateSpiffeCsiDriverDaemonSet` in `daemonset.go` runs an init container (`set-context`) to apply the correct SELinux label to the agent socket directory, then runs `spiffe-csi-driver` and `node-driver-registrar` side by side. The `mountpoint-dir` volume uses `MountPropagationBidirectional` so CSI mounts propagate into workload pod namespaces.

**OIDC Deployment:** `generateDeployment` in `deployments.go` reads `config.Spec.ReplicaCount` to set replicas (minimum 1). The pod consumes the SPIFFE workload API through a CSI volume (`Driver: csiDriverName`) rather than a hostPath, making it portable across nodes. TLS is served from a Secret (`oidc-serving-cert`).

## Alternatives

**All components as Deployments:** Simple to reason about, but the agent and CSI driver cannot guarantee node-local execution. A pod anti-affinity rule could spread agents but would silently leave newly added nodes uncovered.

**StatefulSet for the agent:** Would provide stable pod identity but is unnecessary overhead; agents are stateless across restarts (they re-attest) and the per-node constraint is not expressible in StatefulSet semantics.

**Single monolithic DaemonSet combining agent and CSI driver:** Reduces controller count but couples their lifecycle and update cadence, complicating independent configuration and version upgrades.

**Deployment with shared ReadWriteMany PVC for the server:** Would allow multiple replicas but requires a RWX-capable storage class and SPIRE server HA configuration, which is significantly more complex and not universally available in OpenShift environments.

## Risks

- **Operational:** The server StatefulSet at replica count 1 is a single point of failure for the trust root; any node failure hosting the server pod causes a cluster-wide identity outage until rescheduling completes.
- **Maintenance:** Four distinct workload types mean four separate `needsUpdate` comparison paths and four health-check invocations; drift in update logic between controllers can produce silent misconfiguration.
- **Evolution:** Promoting the server to HA requires replacing the StatefulSet with a more complex topology and changes to the SPIRE server's datastore configuration, which is a breaking schema change for the CRD.
- **CSI coupling:** The OIDC provider depends on the CSI driver DaemonSet being healthy on the same node it schedules to; if the CSI driver pod is evicted or not yet ready, the OIDC provider pod will fail to start due to the unresolvable CSI volume.
