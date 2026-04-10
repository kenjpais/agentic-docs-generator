Here is a clear, LLM-friendly, step-by-step prototype design and build plan based on your requirements:

---

## 1. Project Overview

Build a Python application that generates agentic documentation (ADRs and execution plans) for Red Hat OpenShift repositories by combining:

* GitHub data (PRs, commits, code changes)
* Linked Jira artifacts (tickets, descriptions, discussions)

The generated documentation must strictly follow the structure defined in:
[https://github.com/Prashanth684/agentic-docs-guide/](https://github.com/Prashanth684/agentic-docs-guide/)

Gemini will be used as the LLM for content generation.

---

## 2. High-Level Architecture

The system is composed of the following modules:

1. Data Ingestion Layer

   * GitHub Connector
   * Jira Connector

2. Data Correlation Layer

   * PR ↔ Jira mapping
   * Feature grouping (latest merged features)

3. Processing Layer

   * Feature summarization
   * Context builder (code + PR + Jira)

4. Prompt Builder

   * Structured prompt templates for ADRs and exec plans

5. LLM Interface

   * Gemini API integration

6. Documentation Generator

   * ADR generator
   * Exec-plan generator
   * Output formatter (strictly following guide)

7. Storage Layer

   * Local filesystem (prototype)
   * Optional JSON cache

---

## 3. Data Model (Core Objects)

Define simple Python classes:

* Repository

  * name
  * owner

* PullRequest

  * id
  * title
  * description
  * merged_at
  * files_changed
  * jira_id

* JiraTicket

  * id
  * title
  * description
  * acceptance_criteria
  * comments

* Feature

  * pr
  * jira
  * summary_context

---

## 4. Step-by-Step Build Plan

### Step 1: Project Setup

* Create Python project

* Install dependencies:

  * requests or httpx
  * PyGithub
  * jira (atlassian-python-api or similar)
  * google-generativeai (Gemini SDK)
  * pydantic (optional for structured models)

* Setup environment variables:

  * GITHUB_TOKEN
  * JIRA_API_TOKEN
  * JIRA_BASE_URL
  * GEMINI_API_KEY

---

### Step 2: GitHub Ingestion Module

Implement:

* fetch_merged_prs(repo, limit=10)
* fetch_pr_details(pr_id)
* fetch_changed_files(pr_id)

Logic:

* Retrieve latest merged PRs
* Extract:

  * title
  * description
  * changed files (file paths and diffs)
* Parse Jira ID from:

  * PR title (e.g., ABC-123)
  * branch name
  * PR description

Output: List[PullRequest]

---

### Step 3: Jira Ingestion Module

Implement:

* fetch_jira_ticket(jira_id)

Extract:

* title
* description
* acceptance criteria
* comments/discussion

Output: JiraTicket

---

### Step 4: Data Correlation

Implement:

* link_prs_to_jira(pr_list)

Logic:

* For each PR:

  * Extract jira_id
  * Fetch Jira ticket
* Filter:

  * Only PRs with valid Jira links
* Group as Features

Output: List[Feature]

---

### Step 5: Feature Context Builder

Implement:

* build_feature_context(feature)

Context should include:

* PR summary
* Code changes (summarized)
* Jira description
* Acceptance criteria
* Key decisions inferred

Keep it structured:

{
"feature_title": "",
"problem": "",
"solution_summary": "",
"code_changes": "",
"jira_context": ""
}

---

### Step 6: Prompt Design for Gemini

Define strict prompt templates aligned to the agentic-docs-guide.

#### ADR Prompt Template

System instruction:

"You are an expert software architect. Generate an Architectural Decision Record strictly following the provided structure. Do not deviate."

User prompt template:

"Generate an ADR using the following structure from the agentic docs guide:

[PASTE ADR STRUCTURE TEMPLATE HERE EXACTLY]

Input Context:

* Feature Title: {feature_title}
* Problem: {problem}
* Solution Summary: {solution_summary}
* Code Changes: {code_changes}
* Jira Context: {jira_context}

Constraints:

* Be precise and technical
* Do not hallucinate missing details
* Use only provided context
* Follow headings exactly"

---

#### Exec Plan Prompt Template

System instruction:

"You are an expert engineering planner. Generate a detailed execution plan strictly following the required structure."

User prompt template:

"Generate an execution plan using the following structure:

[PASTE EXEC PLAN STRUCTURE FROM GUIDE]

Input Context:

* Feature Title: {feature_title}
* Problem: {problem}
* Solution Summary: {solution_summary}
* Code Changes: {code_changes}
* Jira Context: {jira_context}

Requirements:

* Break into clear steps
* Include implementation details
* Align with actual PR changes
* Avoid generic statements"

---

### Step 7: Gemini Integration

Implement:

* generate_with_gemini(prompt)

Steps:

* Initialize Gemini client
* Use model (e.g., gemini-pro)
* Send prompt
* Capture response text

Add retry + error handling.

---

### Step 8: Documentation Generator

Implement:

* generate_adr(feature)
* generate_exec_plan(feature)

Flow:

1. Build context
2. Fill prompt template
3. Call Gemini
4. Validate output structure (basic checks)
5. Return formatted text

---

### Step 9: Output Formatter

Store outputs as:

* /output/

  * /repo-name/

    * /feature-1/

      * adr.md
      * exec-plan.md

Ensure:

* Markdown formatting
* Headings match guide exactly

---

### Step 10: CLI Interface

Create simple CLI:

Commands:

* python main.py --repo <repo_name>

Flow:

1. Fetch PRs
2. Link Jira
3. Build features
4. Generate docs
5. Save output

---

## 5. Workflow End-to-End

1. User provides repository name
2. System fetches latest merged PRs
3. Extract Jira IDs
4. Fetch Jira tickets
5. Build unified feature context
6. Generate ADR via Gemini
7. Generate exec plan via Gemini
8. Save documentation locally

---

## 6. Extensibility Design

Ensure:

* Modular connectors (GitHub/Jira interchangeable)
* Prompt templates stored separately (editable)
* LLM provider abstraction (Gemini replaceable)
* Feature filters (date, labels, teams)

Future extensions:

* UI dashboard
* Multi-repo support
* Vector DB for historical context
* Continuous documentation generation pipeline

---

## 7. LLM-Friendliness Considerations

* Use deterministic prompt templates
* Keep inputs structured and bounded
* Avoid raw code dumps; summarize changes
* Enforce output structure via explicit templates
* Validate outputs post-generation

---

## 8. Minimal File Structure

project/

* main.py
* github_client.py
* jira_client.py
* models.py
* context_builder.py
* prompt_templates.py
* gemini_client.py
* doc_generator.py
* utils.py
* output/

---

This design is intentionally simple, modular, and directly executable by a coding agent while remaining extensible for future enhancements.

