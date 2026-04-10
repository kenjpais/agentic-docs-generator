```markdown
---
exec-plan-id: OCPBUGS-81509-fix-aso-crd-duplication
exec-plan-status: completed
exec-plan-title: OCPBUGS-81509: Fix ASO CRD Duplication in `verify-capi-manifests.sh` (PR #10451)
exec-plan-jira-key: OCPBUGS-81509
exec-plan-pr-link: https://github.com/openshift/cluster-api-provider-azure/pull/10451
exec-plan-created-date: 2023-10-26 # Placeholder, replace with actual PR merge date if available
exec-plan-last-updated-date: 2023-10-26 # Placeholder
---

### 1. Problem Statement

The `hack/verify-capi-manifests.sh` script, which is responsible for managing Cluster API (CAPI) manifests, contained a bug. Instead of cleanly writing Azure Service Operator (ASO) Custom Resource Definitions (CRDs) to the `data/data/cluster-api/azureaso-infrastructure-components.yaml` file, the script would append them. This led to the accumulation of duplicate ASO