```markdown
# ADR 5385384: Dual frontend IP configuration support for public load balancer

## Metadata
* Status: Completed
* Date: 2023-10-27
* Decision Makers: OpenShift Infrastructure Team
* Related Tickets:
    * Jira: [CORS-3900](https://issues.redhat.com/CORS-3900)
    * PR: [#5385384](https://github.com/rna-afk/azure_dualstack_add_frontend/pull/5385384)

## Context and Problem Statement
OpenShift clusters deployed on Azure require support for dual-stack networking configurations, specifically for public load balancers. The current implementation lacks the ability to configure both IPv4 and IPv6 frontend IP configurations, hindering the adoption of dual-stack capabilities.

The user story from CORS-3900 outlines the need:
As a (user persona), I want to be able to:
 * Capability 1
 * Capability 2
 * Capability 3
so that I can achieve
 * Outcome 1
 * Outcome 2
 * Outcome 3

## Decision
To implement support for dual frontend IP configurations (IPv4 and IPv6) for public load balancers within the Azure infrastructure management code. This involves adding IPv6 frontend IP configurations to enable dual-stack functionality.

## Rationale
This decision directly addresses the requirement for dual-stack support in Azure public load balancers, as specified in Jira ticket CORS-3900. By modifying the Azure infrastructure code, we enable OpenShift clusters to leverage IPv6 capabilities and dual-stack networking, fulfilling the outlined user story and acceptance criteria. This approach integrates the necessary configuration directly into the existing infrastructure provisioning logic