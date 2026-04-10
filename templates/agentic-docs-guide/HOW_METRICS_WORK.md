# How Metrics Scripts Work

Visual guide to understanding navigation depth and context budget measurement.

---

## 1. measure-navigation-depth.py

**Purpose**: Ensures all documentation is reachable from AGENTS.md in ≤3 hops (links).

**Algorithm**: Breadth-First Search (BFS) through markdown links

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Start at Entry Point                                    │
└─────────────────────────────────────────────────────────────────┘

    AGENTS.md (depth 0)
    │
    │ Parse markdown, extract links: [text](path.md)
    │
    ├─→ ARCHITECTURE.md (depth 1)
    ├─→ agentic/DESIGN.md (depth 1)
    └─→ agentic/domain/index.md (depth 1)

┌─────────────────────────────────────────────────────────────────┐
│ Step 2: BFS Traversal (Level-by-Level)                          │
└─────────────────────────────────────────────────────────────────┘

Depth 0:  [AGENTS.md]
           │
           ├─→ Parse links → Queue: [ARCHITECTURE.md, DESIGN.md, domain/index.md]
           │
Depth 1:  [ARCHITECTURE.md] [DESIGN.md] [domain/index.md]
           │
           ├─→ Parse links from each → Queue: [core-beliefs.md, concepts/X.md, ...]
           │
Depth 2:  [core-beliefs.md] [concepts/machine-config.md] [...]
           │
           ├─→ Parse links → Queue: [machine-config-overview.md, ...]
           │
Depth 3:  [machine-config-overview.md] [...]
           │
           └─→ Parse links → Queue: [deeply-nested-doc.md]

Depth 4:  [deeply-nested-doc.md]  ⚠️ VIOLATION (>3 hops)

┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Track Reachability                                      │
└─────────────────────────────────────────────────────────────────┘

reachable_docs = {
    'AGENTS.md': 0,
    'ARCHITECTURE.md': 1,
    'agentic/DESIGN.md': 1,
    'agentic/domain/index.md': 1,
    'agentic/domain/concepts/machine-config.md': 2,
    'agentic/domain/concepts/machine-config-overview.md': 3,
    'agentic/some-deep-doc.md': 4  # ❌ >3 hops
}

unreachable_docs = [
    'agentic/orphaned-doc.md'  # ❌ Never linked from AGENTS.md chain
]

┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Report Violations                                       │
└─────────────────────────────────────────────────────────────────┘

✅ PASSED if:
   - All expected docs are reachable (0-3 hops)
   - No unreachable docs found

❌ FAILED if:
   - Any doc requires >3 hops from AGENTS.md
   - Any expected doc is unreachable (orphaned)
```

### Example Output

```
Navigation Depth Analysis
=========================

Entry point: AGENTS.md

Reachability Graph:
  Depth 0 (1 docs): AGENTS.md
  Depth 1 (3 docs): ARCHITECTURE.md, DESIGN.md, domain/index.md
  Depth 2 (8 docs): core-beliefs.md, concepts/machine-config.md, ...
  Depth 3 (12 docs): machine-config-overview.md, adr-0001.md, ...

⚠️ Violations:
  Depth 4 (1 doc): agentic/some-deep-doc.md

❌ Unreachable (1 doc):
  - agentic/orphaned-doc.md

Result: ❌ FAILED (1 deep, 1 unreachable)
```

---

## 2. measure-context-budget.py

**Purpose**: Measures how many lines agents load for common workflows (target: ≤700 lines).

**Algorithm**: Sum file line counts per workflow

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Define Workflows (Repository-Specific)                  │
└─────────────────────────────────────────────────────────────────┘

Workflow("Feature Implementation") = [
    'AGENTS.md',                              # Navigation
    'ARCHITECTURE.md',                        # Component map
    'agentic/design-docs/core-beliefs.md',   # Design principles
    'agentic/domain/concepts/machine-config.md',  # Domain knowledge
    'agentic/domain/concepts/machine-config-pool.md',
    'agentic/decisions/adr-0001.md',         # Key decision
    'agentic/DESIGN.md',                     # Design guide
    'agentic/DEVELOPMENT.md',                # Dev guide
    'agentic/TESTING.md'                     # Test guide
]

┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Count Lines Per File                                    │
└─────────────────────────────────────────────────────────────────┘

File                                          Lines
────────────────────────────────────────────────────
AGENTS.md                                     139
ARCHITECTURE.md                               245
agentic/design-docs/core-beliefs.md           156
agentic/domain/concepts/machine-config.md     83
agentic/domain/concepts/machine-config-pool.md 37
agentic/decisions/adr-0001.md                 45
agentic/DESIGN.md                             122
agentic/DEVELOPMENT.md                        201
agentic/TESTING.md                            186
                                              ────
Total Context Budget:                         1214 lines ❌ (>700)

┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Evaluate All Workflows                                  │
└─────────────────────────────────────────────────────────────────┘

Workflow                      Files  Lines   Status
────────────────────────────────────────────────────────────────
Bug Fix (Simple)              3      585     ✅ PASS (≤700)
Bug Fix (Complex)             5      842     ❌ FAIL (>700)
Feature Implementation        9      1214    ❌ FAIL (>700)
Understanding System          4      623     ✅ PASS (≤700)
Security Review               3      421     ✅ PASS (≤700)

┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Report Violations                                       │
└─────────────────────────────────────────────────────────────────┘

✅ PASSED if:
   - All workflows ≤700 lines (or custom --max-budget)

❌ FAILED if:
   - Any workflow exceeds budget
   - Suggests: Split large files, use overview + detail pattern
```

### Example Output

```
Context Budget Analysis
=======================

Workflow: Feature Implementation
  Files: 9
  Total lines: 1214
  Status: ❌ OVER BUDGET (target: 700)

  Largest files:
    - ARCHITECTURE.md: 245 lines
    - agentic/DEVELOPMENT.md: 201 lines
    - agentic/TESTING.md: 186 lines

  Suggestion: Split large concept docs using overview pattern

Workflow: Bug Fix (Simple)
  Files: 3
  Total lines: 585
  Status: ✅ WITHIN BUDGET

Result: ❌ FAILED (2/5 workflows over budget)
```

---

## How They Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                    Documentation Structure                       │
└─────────────────────────────────────────────────────────────────┘

                    AGENTS.md (entry)
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ARCHITECTURE    DESIGN.md      domain/index.md
         │               │               │
         │               │          ┌────┴────┐
         │               │          │         │
         │          core-beliefs  concepts/  workflows/
         │                      machine-config.md
         │                           │
         └──────────────┬────────────┘
                        │
                   (Links form graph)

┌─────────────────────────────────────────────────────────────────┐
│ Navigation Depth: Measures GRAPH STRUCTURE                      │
└─────────────────────────────────────────────────────────────────┘
   "Can agents FIND this document from AGENTS.md in ≤3 clicks?"

   Uses: BFS graph traversal
   Tracks: Shortest path from AGENTS.md to each doc
   Goal: No orphans, no deep nesting

┌─────────────────────────────────────────────────────────────────┐
│ Context Budget: Measures CONTENT SIZE                           │
└─────────────────────────────────────────────────────────────────┘
   "How much do agents READ for this task?"

   Uses: Line counting + summation
   Tracks: Total lines loaded per workflow
   Goal: ≤700 lines to fit in working memory

┌─────────────────────────────────────────────────────────────────┐
│ Combined Impact                                                  │
└─────────────────────────────────────────────────────────────────┘

Good Navigation Depth (≤3 hops)
  → Agents find relevant docs quickly

Good Context Budget (≤700 lines)
  → Agents don't get overwhelmed with information

Both Together
  → Agent can navigate AND understand efficiently
```

---

## Key Algorithms

### Navigation Depth (BFS)

```python
def measure_navigation_depth(entry_point='AGENTS.md', max_depth=3):
    queue = [(entry_point, 0)]  # (file, depth)
    visited = {}

    while queue:
        current_file, depth = queue.pop(0)

        if current_file in visited:
            continue

        visited[current_file] = depth

        # Parse markdown links
        links = extract_markdown_links(current_file)

        for link in links:
            if link not in visited:
                queue.append((link, depth + 1))

    # Check violations
    violations = [f for f, d in visited.items() if d > max_depth]
    unreachable = expected_files - visited.keys()

    return violations, unreachable
```

### Context Budget (Summation)

```python
def measure_context_budget(workflows, max_budget=700):
    violations = []

    for workflow in workflows:
        total_lines = 0

        for file in workflow.files:
            lines = count_lines(file)
            total_lines += lines

        if total_lines > max_budget:
            violations.append({
                'workflow': workflow.name,
                'lines': total_lines,
                'budget': max_budget
            })

    return violations
```

---

## Real-World Example

**Scenario**: Agent fixing a bug in machine-config-operator

```
1. Agent loads "Bug Fix (Complex)" workflow:
   ├─ AGENTS.md (139 lines) ──────────┐
   ├─ ARCHITECTURE.md (245 lines) ────┤
   ├─ agentic/DEVELOPMENT.md (201 lines)  Total: 842 lines ❌
   ├─ agentic/domain/concepts/machine-config.md (83 lines)
   └─ agentic/TESTING.md (186 lines) ─┘

2. Navigation check:
   ✅ All files reachable in ≤3 hops from AGENTS.md

3. Budget check:
   ❌ 842 lines > 700 line budget

4. Fix: Split ARCHITECTURE.md into overview + components
   New total: 625 lines ✅
```

---

**Version**: 1.1
**Last Updated**: 2026-03-27
