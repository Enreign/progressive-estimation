---
name: progressive-estimation
description: An AI skill for estimating AI-assisted and hybrid human+agent development work. Research-backed formulas with PERT statistics, confidence bands, calibration feedback loops, and zero dependencies. Triggers on estimation, effort sizing, story points, how long, agent time, and staffing planning.
license: MIT
metadata:
  author: Enreign
  version: "0.1.1"
---

# Progressive Estimation

> Estimate AI-assisted and hybrid human+agent work with progressive disclosure.
> Research-backed formulas with PERT statistics, confidence bands, and
> calibration feedback loops.

## Trigger

Use when a user wants time/effort estimates for:
- AI-assisted development tasks
- Mixed human+agent workflows
- Batch estimation of backlog items
- Staffing or rollout planning with agents

Keywords: estimate, how long, effort, sizing, story points, rounds, agent time

## Interaction

When asking questionnaire questions, use the `AskUserQuestion` tool if available
in your environment. This creates a structured back-and-forth flow instead of
dumping all questions at once. Ask one question at a time and wait for the
response before proceeding. If the tool is not available, fall back to
conversational questions in your text output.

## Workflow

### Phase 0: Mode Selection

Ask two questions upfront (one at a time):

1. **Speed**: "Quick estimate with sensible defaults, or detailed walkthrough?"
2. **Scope**: "Single task or batch of tasks?"

This produces four paths:
- Quick + Single → fastest, ~4 questions then output
- Quick + Batch → accept list, apply defaults to all, output summary table
- Detailed + Single → full questionnaire (13 questions), rich output
- Detailed + Batch → full questionnaire for shared parameters, per-task overrides

### Phase 1: Intake

**Load** `references/questionnaire.md` for the appropriate path.

Quick path asks only:
1. What's the task? (or paste your list)
2. What type of work? (coding / bug-fix / investigation / testing / infrastructure / data-migration / design)
3. How many humans and how many agents?
4. Automation maturity: exploratory / partial / mostly-automated?

If task type is obvious from the description, auto-assign it and note it.

Detailed path adds: risk factors, integration complexity, domain familiarity,
review depth, human fix ratio, confidence level, definition phase,
organization context, and per-task dependency mapping.

Every question feeds a specific formula variable — see the mapping table in
questionnaire.md for the complete wiring.

### Phase 2: Framework Selection

**Load** `references/frameworks.md` to select the right model:

| Scenario | Framework |
|----------|-----------|
| Single agent task | Round-based |
| Multi-agent project | Module/wave |
| Backlog import or rough sizing | S-M-L conversion |

For batch input, apply the selected framework per task, then roll up with
dependency sequencing.

### Phase 3: Estimation

**Load** `references/formulas.md` and compute estimates using the canonical
formulas. Claude performs the arithmetic inline — no external script needed.

The computation pipeline:
1. Base rounds × risk × domain familiarity → agent rounds
2. Agent rounds × minutes per round → agent time
3. Integration, human fix (agent-effectiveness-adjusted), review, planning
4. Apply org size overhead to human time
5. Apply task type multiplier to subtotal
6. Apply cone of uncertainty spread to widen/narrow range
7. Compute PERT expected value and standard deviation
8. Apply confidence multiplier for committed estimate
9. Check anti-pattern guards and generate warnings

If the user requests a standalone deterministic calculator, generate one from
`formulas.md` in their preferred language. The generated script must:
- Accept inputs via CLI args or stdin
- Output JSON with all canonical fields
- Have zero external dependencies
- Be a single self-contained file

### Phase 4: Output

**Load** `references/output-schema.md` for formatting.

Always lead with the **one-line summary**, then PERT block, then expand:

```
Expected: ~4 hrs | Committed (80%): ~5.5 hrs | 10-26 agent rounds + 3 hrs human | Risk: medium | Size: M
```

Then provide:
- PERT expected value with confidence bands (68%, 95%)
- Full breakdown table
- Anti-pattern warnings (if any triggered)
- Tracker-formatted output (if requested)

Ask which tracker and mode:
- **Tracker**: Linear, JIRA, ClickUp, GitHub Issues, Monday, GitLab, or generic
- **Mode**: Native fields or embedded in description (default: embedded)

For batch output, produce a summary table first, then rollup, then warnings,
then per-task details on request.

### Phase 5: Calibration (Optional)

**Load** `references/calibration.md` when the user wants to log actuals or
tune their estimation ratios.

Key calibration features:
- **PRED(25)** tracking — target 75% of estimates within 25% of actuals
- **Reference story library** — concrete examples per size per task type
- **Bias detection** — systematic over/under estimation identification
- **Team profiles** — separate calibration per team
- **Convergence tracking** — teams reach accuracy within 5-10 cycles

### Re-estimation Triggers

Suggest re-estimation when:
- Scope changes after initial estimate
- A task is blocked by an unresolved dependency
- Midpoint check reveals estimate drift >30%
- Team composition changes (humans or agents added/removed)
- Automation maturity level shifts during the project
- Definition phase advances (narrower cone of uncertainty)

## Loading Phases

| Phase | Files Loaded | When |
|-------|-------------|------|
| 0-1 | questionnaire.md | Always (intake) |
| 2 | frameworks.md | After intake |
| 3 | formulas.md | During computation |
| 4 | output-schema.md | During output |
| 5 | calibration.md | On request |

## Key Concepts

### Agent Effectiveness Decay
Based on METR research: AI agents excel at small tasks (~90% effectiveness)
but effectiveness drops to ~30% for XL tasks. The skill automatically
increases human effort allocation for larger tasks.

### PERT Three-Point Estimation
Every estimate produces a weighted expected value using
`(min + 4×midpoint + max) / 6` with standard deviation `(max - min) / 6`.
This gives stakeholders a single "most likely" number plus confidence bands.

### Confidence Levels
Separate "expected" from "committed" estimates:
- 50% = stretch goal (raw expected value)
- 80% = likely delivery (1.4x, default for quick path)
- 90% = safe commitment for external deadlines (1.8x)

### Cone of Uncertainty
Early-phase estimates have wider ranges. The skill widens min/max spread
based on how well-defined the work is, preventing false precision.

### Anti-Pattern Guards
The skill warns against common estimation mistakes: oversized tasks,
false precision, estimates-as-commitments, and point-to-hour conversions.

## Skill Type

Encoded Preference Skill — sequences a workflow Claude can already perform,
following a specific estimation process with research-backed formulas,
PERT statistics, and calibration feedback loops.
