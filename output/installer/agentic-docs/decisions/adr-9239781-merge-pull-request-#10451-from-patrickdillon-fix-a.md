```markdown
# ADR 9239781: Fix ASO CRD Duplication in `verify-capi-manifests.sh`

## Metadata

*   **Date**: 2023-10-27
*   **Status**: Completed
*   **Decision Makers**: N/A (Decision implied by PR merge)

## Context

A bug was identified in the `hack/verify-capi-manifests.sh` script. Instead of cleanly generating and writing Custom Resource Definitions (CRDs) for Azure Service Operator (ASO) into `data/data/cluster-api/azureaso-infrastructure-components.yaml`, the script was appending new CRD definitions to the existing file. This behavior led to the accumulation of duplicate CRDs within the manifest file, violating the principle of idempotency for the verification script.

## Problem Statement

The `hack/verify-capi-manifests.sh` script exhibits non-idempotent behavior, specifically when handling ASO CRDs. When executed, it appends new CRD definitions to `data/data/cluster-api/azureaso-infrastructure-components.yaml` rather than replacing the content. This results in the `azureaso-infrastructure-components.yaml` file containing duplicate ASO CRDs, leading to an inconsistent and bloated manifest. The expected behavior is that running the script should produce no changes if the file is already in its correct state.

## Decision

The `hack/verify-capi-manifests.sh` script has been modified to ensure idempotency. The fix addresses the logic that previously appended ASO CRDs, ensuring that the script now writes the CRDs cleanly, preventing duplication. Concurrently, the existing duplicate entries in `data/data/cluster-api/azureaso-infrastructure-components.yaml` were removed as part of this change, resetting the file to a correct state.

**Code Locations:**
*   `hack/verify-capi-manifests.sh`: Modified to correct the writing logic (+1 -1 lines).
*   `data/data/cluster-api/azureaso-infrastructure-components.yaml`: Cleaned of duplicate CRDs (+0 -927 lines).

## Consequences

### Positive

*   The `hack/verify-capi-manifests.sh` script is now idempotent, ensuring consistent manifest generation.
*   Prevents the re-introduction of duplicate ASO CRDs in `data/data/cluster-api/azureaso-infrastructure-components.yaml`.
*   Ensures the `azureaso-infrastructure-components.yaml` file remains clean and accurately reflects the desired ASO CRD state.
*   Improves the reliability and predictability of the CAPI manifest verification process.

### Negative

*   None identified in the provided context.

### Neutral

*   This change is an implementation detail, completely invisible to end-users.

## Alternatives Considered

No specific alternatives were explicitly discussed or documented in the provided context, as the issue was a direct bug requiring a fix to achieve idempotent behavior.

## References

*   **Jira Ticket