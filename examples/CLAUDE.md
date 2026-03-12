# Project Instructions

<!-- Copy this file (or merge the relevant sections) into your project's CLAUDE.md -->

## Estimation

This project uses [Progressive Estimation](https://github.com/Enreign/progressive-estimation)
for sizing development work. The skill is installed and auto-triggers on keywords
like "estimate", "how long", "effort", "sizing", "story points".

### Quick reference for available features

**Modes** — choose how much control you want:
- **Instant** — zero questions, infer everything, output immediately
- **Quick** — 4 questions with sensible defaults (good for backlog grooming)
- **Detailed** — 13 questions, full control (good for sprint commitments)

**Scope** — single task or batch (paste 5 or 500 tasks at once).

**Small Council** — for M/L/XL tasks, the skill automatically runs multi-perspective
validation (Optimist, Skeptic, Historian) to catch blind spots before finalizing.

**Calibration** — after completing work, log actuals to improve future estimates.
Tracks PRED(25) accuracy, detects systematic bias, and maintains reference stories.
Invoke with: "calibrate estimation with actuals" or "log estimation actuals".

**Tracker integration** — output estimates formatted for Linear, JIRA, ClickUp,
GitHub Issues, Monday, GitLab, Asana, Azure DevOps, Zenhub, or Shortcut.
Supports native fields or embedded markdown in descriptions.

**Standalone calculator** — generate a zero-dependency estimation script in
Python, TypeScript, Rust, Go, Ruby, Java, C#, Swift, Kotlin, or JavaScript.
Invoke with: "generate an estimation calculator in [language]".

**Re-estimation** — suggest re-estimation when scope changes, dependencies shift,
team composition changes, or midpoint checks reveal >30% drift.

### Estimation conventions for this project

<!-- Customize these for your team: -->
<!-- - Default confidence level: 80% -->
<!-- - Default tracker: Linear (embedded mode) -->
<!-- - Default team: 2 humans, 1 agent, partial maturity -->
<!-- - Org size: startup -->
<!-- - Always use detailed mode for tasks tagged "external-deadline" -->
