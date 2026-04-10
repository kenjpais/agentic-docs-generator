# Architecture Decision Record (ADR)

## Context and Problem Statement

When creating an install-config for PowerVS using `openshift-install create install-config --dir test1` with `Platform powervs` and OpenShift version `4.22.0-ec.3`, the process fails with a `FATAL` error. The error indicates that a default region value, such as "dal" or "au-syd (Sydney (au-syd)) ()", is not found in the available options when surveying desired IBM Cloud regions.

Specifically, the observed errors are:
```
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options
```
or
```
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": failed to survey desired ibmcloud region: default value "au-syd (Sydney (au-syd)) ()" not found in options
```
The expected behavior is for the survey to continue and generate the `install-config.yaml`.

## Decision Drivers

* Feature requirements from Jira ticket: OCPBUGS-77917
* Technical constraints and existing architecture
* Implementation feasibility and maintainability

## Considered Options

Based on the implementation in PR #7623685, the following approach was taken:

## Decision Outcome

**Chosen option:** OCPBUGS-77917: PowerVS: Use short regions and provide a default resource group in survey

### Implementation Details

The solution addresses the PowerVS install-config creation failure by modifying the survey process to use short region names and provide a default resource group. This change prevents the `FATAL` error caused by the installer not finding expected region values.

### Technical Changes

The changes involve modifications to two Go files:
*   `pkg/asset/installconfig/powervs/regions.go`: +5 lines, -7 lines
*   `pkg/asset/installconfig/powervs/session.go`: +6 lines, -2 lines

These modifications likely update how PowerVS regions are enumerated or validated, and how a default resource group is handled during the install-config generation survey.

### Consequences

**Positive:**
* Addresses the requirements outlined in OCPBUGS-77917
* Maintains consistency with existing codebase patterns

**Negative:**
* [To be determined based on monitoring and feedback]

## Additional Context

### Jira Ticket Information
- **Title:** PowerVS: Creating Install Config with ec.3 Generates FATAL Error
- **Key:** OCPBUGS-77917
- **Acceptance Criteria:**

### Code Changes Summary
- **Files Modified:** 2
- **Lines Added:** 11
- **Lines Deleted:** 9

### Key Discussions
No discussions

## Links

* Pull Request: #7623685
* Jira Ticket: OCPBUGS-77917