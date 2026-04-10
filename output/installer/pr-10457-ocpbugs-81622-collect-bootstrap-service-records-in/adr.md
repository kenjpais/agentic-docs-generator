# Architecture Decision Record (ADR)

## Context and Problem Statement

While bootstrapping, bootkube stores debugging information in /var/log/openshift to record progress. We should collect this in agent-gather.

## Decision Drivers

* Feature requirements from Jira ticket: OCPBUGS-81622
* Technical constraints and existing architecture
* Implementation feasibility and maintainability

## Considered Options

Based on the implementation in PR #10457, the following approach was taken:

## Decision Outcome

**Chosen option:** OCPBUGS-81622: Collect bootstrap service records in agent-gather

### Implementation Details


### Technical Changes

Code Changes Summary:
1 other file(s): +12 -1 lines

Modified Files:
  - data/data/agent/files/usr/local/bin/agent-gather: +12 -1

### Consequences

**Positive:**
* Addresses the requirements outlined in OCPBUGS-81622
* Maintains consistency with existing codebase patterns

**Negative:**
* [To be determined based on monitoring and feedback]

## Additional Context

### Jira Ticket Information
- **Title:** agent-gather should collect bootstrap service records
- **Key:** OCPBUGS-81622
- **Acceptance Criteria:**

### Code Changes Summary
- **Files Modified:** 1
- **Lines Added:** 12
- **Lines Deleted:** 1

### Key Discussions
No discussions

## Links

* Pull Request: #10457
* Jira Ticket: OCPBUGS-81622