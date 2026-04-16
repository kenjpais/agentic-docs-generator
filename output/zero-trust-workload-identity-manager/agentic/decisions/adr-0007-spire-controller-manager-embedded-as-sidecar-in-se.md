---
id: ADR-0007
title: "SPIRE Controller Manager Embedded as Sidecar in Server StatefulSet"
date: 2025-05-27
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [cmd/zero-trust-workload-identity-manager, pkg/controller]
supersedes: ""
superseded-by: ""
---

# SPIRE Controller Manager Embedded as Sidecar in Server StatefulSet

## Executive Summary
The SPIRE Controller Manager is deployed as a sidecar container within the SPIRE Server StatefulSet rather than as a separate Deployment or StatefulSet. This co-location enables direct filesystem-based communication via a shared Unix socket, eliminates network-layer complexity for admin API access, and simplifies lifecycle coupling between the two components. The operator manages their configurations independently but tracks both via pod annotation hashes to trigger coordinated rollouts.

## What
- `pkg/controller/spire-server/statefulset.go`: `GenerateSpireServerStatefulSet` produces a single `appsv1.StatefulSet` with two containers: `spire-server` and `spire-controller-manager`.
- The `spire-server-socket` emptyDir volume is mounted read-write into `spire-server` at `/tmp/spire-server/private` and read-only into `spire-controller-manager` at the same path.
- Two separate ConfigMaps (`spire-server` and `spire-controller-manager`) are projected as separate volumes into their respective containers.
- Pod annotations carry two independent config hashes: `ztwim.openshift.io/spire-server-config-hash` and `ztwim.openshift.io/spire-controller-manager-config-hash`.
- `reconcileStatefulSet` accepts both hashes and embeds them in the pod template, so a change to either ConfigMap triggers a StatefulSet rollout.

## Why
SPIRE Controller Manager requires access to SPIRE Server's admin API, which is exposed exclusively over a Unix domain socket. This socket is not network-accessible by design—it is a local privilege boundary. Co-locating both processes in the same pod and sharing the socket via an emptyDir is the canonical approach in the SPIRE ecosystem. Deploying them as separate workloads would require exposing the admin socket over the network (introducing a security regression) or implementing a proxy layer, both of which add complexity with no offsetting benefit in a single-replica operator-managed topology.

## Goals
- Provide `spire-controller-manager` with zero-network-hop access to the SPIRE Server admin Unix socket.
- Keep the deployment unit atomic: the controller manager cannot run without a live SPIRE Server, so they share a fate boundary.
- Enable independent configuration changes to either component to trigger pod rollouts without coupling the two ConfigMaps.
- Minimize operational surface: one StatefulSet to monitor, one PodDisruptionBudget surface, one scheduling decision.

## Non-Goals
- High-availability or multi-replica SPIRE Server topologies (replicas is hardcoded to `1`).
- Independent scaling of the controller manager separate from the server.
- Network-accessible admin API exposure.
- Separate rollout strategies for each container.

## How
`GenerateSpireServerStatefulSet` in `pkg/controller/spire-server/statefulset.go` constructs the StatefulSet spec with both containers inline. The shared socket volume is declared once in `volumes` as `{Name: "spire-server-socket", VolumeSource: EmptyDir}` and referenced in both containers' `VolumeMounts`. The `spire-server` container mounts it read-write (it creates the socket); `spire-controller-manager` mounts it read-only (it consumes the socket).

Each container gets its own ConfigMap-backed volume (`spire-config` → `spire-server` ConfigMap; `controller-manager-config` → `spire-controller-manager` ConfigMap). The controller manager config is mounted via `SubPath` to expose only the specific file `controller-manager-config.yaml`.

The `reconcileStatefulSet` function receives `spireServerConfigMapHash` and `spireControllerManagerConfigMapHash` as parameters. Both are stamped into pod template annotations. Kubernetes detects annotation drift via `needsUpdate`, causing the StatefulSet to roll when either config changes—this is the standard configmap-hash rollout trigger pattern.

Both containers have independent health ports (`server-healthz` on 8080 for SPIRE Server, `ctrlmgr-healthz` on 8083 for controller manager) with liveness and readiness probes, allowing Kubernetes to distinguish container-level failures within the shared pod.

The `kubectl.kubernetes.io/default-container: spire-server` annotation ensures operator UX defaults to the primary container on `kubectl exec`/`logs`.

## Alternatives

**Separate Deployment for controller manager**: Would require exposing the SPIRE admin socket over the network or implementing a proxy. This weakens the security posture of the admin API and adds a network hop. Rejected because the Unix socket boundary is a deliberate SPIRE security design.

**Init container to pre-start SPIRE Server**: Would not solve the runtime dependency—controller manager needs continuous socket access, not just startup access. Sidecars provide the correct lifecycle model.

**Separate StatefulSet sharing a PVC-backed socket**: PVCs with `ReadWriteMany` add storage infrastructure requirements. EmptyDir is simpler and correct for ephemeral IPC within a pod.

**Operator reconciles controller manager CRDs directly**: Would require embedding controller manager logic into the operator binary. The sidecar approach keeps SPIRE Controller Manager as a black-box binary with its own release cadence.

## Risks

**Execution risks**: A crash in either container does not restart the other independently—a `spire-controller-manager` OOMKill will leave `spire-server` running but unmanaged until Kubernetes restarts the sidecar. The health probe ports are distinct, but pod restart policy applies at the pod level.

**Operational risks**: Debugging requires knowing which container to target. The `default-container` annotation mitigates this, but log aggregation and alerting must account for two log streams from one pod. The `needsUpdate` diff function (not shown in full) must correctly detect annotation changes; a bug there would silently suppress rollouts on config changes.

**Evolution risks**: If SPIRE Server needs to scale beyond 1 replica in the future, the emptyDir socket approach breaks—each pod gets its own socket, and the controller manager would need to be redesigned to connect to a specific replica. The hardcoded `Replicas: ptr.To(int32(1))` makes this constraint explicit but not enforced at the API level.
