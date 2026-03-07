# Questionnaire: Progressive Intake

Every question feeds a specific formula input. Questions marked with → show
which formula variable they calibrate.

## Quick Path — Single Task

Ask these four questions, then estimate immediately:

1. **Task description**: "What needs to be done?"
   → Used to infer: `complexity`, `task_type`, `risk_level`
2. **Task type**: "What kind of work is this?"
   → `task_type` (determines lifecycle multiplier)
   - Coding (features, bug fixes, refactors) — 1.0x
   - Bug fix (debugging, reproduction, regression testing) — 1.2x
   - Investigation (research spike, output is a plan) — 0.5x (timeboxed)
   - Testing (test suites, QA automation) — 1.3x
   - Infrastructure (CI/CD, deployment, provisioning) — 1.5x
   - Data migration (schema changes, data moves, ETL) — 2.0x
   - Design (UI/UX, mockups, prototyping) — 1.2x
   - If obvious from description, auto-assign and note it.
3. **Team composition**: "How many humans and how many agents?"
   → `num_humans`, `num_agents`
   - Default: 1 human, 1 agent
4. **Automation maturity**: "How established is your AI-assisted workflow?"
   → `maturity` (determines minutes per round)
   - Exploratory (first time, lots of unknowns) — 3-5 min/round
   - Partial (some tasks automated, some manual) — 2-3 min/round
   - Mostly-automated (well-defined agent workflows) — 1-2 min/round

Apply defaults for unasked inputs:
- Risk coefficient: 1.3 → `risk_coefficient`
- Integration overhead: 15% → `integration_overhead`
- Human fix ratio: 20% → `human_fix_ratio`
- Review depth: standard → `review_depth`
- Domain familiarity: 1.0 → `domain_familiarity`
- Confidence level: 80% → `confidence_level`
- Definition phase: ready → `definition_phase`
- Org size: solo-startup → `org_size`

## Quick Path — Batch

1. **Task list**: "Paste your tasks (one per line, or CSV with columns: task, complexity, notes)"
   → Each task gets: `complexity` (inferred), `task_type` (inferred)
   - Accept plain list, CSV, markdown table, or JSON array
   - If only names given, infer complexity and task type from description
   - Show inferred values in confirmation table before estimating
2. **Task type default**: "What's the primary type of work in this batch?"
   → `task_type` (applied globally, overridable per task)
   - If batch is mixed, auto-classify each task and show in confirmation table
3. **Team composition**: same as above (applied globally)
   → `num_humans`, `num_agents`
4. **Automation maturity**: same as above (applied globally)
   → `maturity`

Output a confirmation table, then: "Want to adjust any tasks before I estimate?"

```
| # | Task                  | Size | Type           | Risk | Deps | Adjust? |
|---|-----------------------|------|----------------|------|------|---------|
| 1 | Auth service          | M    | coding         | med  | —    |         |
| 2 | DB migration          | L    | data-migration | high | —    |         |
| 3 | Email templates       | S    | coding         | low  | —    |         |
```

## Detailed Path — Single Task

All quick-path questions, plus:

5. **Risk factors**: "What could go wrong or is uncertain?"
   → `risk_coefficient` (auto-derive from answers or let user set directly)
   - Unknown API surface / undocumented dependencies → +0.3
   - Ambiguous requirements → +0.2
   - New technology / unfamiliar domain → +0.3
   - External service dependencies → +0.2
   - Production data involved → +0.3
   - Base: 1.0, add applicable increments, cap at 2.5
6. **Integration complexity**: "How much glue code, config, or wiring?"
   → `integration_overhead`
   - Standalone (5%)
   - Moderate integration (15%)
   - Heavy integration with existing systems (25%)
   - Cross-system integration (30%)
7. **Domain familiarity**: "How well does the team know this area?"
   → `domain_familiarity`
   - Expert (0.8x) — team has shipped similar work before
   - Familiar (1.0x) — team knows the domain, not this specific area
   - Somewhat new (1.3x) — team is learning as they go
   - Completely new (1.5x) — first time in this domain
8. **Review depth**: "What level of human review is needed?"
   → `review_depth`
   - Light scan — quick check, trusted agent output
   - Standard review — line-by-line review, basic testing
   - Deep review with testing — thorough review, manual testing, edge cases
9. **Human fix ratio**: "How much of the agent's output typically needs manual fixes?"
   → `human_fix_ratio`
   - Minimal (5-10%) — agent output is usually production-ready
   - Moderate (15-25%) — some adjustments needed
   - Significant (30-50%) — substantial rework expected
10. **Confidence level**: "What confidence level do you need for this commitment?"
    → `confidence_multiplier`
    - 50% (stretch goal) — equal chance of finishing earlier or later (1.0x)
    - 80% (likely) — reasonable buffer for typical unknowns (1.4x)
    - 90% (safe commitment) — high confidence, suitable for external deadlines (1.8x)
    - Explain: "50% means 'our best guess', 90% means 'we're almost certain
      we'll deliver within this range'."
11. **Definition phase**: "How well-defined is this work right now?"
    → `spread_multiplier` (affects width of estimate range)
    - Concept (just an idea, minimal spec) — range spreads 2x wider
    - Requirements defined (we know what, not fully how) — range spreads 1.5x
    - Design complete (architecture decided, ready to spec tasks) — range spreads 1.2x
    - Ready to build (clear spec, acceptance criteria defined) — baseline range
    - Explain: "Earlier phases have wider ranges because more unknowns remain.
      This doesn't change the expected value, just the uncertainty band."
12. **Organization context**: "What's your team/org size?"
    → `org_overhead` (multiplier on human time only)
    - Solo/startup (1-10 people) — minimal process overhead (1.0x)
    - Growth (10-50 people) — some process, light review, moderate coordination (1.15x)
    - Enterprise (50+ people) — formal review, compliance, multi-team coordination (1.3x)
13. **Dependencies**: "Is this blocked by or blocking other tasks?"
    → dependency graph for sequencing

## Detailed Path — Batch

Questions 2-12 asked once as shared defaults for the batch.
Then for each task:

- Confirm or override complexity (S/M/L/XL) → `complexity`
- Confirm or override task type → `task_type`
- Note any per-task dependencies → dependency graph
- Flag any tasks that deviate from shared defaults

Present as a table for quick confirmation:

```
| # | Task                | Size | Type           | Risk | Famil. | Deps | Override? |
|---|---------------------|------|----------------|------|--------|------|-----------|
| 1 | Auth service        | M    | coding         | 1.3  | 1.0    | —    |           |
| 2 | DB migration        | XL   | data-migration | 1.8  | 1.0    | —    |           |
| 3 | Email templates     | S    | coding         | 1.0  | 0.8    | —    |           |
```

User can mark overrides or approve the whole table at once.

## Input → Formula Mapping (Complete)

| Question | Formula Variable | Quick Default | Detailed Source |
|----------|-----------------|---------------|-----------------|
| Task description | complexity, task_type | inferred | inferred + confirmed |
| Task type | task_type_multiplier | inferred or asked | asked |
| Team composition | num_humans, num_agents | 1, 1 | asked |
| Automation maturity | minutes_per_round | partial | asked |
| Risk factors | risk_coefficient | 1.3 | derived from answers |
| Integration complexity | integration_overhead | 0.15 | asked |
| Domain familiarity | domain_familiarity | 1.0 | asked |
| Review depth | review_minutes | standard | asked |
| Human fix ratio | human_fix_ratio | 0.20 | asked |
| Confidence level | confidence_multiplier | 80% (1.4x) | asked |
| Definition phase | spread_multiplier | ready (1.0x) | asked |
| Organization context | org_overhead | solo-startup (1.0x) | asked |
| Dependencies | sequencing | none | asked |

## Input Formats Accepted (Batch)

- **Plain list**: one task per line
- **CSV**: `task, complexity, type, notes` (header optional)
- **Markdown table**: any column layout, skill maps columns to fields
- **JSON array**: `[{"task": "...", "complexity": "M", "type": "coding", "notes": "..."}]`
- **Pasted from tracker**: best-effort parsing of copied issue lists
