"""Prompt templates for Gemini LLM to generate documentation."""

# ADR Template - Update this based on agentic-docs-guide structure
ADR_TEMPLATE = """
# Architecture Decision Record (ADR)

## Context and Problem Statement

{problem}

## Decision Drivers

* Feature requirements from Jira ticket: {jira_key}
* Technical constraints and existing architecture
* Implementation feasibility and maintainability

## Considered Options

Based on the implementation in PR #{pr_number}, the following approach was taken:

## Decision Outcome

**Chosen option:** {feature_title}

### Implementation Details

{solution_summary}

### Technical Changes

{code_changes}

### Consequences

**Positive:**
* Addresses the requirements outlined in {jira_key}
* Maintains consistency with existing codebase patterns

**Negative:**
* [To be determined based on monitoring and feedback]

## Additional Context

### Jira Ticket Information
- **Title:** {jira_title}
- **Key:** {jira_key}
- **Acceptance Criteria:**
{acceptance_criteria}

### Code Changes Summary
- **Files Modified:** {files_count}
- **Lines Added:** {additions}
- **Lines Deleted:** {deletions}

### Key Discussions
{key_discussions}

## Links

* Pull Request: #{pr_number}
* Jira Ticket: {jira_key}
"""

# Execution Plan Template - Update this based on agentic-docs-guide structure
EXEC_PLAN_TEMPLATE = """
# Execution Plan: {feature_title}

## Overview

**Related PR:** #{pr_number}
**Jira Ticket:** {jira_key}

{solution_summary}

## Problem Statement

{problem}

## Acceptance Criteria

{acceptance_criteria}

## Implementation Steps

Based on the code changes in this PR, the implementation followed these steps:

### 1. Analysis and Planning
- Reviewed requirements from {jira_key}
- Identified affected components and files
- Planned implementation approach

### 2. Code Changes
{code_changes}

### 3. Files Modified
{modified_files}

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
- **Total Files Modified:** {files_count}
- **Lines Added:** {additions}
- **Lines Deleted:** {deletions}

### Key Components Affected
{affected_components}

## Dependencies

- Related tickets: [List any dependencies mentioned in Jira]
- External dependencies: [Any new libraries or services]

## Rollback Plan

In case of issues:
1. Revert PR #{pr_number}
2. Monitor for any data inconsistencies
3. Re-evaluate implementation approach

## Success Metrics

- All acceptance criteria met
- No regression in existing functionality
- Performance within acceptable parameters

## Key Discussions and Decisions

{key_discussions}

## References

* Pull Request: #{pr_number}
* Jira Ticket: {jira_key}
"""


class PromptBuilder:
    """Builds prompts for Gemini LLM."""

    def build_adr_prompt(self, context: dict) -> str:
        """
        Build ADR generation prompt.

        Args:
            context: Feature context dictionary

        Returns:
            Formatted prompt string
        """
        jira_context = context.get('jira_context', {})

        system_instruction = (
            "You are an expert software architect. Generate a detailed and precise "
            "Architectural Decision Record (ADR) based on the provided context. "
            "Use only the information provided. Do not hallucinate or add speculative details. "
            "Be technical and specific."
        )

        user_prompt = f"""Generate an ADR using the following template and context:

TEMPLATE:
{ADR_TEMPLATE}

CONTEXT:
- Feature Title: {context.get('feature_title', 'N/A')}
- PR Number: {context.get('pr_number', 'N/A')}
- Jira Key: {context.get('jira_key', 'N/A')}
- Jira Title: {jira_context.get('title', 'N/A')}
- Problem: {context.get('problem', 'N/A')}
- Solution Summary: {context.get('solution_summary', 'N/A')}
- Code Changes: {context.get('code_changes', 'N/A')}
- Acceptance Criteria: {jira_context.get('acceptance_criteria', 'N/A')}
- Files Modified: {len(context.get('files_modified', []))}
- Total Additions: {context.get('total_additions', 0)}
- Total Deletions: {context.get('total_deletions', 0)}
- Key Discussions: {jira_context.get('key_discussions', 'None')}

CONSTRAINTS:
- Follow the template structure exactly
- Be precise and technical
- Use only the provided context
- Do not add speculative or generic statements
- Include specific file names and technical details where available
"""

        return f"{system_instruction}\n\n{user_prompt}"

    def build_exec_plan_prompt(self, context: dict) -> str:
        """
        Build execution plan generation prompt.

        Args:
            context: Feature context dictionary

        Returns:
            Formatted prompt string
        """
        jira_context = context.get('jira_context', {})
        files_modified = context.get('files_modified', [])
        modified_files_str = '\n'.join([f"- {f}" for f in files_modified])

        # Extract affected components from file paths
        affected_components = self._extract_components(files_modified)

        system_instruction = (
            "You are an expert engineering planner. Generate a detailed execution plan "
            "based on the actual implementation reflected in the pull request. "
            "Use only the provided context. Be specific about implementation steps, "
            "technical decisions, and testing approach."
        )

        user_prompt = f"""Generate an execution plan using the following template and context:

TEMPLATE:
{EXEC_PLAN_TEMPLATE}

CONTEXT:
- Feature Title: {context.get('feature_title', 'N/A')}
- PR Number: {context.get('pr_number', 'N/A')}
- Jira Key: {context.get('jira_key', 'N/A')}
- Problem: {context.get('problem', 'N/A')}
- Solution Summary: {context.get('solution_summary', 'N/A')}
- Code Changes: {context.get('code_changes', 'N/A')}
- Acceptance Criteria: {jira_context.get('acceptance_criteria', 'N/A')}
- Files Modified: {len(files_modified)}
- Modified Files List:
{modified_files_str}
- Total Additions: {context.get('total_additions', 0)}
- Total Deletions: {context.get('total_deletions', 0)}
- Affected Components: {affected_components}
- Key Discussions: {jira_context.get('key_discussions', 'None')}

REQUIREMENTS:
- Follow the template structure exactly
- Break down implementation into clear, specific steps
- Include actual technical details from the code changes
- Align with the PR changes and Jira requirements
- Avoid generic or boilerplate statements
"""

        return f"{system_instruction}\n\n{user_prompt}"

    def _extract_components(self, file_paths: list) -> str:
        """Extract component names from file paths."""
        if not file_paths:
            return "N/A"

        components = set()
        for path in file_paths:
            parts = path.split('/')
            if len(parts) > 1:
                # Assume first directory is component/module name
                components.add(parts[0])

        return ', '.join(sorted(components)) if components else "N/A"
