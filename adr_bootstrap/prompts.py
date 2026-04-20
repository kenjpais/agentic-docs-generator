"""ADR-specific prompt templates (self-contained, no YAML dependency)."""

ADR_GENERATION_SYSTEM = """\
You are an expert software architect analyzing an existing codebase. The decision
you are documenting has ALREADY been made and implemented. Your job is to articulate
it as a decision document: explain what exists in the code, why it was likely chosen
over alternatives, and what risks it carries.

This is an OpenShift {repo_type} repository ({openshift_category}).
Primary language: {primary_language}.

Write for an audience of engineers and AI agents who need to understand WHY the
architecture is the way it is before making changes. Be concrete: reference file
paths, type names, and patterns from the evidence. Do not restate dependency names
from go.mod — focus on the design decisions, patterns, and trade-offs."""

ADR_GENERATION_USER = """\
Analyze the following architectural pattern and generate a decision document.

DECISION AREA: {decision_name}
DECISION TYPE: {decision_type}
OBSERVED PATTERN: {description}

KEY FILES:
{key_files_formatted}

CODE EVIDENCE:
{evidence_formatted}

CODE SNIPPETS (from key files):
{code_snippets}

HISTORICAL CONTEXT:
- Introduced: {introducing_date}
- Introducing commit: {introducing_subject}
- PR description: {pr_description}
- Jira context: {jira_description}

ENHANCEMENT PROPOSAL (if available):
{enhancement_summary}

OWNERS / DECIDERS: {owners}

Generate the ADR using EXACTLY this structure (use these headings):

# [Decision Title]

## Executive Summary
A single paragraph summarizing the decision and its impact.

## What
What components are touched. What is being decided. Short and concrete.

## Why
Motivation and context. What present circumstances require this design.
Why is this important. What problems would arise without it.

## Goals
Bullet list of what the solution achieves.

## Non-Goals
What is explicitly out of scope or not addressed.

## How
Full technical overview of the implemented approach. Be concrete:
- Reference specific file paths and type names from the evidence
- Describe the data flow or control flow
- Explain how components interact
- Mention testing and verification approach if visible in the evidence

## Alternatives
What other approaches could have been taken. For each alternative:
- Describe it briefly
- Explain why it was not chosen (trade-offs, constraints)
Use your knowledge of the {primary_language} and Kubernetes/OpenShift ecosystem.

## Risks
- Execution risks (complexity, maintenance burden)
- Operational risks (failure modes, debugging difficulty)
- Evolution risks (what happens when requirements change)

REQUIREMENTS:
- Do NOT generate YAML frontmatter (it will be injected separately)
- Do NOT wrap output in markdown code fences
- Do NOT restate go.mod dependency entries as content
- Focus on DESIGN DECISIONS, not library choices
- Reference actual file paths from the evidence
- Keep total output under 150 lines"""

ADR_TEMPLATE_CONTENT = """\
---
id: ADR-[number]
title: [Decision Title]
date: YYYY-MM-DD
status: [proposed | accepted | deprecated | superseded]
deciders: [team-name, @username]
supersedes: [ADR-XXX if applicable]
superseded-by: [ADR-XXX if applicable]
---

# [Decision Title]

## Executive Summary
A quick summary of the decision.

## What
Short summary of what decision this document is reaching and what components it touches.

## Why
Motivation behind the change, context, why a decision is needed.

## Goals
- Goal 1
- Goal 2

## Non-Goals
- Non-goal 1

## How
Full overview of the proposed/implemented solution.

## Alternatives
Potential alternatives and why they were not chosen.

## Risks
- Execution risk
- Operational risk
- Customer risk
"""


def build_adr_prompt(context: dict) -> str:
    """Build the full prompt for ADR generation from a context dictionary."""
    system = ADR_GENERATION_SYSTEM.format(**context)
    user = ADR_GENERATION_USER.format(**context)
    return f"{system}\n\n{user}"
