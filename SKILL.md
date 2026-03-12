---
name: progressive-estimation
description: "Adapts to your team's working mode — human-only, hybrid, or agent-first — with research-backed formulas, confidence bands, and the right velocity model for each."
license: MIT
metadata:
  author: Enreign
  version: "0.5.0"
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

Use the `AskUserQuestion` tool if available in your environment for ALL user
interactions: mode selection (Phase 0), intake questions (Phase 1), batch
confirmation ("adjust any tasks?"), and tracker selection (Phase 4). This
creates structured dropdowns instead of free-text back-and-forth. Ask one
question at a time (or group related questions, up to 4 per call) and wait
for the response before proceeding. If the tool is not available, fall back
to conversational questions in your text output. Instant mode skips Phase 0
and Phase 1 questions but still uses the tool for Phase 4 tracker selection.

## Workflow

### Phase 0: Mode Selection

Ask two questions upfront (one at a time):

1. **Control**: "How much control do you want?"
   - **Instant** — zero questions, infer everything from the task description, output immediately
   - **Quick** — 4 questions with sensible defaults
   - **Detailed** — 13 questions, full control over every parameter
2. **Scope**: "Single task or batch?"

This produces six paths:
- Instant + Single → infer all parameters, output immediately
- Instant + Batch → accept list, infer per task, output summary table
- Quick + Single → ~4 questions then output
- Quick + Batch → accept list, apply defaults to all, output summary table
- Detailed + Single → full questionnaire (13 questions), rich output
- Detailed + Batch → full questionnaire for shared parameters, per-task overrides

### Instant Mode

When the user selects Instant mode:
- Infer complexity, task_type, and risk_level from the task description
- Apply all defaults: 1 human, 1 agent, partial maturity, risk 1.3,
  integration 15%, human fix 20%, standard review, domain familiarity 1.0,
  confidence 80%, ready phase, solo-startup org
- Skip directly to Phase 3 (Estimation) and Phase 4 (Output)
- After output, suggest: "Want to refine? Say 'quick' for 4 questions or
  'detailed' for full control."

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

### Phase 1.5: Cooperation Mode Detection (Automatic)

Auto-detect the team's cooperation mode from intake answers:

```
if num_agents == 0 → Human-only mode
if num_agents > 0 AND maturity in [exploratory, partial] → Hybrid mode
if num_agents > 0 AND maturity == mostly-automated → Agent-first mode
```

Announce the detected mode before proceeding:

| Mode | Announcement | Points Approach |
|------|-------------|----------------|
| Human-only | "Detected: human-only team. Using standard estimation with story points." | Points for sizing and velocity |
| Hybrid | "Detected: hybrid team. Using dual-track estimation — points for sizing, hours for planning." | Dual-track: points + hours |
| Agent-first | "Detected: agent-first team. Planning by human review capacity in hours." | Hours only; points optional for rough sizing |

This mode affects output format (Phase 4) and calibration recommendations (Phase 5).

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
9. Compute token & cost estimates (Step 15)
10. Check anti-pattern guards and generate warnings

If the user requests a standalone deterministic calculator, generate one from
`formulas.md` in their preferred language. The generated script must:
- Accept inputs via CLI args or stdin
- Output JSON with all canonical fields
- Have zero external dependencies
- Be a single self-contained file

### Phase 3.5: Small Council Validation (Automatic)

Three subagent perspectives review the estimate before output:

- **Optimist**: Best-case analyst. What if everything goes right? Looks for
  parallelizable work, reducible scope.
- **Skeptic**: Risk analyst. What's missing? Hidden dependencies, integration
  surprises, underestimated review.
- **Historian**: Calibration analyst. How do similar past tasks compare?
  Reference stories, velocity data.

Trigger rules based on complexity:

| Complexity | Council Members | Rationale |
|------------|----------------|-----------|
| S | None | Overhead exceeds value |
| M | Skeptic only | 1 subagent |
| L | Skeptic + Historian | 2 subagents |
| XL | Full council (all 3) | All subagents |

Each agent gives 2-3 sentences. Output a consensus estimate that weighs all
perspectives. Flag disagreements where agents differ by >20%.

> **Note:** Use the Agent tool to spawn council members as subagents if
> available. If not available, simulate the perspectives inline.

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
- **Tracker**: Linear, JIRA, ClickUp, GitHub Issues, Monday, GitLab, Asana, Azure DevOps, Zenhub, Shortcut, or generic
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
| 0-1 | questionnaire.md | Always (intake); skipped in Instant mode |
| 1.5 | (no files) | Automatic after intake |
| 2 | frameworks.md | After intake |
| 3 | formulas.md | During computation |
| 3.5 | calibration.md (reference stories) | Automatic for M+ tasks (council validation) |
| 4 | output-schema.md | During output |
| 5 | calibration.md | On request |

## Key Concepts

### Agent Effectiveness Decay
Based on METR research (24k runs, 228 tasks): AI agents excel at small tasks
(~90% effectiveness) but effectiveness drops to ~30% for XL tasks. The skill
automatically increases human effort allocation for larger tasks.

### Log-Normal Three-Point Estimation
Every estimate produces a weighted expected value using a log-normal weighting:
`(min + 4×geometric_mean + max) / 6` with standard deviation `(max - min) / 6`.
Deep validation (KS test, n=84k) showed log-normal fits actual software effort
distributions better than PERT-beta in all size bands.

### Confidence Levels
Size-dependent multipliers derived from 84k estimate-actual pairs. Small tasks
need larger buffers due to wider actual/estimate spreads:
- 50% = stretch goal (raw expected value)
- 80% = likely delivery (1.4–1.8x depending on size, default for quick path)
- 90% = safe commitment for external deadlines (2.0–2.9x depending on size)

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
