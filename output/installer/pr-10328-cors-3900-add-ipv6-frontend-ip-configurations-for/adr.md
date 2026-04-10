# Architecture Decision Record (ADR)

## Context and Problem Statement

User Story:
As a (user persona), I want to be able to:
* Capability 1
* Capability 2
* Capability 3
so that I can achieve
* Outcome 1
* Outcome 2
* Outcome 3

## Decision Drivers

* Feature requirements from Jira ticket: CORS-3900
* Technical constraints and existing architecture
* Implementation feasibility and maintainability

## Considered Options

Based on the implementation in PR #10328, the following approach was taken:

## Decision Outcome

**Chosen option:** CORS-3900: Add IPv6 frontend IP configurations for dual-stack

### Implementation Details

Adding IPv6 public IP creation and frontend IP configurations on external load balancers and adding IPv6 frontend IP to CAPZ apiServerLB manifest. Also adding IPv6 NAT rule for bootstrap SSH access and updating NAT rules to the correct IP version on the bootstrap NIC.

Specifically, this includes:
*   Added IPv6 dual-stack support for Azure infrastructure, enabling IPv6 frontend allocation on internal and external load balancers when dual-stack is enabled.
*   Enhanced public IP allocation and management with IPv6 support.
*   Improved load balancer configuration with dual-stack IPv4/IPv6 frontend handling for API and internal load balancers.

### Technical Changes

Code Changes Summary:
2 go file(s): +278 -86 lines

Modified Files:
  - pkg/infrastructure/azure/azure.go: +70 -5
  - pkg/infrastructure/azure/network.go: +208 -81

### Consequences

**Positive:**
* Addresses the requirements outlined in CORS-3900
* Maintains consistency with existing codebase patterns

**Negative:**
* [To be determined based on monitoring and feedback]

## Additional Context

### Jira Ticket Information
- **Title:** Dual frontend IP configuration support for public load balancer
- **Key:** CORS-3900
- **Acceptance Criteria:**
Description of criteria:
 * Upstream documentation
 * Point 1
 * Point 2
 * Point 3

Out of Scope:
Detail about what is specifically not being delivered in the story

Engineering Details:
 * (optional) [https://github/com/link.to.enhancement/]
 * (optional) [https://issues.redhat.com/link.to.spike]
 * Engineering detail 1
 * Engineering detail 2
(?) This requires/does not require a design proposal.
(?) This requires/does not require a feature gate.

### Code Changes Summary
- **Files Modified:** 2
- **Lines Added:** 278
- **Lines Deleted:** 86

### Key Discussions
No discussions

## Links

* Pull Request: #10328
* Jira Ticket: CORS-3900