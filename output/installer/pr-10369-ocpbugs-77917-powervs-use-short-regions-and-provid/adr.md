# Architecture Decision Record (ADR)

## Context and Problem Statement

When attempting to create an `install-config` for the PowerVS platform using `./openshift-install create install-config` with OpenShift version `4.22.0-ec.3`, the process fails with a `FATAL` error. Specifically, the error indicates that a default value for the IBM Cloud region (e.g., "dal" or "au-syd (Sydney (au-syd)) ()") is not found within the available options presented during the platform survey. This prevents the `install-config.yaml` from being generated, effectively blocking the installation process for PowerVS.

Example error:
```
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options
```
or
```
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": failed to survey desired ibmcloud region: default value "au-syd (Sydney (au-syd)) ()" not found in options
```

## Decision Drivers

*   Feature requirements from Jira ticket: OCPBUGS-77917
*   Technical constraints and existing architecture: The underlying `survey` library expects any default option to be explicitly present within the list of options provided to the user, as per `https://github.com/AlecAivazis/survey/blob/master/select.go#L232:L238`. The current implementation for PowerVS regions did not consistently ensure this, leading to the FATAL error.
*   Implementation feasibility and maintainability

## Considered Options

Based on the implementation in PR #10369, the following approach was taken: The existing PowerVS region and resource group survey logic was modified to ensure that the default values presented to the user are always part of the available options.

## Decision Outcome

**Chosen option:** OCPBUGS-77917: PowerVS: Use short regions and provide a default resource group in survey

### Implementation Details

The solution involves modifying the PowerVS asset generation logic to ensure that default region and resource group values are consistently included in the list of options presented to the user during the `openshift-install` survey. This aligns with the `survey` library's expectation that a default option must be discoverable within the provided choices.

### Technical Changes

The changes primarily affect the PowerVS asset generation code, specifically concerning how regions and sessions are handled.
*   **Files Modified:** 2 go file(s)
*   **Lines Added:** +11
*   **Lines Deleted:** -9

Modified Files:
*   `pkg/asset/installconfig/powervs/regions.go`: +5 -7
*   `pkg/asset/installconfig/powervs/session.go`: +6 -2

### Consequences

**Positive:**
*   Addresses the requirements outlined in OCPBUGS-77917 by resolving the FATAL error during `install-config` creation for Power