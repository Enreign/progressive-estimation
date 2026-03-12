# Agent Instructions

<!-- Copy this file (or merge the relevant sections) into your project's AGENTS.md -->
<!-- AGENTS.md tells subagents how to behave when working on tasks in this project. -->

## Estimation

This project uses [Progressive Estimation](https://github.com/Enreign/progressive-estimation)
for sizing work before implementation begins.

### When to estimate

- Before starting any task sized M or larger
- When a user asks "how long will this take?" or similar
- When planning a batch of work (sprint planning, backlog grooming)
- When scope changes on an in-progress task (re-estimation)

### How to invoke

The skill auto-triggers on keywords: *estimate*, *how long*, *effort*, *sizing*,
*story points*, *agent time*. You can also invoke it explicitly:

```
/progressive-estimation
```

### Modes

| Mode | When to use |
|------|-------------|
| **Instant** | Quick sanity check, rough sizing during planning |
| **Quick** | Default for most tasks — 4 questions, good defaults |
| **Detailed** | External deadlines, high-stakes commitments, complex projects |

For batch estimation, pass a list of tasks. The skill handles mixed types,
dependencies, and produces a rollup summary.

### What the output includes

- **One-line summary**: expected hours, committed hours, agent rounds, risk, size
- **PERT statistics**: expected value + 68%/95% confidence bands
- **Breakdown table**: agent rounds, agent time, human review/fix/planning time
- **Anti-pattern warnings**: oversized tasks, false precision, missing risk factors
- **Token & cost estimates**: per model tier (economy/standard/premium)

### Features agents should know about

**Small Council** — For M+ tasks, the skill spawns perspective subagents
(Optimist, Skeptic, Historian) to validate the estimate. This is automatic;
no action needed.

**Calibration** — If the user has logged actuals before, the skill uses that
data to adjust multipliers. When a task is completed, suggest logging actuals:
"Want to log actuals for calibration?"

**Tracker integration** — The skill can format output for 10+ trackers.
Ask which tracker and mode (native fields vs embedded markdown) during output.

**Standalone calculator** — Users can request a deterministic calculator script
in 10 languages. The generated script has zero dependencies and reproduces
the skill's arithmetic exactly.

**Re-estimation triggers** — Suggest re-estimation when:
- Scope changes after initial estimate
- A blocking dependency is discovered
- Team composition changes (humans or agents added/removed)
- Midpoint check shows >30% drift from estimate
- Definition phase advances (concept → requirements → design → ready)

### Conventions

<!-- Customize for your team: -->
<!-- - Always estimate before starting L/XL tasks -->
<!-- - Use quick mode by default, detailed for external deadlines -->
<!-- - Log actuals after every completed task -->
<!-- - Default tracker: Linear -->
<!-- - Flag any task estimated >40 hrs for decomposition -->
