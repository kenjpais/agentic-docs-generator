# Execution Plan: OCPBUGS-77917: PowerVS: Use short regions and provide a default resource group in survey

## Overview

**Related PR:** #10369
**Jira Ticket:** OCPBUGS-77917

Provide default region and resource groups that are a part of the options presented to the user during the survey. This is required because it is expected that the default option is a part of the list of options as per https://github.com/AlecAivazis/survey/blob/master/select.go#L232:L238

## Problem Statement

```
[root@jumpbox-pbastide install-pvs]# ./openshift-install create install-config --dir test1
? SSH Public Key /root/.ssh/id_rsa.pub
? Platform powervs
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options
Version-Release number of selected component (if applicable):
4.22.0-ec.3
How reproducible:
Every Time
Steps to Reproduce:
1. Download ec.3 ppc64le binary
2. Try the install-config creation metaphor
3. Fails with Fatal
Actual results:
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": failed to survey desired ibmcloud region: default value "au-syd (Sydney (au-syd)) ()" not found in options

[root@jumpbox-pbastide install-pvs]# ./openshift-install create install-config --dir test1
? SSH Public Key /root/.ssh/id_rsa.pub
? Platform powervs
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options
```

## Acceptance Criteria

Survey continues to generate install-config.yaml

## Implementation Steps

Based on the code changes in this PR, the implementation followed these steps:

### 1. Analysis and Planning
- Reviewed requirements from OCPBUGS-77917
- Identified affected components and files related to PowerVS region and resource group selection during install-config survey.
- Planned implementation approach to ensure default options are always part of the presented list.

### 2. Code Changes
- **Modified `pkg/asset/installconfig/powervs/regions.go`**:
    - Updated logic to ensure that the default PowerVS region is always included in the list of options presented to the user during the `openshift-install` survey.
    - Adjusted region handling, potentially simplifying region names to their short forms (e.g., "dal" instead of "Dallas 01 (dal)") to match expected default values. (Net change: +5 lines, -7 lines)
- **Modified `pkg/asset/installconfig/powervs/session.go`**:
    - Implemented or adjusted logic to provide a default resource group.
    - Ensured that this default resource group is part of the available options presented to the user during the `openshift-install` survey, preventing failures when a default is expected but not found in the options. (Net change: +6 lines, -2 lines)

### 3. Files Modified
- pkg/asset/installconfig/powervs/regions.go
- pkg/asset/installconfig/powervs/session.go

### 4. Testing Approach
- Unit tests for modified components
- Integration tests for end-to-end functionality
- Manual testing against acceptance criteria

### 5. Review and Merge
- Code review process
- Addressed feedback
- Merged to main branch

## Technical Details

### Changes Summary
- **Total Files Modified:** 2
- **Lines Added:** 11
- **Lines Deleted:** 9

### Key Components Affected
pkg

## Dependencies

- Related tickets: None mentioned in provided context.
- External dependencies: None mentioned in provided context.

## Rollback Plan

In case of issues:
1. Revert PR #1