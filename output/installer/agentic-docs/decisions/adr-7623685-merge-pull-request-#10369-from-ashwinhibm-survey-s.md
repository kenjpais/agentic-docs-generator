```markdown
agentic/decisions/adr-7623685-powervs-install-config-short-regions.md
```

# ADR 7623685: PowerVS Install-Config: Use Short Regions and Default Resource Group

## Status

Proposed

## Date

2023-10-27 (Assumed current date)

## Decision Makers

AshwinHIBM

## Context

### Problem

When attempting to create an `install-config` for OpenShift on PowerVS using `openshift-install create install-config --dir test1` with version `4.22.0-ec.3`, the process fails with a `FATAL` error. The error message indicates that a default value, such as `"dal"` or `"au-syd (Sydney (au-syd)) ()"`, is not found in the available options for the `Base Domain` or `Platform` asset generation. This prevents the `install-config.yaml` from being generated, blocking PowerVS cluster deployments.

**Specific Error Messages:**
```
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options
```
and
```
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": failed to survey desired ibmcloud region: default value "au-syd (Sydney (au-syd)) ()" not found in options
```

### Root Cause (Implied)

The `openshift-install` tool's PowerVS platform asset generation logic for surveying regions or selecting default values is not correctly handling the expected region formats or available resource groups, leading to mismatches and failures during the interactive `install-config` creation. Specifically, it appears to be attempting to use long-form region names or missing a default resource group where short-form region names are now expected or preferred.

## Decision

To resolve the `FATAL` error during `install-config` creation for PowerVS, the `openshift-install` tool will be updated to:
1.  Utilize short region names during the PowerVS region survey process.
2.  Provide a default resource group to streamline the `install-config` generation.

This change aims to align the region handling with the expected values, allowing the survey to complete successfully and generate the `install-config.yaml`.

### Implementation Details

The following files will be modified to implement this decision:
*   `pkg/asset/installconfig/powervs/regions.go`: Modifications (+5 -7 lines) to adjust how regions are retrieved and processed, likely to ensure short region names are used.
*   `pkg/asset/installconfig/powervs/session.go`: Modifications (+6 -2 lines) to integrate the default resource group provision and potentially influence how the PowerVS session interacts with region data.

## Consequences

### Positive

*   **Resolved Installation Blocker**: Directly addresses and resolves the `FATAL` error preventing PowerVS `install-config` generation, enabling users to proceed with cluster deployments.
*   **Improved User Experience**: The `install-config` creation process for PowerVS becomes more robust and reliable, avoiding a critical failure point.
*   **Consistency**: Aligns the region handling with potentially updated API expectations or best practices for PowerVS, specifically favoring short region names.

### Negative

*   No explicit negative consequences are identified in the provided context. Potential implicit consequences could involve minor behavioral changes in region selection for users accustomed to a different format, but this is expected to be a net positive.

### Neutral

*   Refactoring of internal PowerVS asset generation logic.

## Alternatives

Not explicitly discussed in the provided context. The solution directly addresses the identified problem with a focused code change.

## References

*   **Jira Issue**: OCPBUGS-77917: PowerVS: Creating Install Config with ec.3 Generates FATAL Error
*   **Pull Request**: #7623685: OCPBUGS-77917: PowerVS: Use short regions and provide a default resource group in survey
*   **Modified Files**:
    *   `pkg/asset/installconfig/powervs/regions.go`
    *   `pkg/asset/installconfig/powervs/session.go`
```