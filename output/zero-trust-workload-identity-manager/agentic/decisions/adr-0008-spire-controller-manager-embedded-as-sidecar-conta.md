---
id: ADR-0008
title: "SPIRE controller manager embedded as sidecar container within the SPIRE server StatefulSet pod"
date: 2025-05-27
status: accepted
deciders: [anirudhAgniRedhat, bharath-b-rh, swghosh, TrilokGeer]
components: [pkg/controller]
supersedes: ""
superseded-by: ""
---

# SPIRE Controller Manager Embedded as Sidecar in SPIRE Server StatefulSet

## Executive Summary
The operator co-locates the `spire-controller-manager` as a sidecar container within the same StatefulSet pod as the SPIRE server, sharing the server's Unix domain socket via an `emptyDir` volume. This topology couples the controller manager's lifecycle directly to the SPIRE server's, eliminates any network hop for the socket connection, and reduces the cluster footprint from two workload objects to one — at the cost of tighter coupling and a shared failure domain.

## What
- **Component:** `pkg/controller/spire-server/statefulset.go`, `GenerateSpireServerStatefulSet`
- **Decision:** The `spire-controller-manager` container runs inside the `spire-server` StatefulSet pod rather than as a standalone `Deployment`
- **Mechanism:** A shared `spire-server-socket` `emptyDir` volume is mounted read-write by `spire-server` at `/tmp/spire-server/private` and read-only by `spire-controller-manager` at the same path
- **Configuration:** A separate `spire-controller-manager` ConfigMap is reconciled, its content hash is tracked in the pod template annotation `ztwim.openshift.io/spire-controller-manager-config-hash`, distinct from `ztwim.openshift.io/spire-server-config-hash`

## Why
SPIRE's controller manager communicates with the SPIRE server exclusively over a Unix domain socket. Placing both processes in the same pod removes any requirement for a network-accessible endpoint between them, avoids TLS bootstrap ordering problems, and guarantees the socket is available the moment the server container writes it. In an operator-managed, single-replica SPIRE deployment on OpenShift, a separate `Deployment` for the controller manager would add scheduling complexity (affinity rules, startup ordering) without operational benefit.

## Goals
- Guarantee zero-network-hop, same-lifecycle access to the SPIRE server Unix socket from the controller manager
- Drive pod restarts on controller manager config changes independently of SPIRE server config changes via separate annotation keys
- Reduce Kubernetes object count and scheduling surface area for a single-replica topology
- Keep both containers under one `controllerutil.SetControllerReference` ownership chain tied to the `SpireServer` CR

## Non-Goals
- High-availability or multi-replica SPIRE server deployments
- Independent scaling of the controller manager relative to the SPIRE server
- Network-based (gRPC/TLS) communication between the two processes
- Lifecycle management of the OIDC discovery provider (handled separately in `pkg/controller/spire-oidc-discovery-provider/controller.go` as its own `Deployment`)

## How
`GenerateSpireServerStatefulSet` in `statefulset.go` constructs a single `appsv1.StatefulSet` with `Replicas: 1` containing two entries in `spec.template.spec.containers`:

1. **`spire-server`** — mounts `spire-server-socket` (emptyDir) read-write at `/tmp/spire-server/private`, writes its Unix socket there
2. **`spire-controller-manager`** — mounts the same `spire-server-socket` volume read-only at the identical path; also mounts `controller-manager-config` (ConfigMap) as a file subpath and a private `spire-controller-manager-tmp` emptyDir at `/tmp`

Both containers have independent liveness/readiness probes (`spireServerHealthPort`=8080, `spireCtrlMgrHealthPort`=8083) so Kubernetes can distinguish their health states.

The `reconcileStatefulSet` function receives two hash arguments — `spireServerConfigMapHash` and `spireControllerManagerConfigMapHash` — and writes them as distinct pod template annotations (`ztwim.openshift.io/spire-server-config-hash`, `ztwim.openshift.io/spire-controller-manager-config-hash`). A change to either ConfigMap triggers a rolling restart of the StatefulSet pod, correctly attributing the cause.

The `needsUpdate` check on the existing StatefulSet gates all mutations; `createOnlyMode` suppresses updates when the flag is active, preventing drift correction during controlled rollouts.

The OIDC provider contrast (a separate `Deployment` in `spire-oidc-discovery-provider/controller.go`) confirms the sidecar pattern is a deliberate choice for the server/controller-manager pair, not a blanket policy.

## Alternatives

**Separate `Deployment` for `spire-controller-manager`**
Standard upstream SPIRE Helm chart topology. Requires the controller manager to reach the server via a network socket or `hostPath`/shared volume with affinity rules. On OpenShift with `ReadOnlyRootFilesystem` and strict pod security, coordinating volume sharing across pods adds significant complexity. Rejected due to scheduling coupling overhead and socket bootstrapping race conditions.

**`initContainer` to wait for socket readiness**
Could be added to the controller manager to delay start until the socket appears. Does not change the fundamental deployment topology and adds operational opacity. Not adopted; Kubernetes readiness probes on the server container serve a similar signal.

**`hostPath` volume for socket sharing across pods**
Would allow separate pods but introduces node-level state, breaks pod mobility, and conflicts with OpenShift's restricted security context constraints. Rejected.

## Risks

- **Single failure domain:** A crash-loop in either container (e.g., controller manager misconfiguration) kills the pod and takes the SPIRE server offline. There is no independent restart boundary between the two processes.
- **Debugging difficulty:** Operators must inspect a multi-container pod; logs and exec sessions must explicitly target `--container spire-controller-manager`, increasing cognitive overhead.
- **Config change coupling:** Both ConfigMap hashes share one pod template — any config change to either component causes a full pod restart, briefly interrupting SPIRE server attestation for all workloads.
- **Scale-out friction:** If a future requirement demands multiple SPIRE server replicas or independent controller manager scaling, the sidecar topology requires a significant refactor to extract the controller manager into its own `Deployment` with affinity and network socket exposure.
- **Resource contention:** Both containers share the same `config.Resources` value (`utils.DerefResourceRequirements(config.Resources)`), meaning there is no independent resource tuning for the controller manager without API surface changes.
