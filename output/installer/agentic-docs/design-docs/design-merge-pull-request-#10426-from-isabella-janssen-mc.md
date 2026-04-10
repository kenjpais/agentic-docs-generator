This document outlines the design for labeling Machine, MachineSet, and ControlPlaneMachineSet resources with OS stream information within the `openshift/installer` repository. This feature, tracked as MCO-2135, is crucial for enabling the Machine Config Operator (MCO) to accurately identify and manage machine resources based on their boot image.

## 🎯 Design Document: MCO-