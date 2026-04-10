# Execution Plan: MCO-2135: Label Machines, MachineSets, and ControlPaneMachineSets with OSStream labels

## Overview

**Related PR:** #10426
**Jira Ticket:** MCO-2135

This adds a `"machineconfiguration.openshift.io/osstream"` label to `MachineSet.Metadata.Labels`, `MachineSet.Spec.Template.Metadata.Labels`, `Machine.Metadata.Labels`, `ControlPlaneMachineSet.ObjectMeta.Labels`, and `ControlPlaneMachineSet.Spec.Template.OpenShiftMachineV1Beta1Machine.ObjectMeta.Labels` for all install platforms. Note that the ControlPaneMachineSet labels were only added for aws, azure, gcp, nutanix, openstack, powerVS, and vSphere since not all platforms support the resource type.

## Problem Statement

With https://redhat.atlassian.net/browse/MCO-2133, the installer will become aware of the boot image being selected for each machine resource. This should be placed as label/annotation on every machine and machineset resource so that the MCO can distinguish between what resources to manage and what resources to leave alone.

## Acceptance Criteria

*   Verify that `MachineSet.Metadata.Labels` includes the `machineconfiguration.openshift.io/osstream` label with the correct OSStream value on all supported install platforms.
*   Verify that `MachineSet.Spec.Template.Metadata.Labels` includes the `machineconfiguration.openshift.io/osstream` label with the correct OSStream value on all supported install platforms.
*   Verify that `Machine.Metadata.Labels` includes the `machineconfiguration.openshift.io/osstream` label with the correct OSStream value on all supported install platforms.
*   Verify that `ControlPlaneMachineSet.ObjectMeta.Labels` includes the `machineconfiguration.openshift.io/osstream` label with the correct OSStream value specifically for AWS, Azure, GCP, Nutanix, OpenStack, PowerVS, and vSphere platforms.
*   Verify that `ControlPlaneMachineSet.Spec.Template.OpenShiftMachineV1Beta1Machine.ObjectMeta.Labels` includes the `machineconfiguration.openshift.io/osstream` label with the correct OSStream value specifically for AWS, Azure, GCP, Nutanix, OpenStack, PowerVS, and vSphere platforms.
*   Confirm no regression in existing machine provisioning or cluster functionality across any platform.
*   Successful execution of the MCO's disruptive test suites (with https://