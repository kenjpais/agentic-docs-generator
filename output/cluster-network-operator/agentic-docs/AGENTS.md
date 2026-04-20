# AGENTS.md

> **AI Agent Entry Point** — Table of contents only. Follow links for detail.

## What This Repo Does
`cluster-network-operator` (CNO) installs, configures, and upgrades the OpenShift cluster network (OVN-Kubernetes, OpenShift SDN, Kuryr). It is a cluster operator managing CRDs, DaemonSets, and network policy across the control plane.

---

## Component Map
```
┌─────────────────────────────────────────────────────────────┐
│                  cluster-network-operator                    │
│                                                             │
│  cmd/                  Entrypoints (operator, render)       │
│  pkg/                                                       │
│  ├── bootstrap/        Cluster bootstrap detection          │
│  ├── client/           Kubernetes/OpenShift client wrappers │
│  ├── network/          Network plugin reconcilers           │
│  │   ├── ovn_kubernetes.go   OVN-K reconciler (PRIMARY)    │
│  │   ├── sdn.go              OpenShift SDN reconciler       │
│  │   ├── kuryr.go            Kuryr reconciler               │
│  │   └── network.go          Plugin dispatch                │
│  ├── operator/         Main operator loop & status          │
│  ├── util/             Shared utilities                     │
│  └── apply/            Server-side apply helpers            │
│  bindata/              Embedded manifests (YAML/templates)  │
│  manifests/            CRD and operator manifests           │
│  vendor/               Vendored dependencies                │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

| Concept | What It Is | Key File |
|---|---|---|
| Network.operator.openshift.io | Primary CRD driving reconciliation | `manifests/0000_70_cluster-network-operator_01_crd.yaml` |
| OVN-Kubernetes | Default CNI plugin | `pkg/network/ovn_kubernetes.go` |
| OpenShift SDN | Legacy CNI plugin | `pkg/network/sdn.go` |
| bindata | Rendered manifests embedded in binary | `bindata/` + `pkg/util/render.go` |
| Bootstrap | Detects existing network config on startup | `pkg/bootstrap/` |
| Apply | Server-side apply for manifest management | `pkg/apply/` |
| Network policy (ICMP) | Allow ICMP in network policies | `pkg/network/ovn_kubernetes.go` |

---

## Key Invariants

- **Never mutate network type post-install** — migration between plugins is a controlled, multi-step process
- **bindata changes require re-render** — run `hack/update-generated-bindata.sh` after editing `bindata/`
- **Operator must tolerate partial cluster state** — control-plane-only nodes, zero workers at rollout
- **All CRD changes need migration paths** — no breaking schema changes without version bump
- **Vendor is committed** — run `hack/update-vendor.sh` to update dependencies

---

## Critical File Paths

```
pkg/network/ovn_kubernetes.go     # OVN-K plugin logic (largest, most active)
pkg/network/network.go            # Plugin dispatch and common reconcile
pkg/operator/operator.go          # Main operator loop
pkg/bootstrap/bootstrap.go        # Cluster state detection at startup
pkg/apply/apply.go                # Manifest apply logic
bindata/                          # All rendered Kubernetes manifests
manifests/                        # CRDs and operator deployment manifests
hack/                             # Developer scripts
vendor/                           # Vendored Go dependencies
```

---

## Build & Test Commands

```bash
# Build
make build

# Run unit tests
make test

# Update generated bindata (required after bindata/ changes)
hack/update-generated-bindata.sh

# Update vendored dependencies
hack/update-vendor.sh

# Lint
make lint

# Run e2e tests (requires cluster)
make test-e2e

# Render manifests locally
go run ./cmd/render --...
```

---

## Navigation by Intent

| I want to… | Go to… |
|---|---|
| Change OVN-Kubernetes config | `pkg/network/ovn_kubernetes.go` |
| Change network policy behavior | `pkg/network/ovn_kubernetes.go`, `bindata/network/ovn-kubernetes/` |
| Add/modify a manifest | `bindata/` → re-run bindata script |
| Understand operator reconcile loop | `pkg/operator/operator.go` |
| Debug bootstrap/detection issues | `pkg/bootstrap/bootstrap.go` |
| Modify CRDs | `manifests/` + update vendor if API changes |
| Add a new feature flag | `pkg/network/network.go`, operator CRD |
| Understand SDN migration | `pkg/network/sdn.go`, `docs/` |
| Find existing design docs | `docs/` |
| Track tech debt / active work | `agentic/exec-plans/` *(create if absent)* |

---

## Recent Activity Signals

- ICMP network policy support added (`pkg/network/ovn_kubernetes.go`)
- No-overlay networking mode added (`pkg/network/`)
- Control-plane rollout with zero workers hardened (`pkg/operator/`)
- Active OVN-Kubernetes rebasing and CORENET bug fixes

---

## Agentic Docs (Extended)

> Create `agentic/` if starting structured documentation.

- `agentic/DESIGN.md` — Architecture decisions and plugin model
- `agentic/TESTING.md` — Test strategy, e2e setup
- `agentic/DEVELOPMENT.md` — Local dev, cluster requirements
- `agentic/decisions/` — ADRs for network type choices
- `agentic/exec-plans/active/` — In-progress work