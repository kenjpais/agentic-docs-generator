```markdown
---
title: CORS-3900 - Add IPv6 frontend IP configurations for dual-stack
status: completed
date: 2024-07-30
authors: [Your Name/Team] # Replace with actual author(s)
pr: https://github.com/rna-afk/azure_dualstack_add_frontend/pull/5385384
jira: https://issues.redhat.com/browse/CORS-3900
feature_gate: N/A
design_doc: N/A
---

## Problem Statement

As a user, I want to be able to provision OpenShift clusters on Azure with dual-stack networking capabilities, specifically including IPv6 frontend IP configurations. This will allow the cluster to communicate and expose services over both IPv4 and IPv6, enabling broader network compatibility and future-proofing.

## Solution Summary

This feature implements the necessary changes in the Azure infrastructure provisioning logic to support IPv6 frontend IP configurations for dual-stack clusters. This involves modifications to how Public IP Addresses and Load Balancer frontend IP configurations are created and managed within the `pkg/infrastructure/azure` component, ensuring that both IPv4 and IPv6 addresses are provisioned concurrently when dual-stack is enabled.

## Implementation Steps

The implementation focused on extending existing Azure resource management functions to accommodate IPv6, primarily within the `pkg/infrastructure/azure/network.go` and `pkg/infrastructure/azure/azure.go` files.

1.  **Extend Network Resource Creation for IPv6 in `pkg/infrastructure/azure/network.go`**:
    *   **Public IP Address Management**: Modified functions responsible for creating and managing Azure Public IP Addresses to allow specifying the IP version (IPv4 or IPv6). This involved adding parameters or logic to differentiate between the two, ensuring that IPv6 Public IPs can be provisioned alongside IPv4 ones for dual-stack scenarios.
