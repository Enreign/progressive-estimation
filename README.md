# Progressive Estimation

> **Early Development Notice:** This skill is under active development. Formulas,
> multipliers, and default values are being calibrated and may change between
> versions. We welcome feedback, calibration data, and contributions to help
> stabilize the estimation model. Use in production planning at your own discretion.

A Claude Code skill for estimating AI-assisted and hybrid human+agent development work.

Research-backed formulas. PERT statistics. Calibration feedback loops. Zero dependencies.

> **Important:** Estimation is one of the hardest problems in software engineering.
> A database migration might take 2 days for a small app or 2 years for a large
> enterprise system. Meanwhile, small tasks that once took hours can now be completed
> in minutes with modern AI tools. This skill gives you structure and consistency —
> not certainty. See [DISCLAIMER.md](DISCLAIMER.md) for the full picture.

## What It Does

- Estimates development tasks accounting for both **human and AI agent effort**
- Supports **single tasks or batches** (paste 5 issues or 500)
- Produces **PERT expected values** with confidence bands, not just ranges
- Separates **"expected"** from **"committed"** estimates at your chosen confidence level
- Outputs in formats ready for **Linear, JIRA, ClickUp, GitHub Issues, Monday, and GitLab**
- Includes a **calibration system** to improve accuracy over time with actuals

## Quick Start

### Install

```bash
git clone https://github.com/YOUR_USERNAME/progressive-estimation.git ~/.claude/skills/progressive-estimation
```

### Use

In Claude Code, just ask for an estimate:

```
Estimate: "Add Stripe payment integration to our checkout flow"
```

Or batch estimate:

```
Estimate these tasks:
1. Add dark mode toggle
2. Migrate database from MySQL to PostgreSQL
3. Build Slack notification service
4. Implement CSV export for reports
5. Set up end-to-end test suite
```

The skill auto-triggers on keywords like *estimate*, *how long*, *effort*, *sizing*, *story points*.

## How It Works

### Progressive Disclosure

The skill asks only what it needs. Two paths:

| Path | Questions | Best For |
|------|-----------|----------|
| **Quick** | 4 questions + defaults | Fast sizing, backlog grooming |
| **Detailed** | 13 questions, full control | Sprint commitments, external deadlines |

Combined with single or batch scope, this gives four modes:

```
Quick + Single  →  fastest, ~4 questions
Quick + Batch   →  paste a list, get a table
Detailed + Single → full intake, rich output
Detailed + Batch  → shared defaults + per-task overrides
```

### What It Computes

```
Agent Rounds × Minutes per Round = Agent Time
                                 + Integration Time
                                 + Human Fix Time (agent-effectiveness-adjusted)
                                 + Human Review Time
                                 + Human Planning Time
                                 × Org Size Overhead (human time only)
                                 × Task Type Multiplier
                                 → apply Cone of Uncertainty spread
                                 → compute PERT Expected + Standard Deviation
                                 → apply Confidence Multiplier
                                 = Expected Estimate + Committed Estimate
```

### Key Concepts

**Agent Effectiveness Decay** — Based on [METR research](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/): AI agents handle ~90% of small tasks well but only ~30% of XL tasks. The skill automatically increases human effort for larger tasks.

**PERT Three-Point Estimation** — Every estimate produces a weighted expected value `(min + 4×midpoint + max) / 6` with standard deviation. This gives stakeholders a single "most likely" number plus confidence bands.

**Confidence Levels** — Separate "what we expect" from "what we commit to":
- 50% = stretch goal (raw expected)
- 80% = likely delivery (1.4×, default)
- 90% = safe for external deadlines (1.8×)

**Cone of Uncertainty** — Early-phase estimates get wider ranges automatically. A concept-phase estimate spreads 2× wider than a ready-to-build estimate.

**Task Type Multipliers** — Different work has different lifecycle overhead:

| Type | Multiplier | Why |
|------|-----------|-----|
| Coding | 1.0× | Baseline |
| Bug fix | 1.2× | Debugging, reproduction, regression testing |
| Investigation | 0.5× | Timeboxed — output is a plan, not code |
| Design | 1.2× | Iteration with stakeholders |
| Testing | 1.3× | Environment setup, fixtures, flakiness |
| Infrastructure | 1.5× | Provisioning, CI/CD, deployment verification |
| Data migration | 2.0× | Planning, validation, rollback, staged rollout |

## Example Output

### Single Task (Quick Mode)

```
Expected: ~4 hrs | Committed (80%): ~5.5 hrs | 10-26 agent rounds + 3 hrs human | Risk: medium | Size: M

PERT Expected: 4.2 hrs (most likely outcome)
Standard Deviation: ±0.8 hrs
68% Confidence: 3.4 - 5.0 hrs
95% Confidence: 2.6 - 5.8 hrs

| Field            | Value          |
|------------------|----------------|
| Complexity       | M              |
| Task Type        | coding         |
| Agent Rounds     | 10-26          |
| Agent Time       | 20-78 min      |
| Human Review     | 60 min         |
| Human Planning   | 30-60 min      |
| Human Fix/QA     | 8-30 min       |
| Expected (PERT)  | ~4 hrs         |
| Committed (80%)  | ~5.5 hrs       |
| Risk             | medium         |
| Team             | 1 human, 1 agent |
```

### Batch (Quick Mode)

```
5 tasks | Expected: ~23.5 hrs | Committed (80%): ~32.8 hrs | 2S, 2M, 1L

| # | Task              | Size | Type         | Expected | Committed | Risk |
|---|-------------------|------|--------------|----------|-----------|------|
| 1 | Dark mode toggle  | S    | coding       | ~1.3 hrs | ~1.8 hrs  | low  |
| 2 | DB migration      | L    | data-mig     | ~14.2 hrs| ~19.8 hrs | high |
| 3 | Slack notifier    | M    | coding       | ~2.9 hrs | ~4.1 hrs  | med  |
| 4 | CSV export        | S    | coding       | ~1.3 hrs | ~1.8 hrs  | low  |
| 5 | E2E test suite    | M    | testing      | ~3.8 hrs | ~5.3 hrs  | med  |

Warnings:
- Task #2 is type=data-migration (2.0x overhead). Consider phased delivery.
```

## Issue Tracker Integration

Estimates can be output in two modes for any supported tracker:

| Mode | How It Works | Setup Required |
|------|-------------|----------------|
| **Embedded** (default) | Markdown table in the description/body | None |
| **Native** | Maps to tracker-specific fields | Custom fields |

Supported trackers: **Linear, JIRA, ClickUp, GitHub Issues, Monday, GitLab**

Embedded mode works everywhere immediately. Native mode requires custom fields
for agent-specific metrics (agent rounds, committed estimate, etc.).

## Standalone Calculator

Don't want to depend on an LLM for arithmetic? Ask the skill to generate a
deterministic calculator script:

```
Generate an estimation calculator in Python
```

The skill generates a single-file, zero-dependency script from the canonical
formulas that accepts inputs via CLI args or stdin JSON and outputs the full
estimate as JSON. Supported languages:

Python, TypeScript, JavaScript, Rust, Go, Ruby, Java, C#, Swift, Kotlin

## Calibration

Estimates improve with feedback. The skill includes a calibration system:

1. **Log actuals** — Record estimated vs. actual effort after completing work
2. **Track PRED(25)** — Percentage of estimates within 25% of actual (target: 75%)
3. **Reference stories** — Maintain examples per size per task type as anchors
4. **Bias detection** — Identify systematic over/under estimation
5. **Team profiles** — Separate calibration per team

Most teams reach PRED(25) ≥ 65% within 3-5 calibration cycles and ≥ 75%
within 8-12 cycles.

See [references/calibration.md](references/calibration.md) for the full system.

## File Structure

```
progressive-estimation/
├── SKILL.md                          # Workflow map (loaded first, always)
├── DISCLAIMER.md                     # Honest limitations of estimation
├── README.md                         # This file
├── LICENSE                           # MIT
├── references/
│   ├── questionnaire.md              # Progressive intake (loaded phase 1)
│   ├── frameworks.md                 # Round-based, module/wave, S-M-L (phase 2)
│   ├── formulas.md                   # All arithmetic, single source of truth (phase 3)
│   ├── output-schema.md             # Output formats, tracker mappings (phase 4)
│   └── calibration.md               # Tuning with actuals (phase 5, on request)
└── evals/
    ├── eval-quick.md                 # Quick path smoke test
    ├── eval-hybrid.md                # Detailed path, multi-team
    ├── eval-batch.md                 # Batch with dependencies
    └── eval-regression.md            # Known-good baselines
```

Files are loaded progressively — the skill only reads what it needs for the
current phase. SKILL.md is the map; reference files are the territory.

## Research Behind the Formulas

The estimation model is informed by:

- **[METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)** — Agent effectiveness decay by task size; AI time horizon benchmarks
- **[PERT](https://en.wikipedia.org/wiki/Three-point_estimation)** — Three-point estimation with beta distribution for expected values
- **[James Shore](http://www.jamesshore.com/v2/blog/2008/use-risk-management-to-make-solid-commitments)** — Risk multipliers for confidence-based commitments
- **[Jorgensen & Grimstad](https://www.sciencedirect.com/science/article/abs/pii/S0164121202001565)** — Calibration feedback improving accuracy from 64% to 81%
- **[Construx Cone of Uncertainty](https://www.construx.com/books/the-cone-of-uncertainty/)** — Estimate ranges narrowing as decisions are made
- **[Standish CHAOS](https://www.umsl.edu/~sauterv/7892/Standish/standish-IST.pdf)** — Project overrun patterns (and their [limitations](https://www.umsl.edu/~sauterv/7892/Standish/standish-IST.pdf))

## Evals

The skill includes evaluation prompts per the [Claude Skills 2.0](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills) framework:

| Eval | Tests |
|------|-------|
| `eval-quick.md` | Quick path produces valid PERT output with minimal input |
| `eval-hybrid.md` | Detailed path handles multi-team, confidence levels, org overhead |
| `eval-batch.md` | Batch mode with mixed types, dependencies, and rollup |
| `eval-regression.md` | 6 baseline cases to detect drift after formula changes |

Run evals after any change to formulas, frameworks, or the skill workflow.

## Contributing

Contributions welcome. Key areas:

- **Calibration data** — If you track estimated vs. actual, share anonymized results to improve the default ratios
- **Tracker mappings** — Additional tracker support (Asana, Notion, Shortcut, etc.)
- **Task types** — New multipliers for work categories not yet covered
- **Formulas** — Improvements backed by data or research
- **Evals** — Additional test cases, especially edge cases

Please include research citations or empirical data when proposing formula changes.

## License

[MIT](LICENSE)
