```markdown
# adr-10369-powervs-default-region-resource-group-survey

## Status

Date: 2023-10-27
Status: Completed
Decision Makers: N/A

## Context

The `openshift-install create install-config` command for the PowerVS platform fails fatally when attempting to generate the `install-config.yaml`. This occurs specifically during the interactive survey for selecting the IBM Cloud region and resource group.

The observed fatal errors are:
- `FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": default value "dal" not found in options`
- `FATAL failed to fetch Install Config: failed to fetch dependency of "Install Config": failed to fetch dependency of "Base Domain": failed to generate asset "Platform": failed to survey desired ibmcloud region: default value "au-syd (Sydney (au-syd)) ()" not found in options`

This issue is reproducible every time with OpenShift installer version `4.22.0-ec.3`. The root cause is that the underlying `survey` library, as referenced by `https://github.com/AlecAivazis/survey/blob/master/select.go#L232:L238`, expects any default value provided for a selection prompt to be explicitly present within the list of options presented to the user. The existing PowerVS asset generation for regions and resource groups did not guarantee this, leading to a mismatch and the fatal error.

## Decision

The decision is to modify the PowerVS install config asset generation logic to ensure that any default region and resource group values are explicitly included in the list of options presented to the user during the interactive `openshift-install create install-config` survey. This ensures compliance with the `survey` library's expectation that a default option