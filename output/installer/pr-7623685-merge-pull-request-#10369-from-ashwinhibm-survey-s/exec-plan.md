# Execution Plan: PowerVS: Use short regions and provide a default resource group in survey

## Overview

**Related PR:** #7623685
**Jira Ticket:** OCPBUGS-77917

OCPBUGS-77917: PowerVS: Use short regions and provide a default resource group in survey

## Problem Statement

```
[root@jumpbox-pbastide install-pvs]# ./openshift-install create install-config --dir test1
? SSH Public Key /root/.ssh/id_rsa.pub
? Platform powervs
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options 
```
Version-Release number of selected component (if applicable):
```
    4.22.0-ec.3
```
How reproducible:
```
    Every Time
```
Steps to Reproduce:
```
    1. Download ec.3 ppc64le binary
    2. Try the install-config creation metaphor
    3. Fails with Fatal
```
Actual results:
```
    FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": failed to survey desired ibmcloud region: default value "au-syd (Sydney (au-syd)) ()" not found in options

[root@jumpbox-pbastide install-pvs]# ./openshift-install create install-config --dir test1
? SSH Public Key /root/.ssh/id_rsa.pub
? Platform powervs
FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options
```
Expected results:
```
  Survey continues to generate install-config.yaml
```
Additional info:
```
    
```

## Acceptance Criteria

*   The `openshift-install create install-config` command for the PowerVS platform completes successfully without a `FATAL` error related to the region default value.
*   The region selection in the `install-config` survey correctly uses short region codes (e.g., "dal", "