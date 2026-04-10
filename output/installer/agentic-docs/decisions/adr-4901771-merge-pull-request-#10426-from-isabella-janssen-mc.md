```markdown
# ADR-4901771: Label Machine Resources with OSStream for MCO Management

## Status
Completed

## Context
With the implementation of MCO-2133, the installer now identifies the specific boot image selected for each machine resource. The Machine Config Operator (MCO) requires a mechanism to differentiate between machine resources it is responsible for managing and those it should ignore. This distinction is critical for the MCO to operate correctly and avoid unintended modifications to unmanaged resources.

## Decision
The architectural decision is to label `Machine`, `MachineSet`, and `ControlPlaneMachineSet` resources with `OSStream` labels or annotations. These labels will explicitly indicate the selected boot image stream, enabling the MCO to identify and manage only the relevant resources. This approach provides a clear, machine-readable signal for MCO's operational logic.

## Consequences
*   **Positive:**
    *   Enables the MCO to accurately distinguish and manage machine resources based on their associated boot image stream, preventing interference with unmanaged resources.
    *   Addresses and facilitates the closure of OCPBUGS-79522 as "not a bug," indicating that the intended functionality is now correctly implemented.
    *   Provides a foundation for MCO regression tests to verify installer changes across various cloud providers and baremetal environments (e.g., AWS, Azure, Baremetal, GCP).
*   **Negative:**
    *   None explicitly identified in the provided context.
*   **Neutral:**
    *   The implementation involves modifications across numerous provider-specific machine asset generation files, ensuring consistent application of labels.
    *   The installer work for this change has landed, with MCO tests serving as the primary outstanding verification.

## Code References
The following files were modified to implement this decision, primarily within the `pkg/asset/machines` directory to apply labels during resource generation:

*   `pkg/asset/machines/aws/awsmachines.go`
*   `pkg/asset/machines/aws/machines.go`