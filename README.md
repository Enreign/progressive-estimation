<div align="center">

# Agent Skills

**A collection of AI skills for modern development workflows.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Early Development](https://img.shields.io/badge/Status-Early%20Development-orange.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude%20Code-blueviolet.svg)]()
[![Cursor](https://img.shields.io/badge/Cursor-blue.svg)]()
[![Copilot](https://img.shields.io/badge/GitHub%20Copilot-black.svg)]()
[![Windsurf](https://img.shields.io/badge/Windsurf-teal.svg)]()
[![Cline](https://img.shields.io/badge/Cline-green.svg)]()
[![Aider](https://img.shields.io/badge/Aider-orange.svg)]()

</div>

---

> [!WARNING]
> **Early development.** Skills in this repo are actively developed and may change frequently. Expect rough edges, incomplete calibration, and breaking changes between versions. Bug reports, calibration data, and PRs are welcome.

> [!NOTE]
> **Estimation is one of the hardest problems in software engineering.** A database migration might take 2 days for a small app or 2 years for a large enterprise system. Meanwhile, small tasks that once took hours can now be completed in minutes with modern AI tools. These skills give you structure and consistency — not certainty. See [DISCLAIMER.md](DISCLAIMER.md) for the full picture.

---

## Install

**One command** (via [skills.sh](https://skills.sh) — works with Claude Code, Cursor, Codex, and 37+ agents):

```bash
# Install all skills
npx skills add Enreign/agent-skills

# Install a specific skill
npx skills add Enreign/agent-skills --skill progressive-estimation
```

**Manual** (Claude Code):

```bash
git clone https://github.com/Enreign/agent-skills.git ~/.claude/skills/agent-skills
```

**Other clients:** See the [Installation Guide](INSTALLATION.md) for Cursor, GitHub Copilot, Windsurf, Cline, Aider, Continue.dev, ChatGPT, and Gemini Code Assist.

---

## Skills

### Progressive Estimation

> Estimate AI-assisted and hybrid human+agent development work with progressive disclosure. Research-backed formulas, PERT statistics, calibration feedback loops, zero dependencies.

| | |
|---|---|
| **What it does** | Estimates development tasks accounting for both human and AI agent effort |
| **Modes** | Single task or batch (paste 5 issues or 500) |
| **Output** | PERT expected values with confidence bands, not just ranges |
| **Trackers** | Linear, JIRA, ClickUp, GitHub Issues, Monday, GitLab |
| **Calibration** | Log actuals, track PRED(25), improve accuracy over time |

**Quick start** — just ask:

```
Estimate: "Add Stripe payment integration to our checkout flow"
```

Auto-triggers on keywords: *estimate*, *how long*, *effort*, *sizing*, *story points*.

<details>
<summary><strong>Example output</strong></summary>

```
Expected: ~4 hrs | Committed (80%): ~5.5 hrs | 10-26 agent rounds + 3 hrs human | Risk: medium | Size: M

PERT Expected: 4.2 hrs (most likely outcome)
Standard Deviation: +/-0.8 hrs
68% Confidence: 3.4 - 5.0 hrs
95% Confidence: 2.6 - 5.8 hrs
```

| Field | Value |
|-------|-------|
| Complexity | M |
| Task Type | coding |
| Agent Rounds | 10-26 |
| Agent Time | 20-78 min |
| Human Review | 60 min |
| Human Planning | 30-60 min |
| Human Fix/QA | 8-30 min |
| **Expected (PERT)** | **~4 hrs** |
| **Committed (80%)** | **~5.5 hrs** |
| Risk | medium |
| Team | 1 human, 1 agent |

</details>

<details>
<summary><strong>How it works</strong></summary>

**Progressive Disclosure** — asks only what it needs:

| Path | Questions | Best For |
|------|-----------|----------|
| **Quick** | 4 questions + defaults | Fast sizing, backlog grooming |
| **Detailed** | 13 questions, full control | Sprint commitments, external deadlines |

**Computation Pipeline:**

```
Agent Rounds x Minutes per Round
    + Integration Time
    + Human Fix Time (agent-effectiveness-adjusted)
    + Human Review Time
    + Human Planning Time
    x Org Size Overhead (human time only)
    x Task Type Multiplier
    -> Cone of Uncertainty spread
    -> PERT Expected + Standard Deviation
    -> Confidence Multiplier
    = Expected Estimate + Committed Estimate
```

**Key concepts:**
- **Agent Effectiveness Decay** — based on METR research, agents handle ~90% of small tasks but only ~30% of XL tasks
- **PERT Three-Point Estimation** — weighted expected value with confidence bands (68%, 95%)
- **Confidence Levels** — 50% (stretch), 80% (likely, default), 90% (safe commitment)
- **Cone of Uncertainty** — early-phase estimates get wider ranges automatically
- **Task Type Multipliers** — coding (1.0x) through data migration (2.0x)

</details>

<details>
<summary><strong>Research</strong></summary>

| Source | Contribution |
|--------|-------------|
| [METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) | Agent effectiveness decay by task size |
| [PERT](https://en.wikipedia.org/wiki/Three-point_estimation) | Three-point estimation with beta distribution |
| [James Shore](http://www.jamesshore.com/v2/blog/2008/use-risk-management-to-make-solid-commitments) | Risk multipliers for confidence-based commitments |
| [Jorgensen & Grimstad](https://www.sciencedirect.com/science/article/abs/pii/S0164121202001565) | Calibration feedback improving accuracy 64% -> 81% |
| [Construx](https://www.construx.com/books/the-cone-of-uncertainty/) | Cone of Uncertainty |

</details>

---

## File Structure

```
agent-skills/
├── README.md
├── INSTALLATION.md             Setup guide for 9+ AI coding clients
├── DISCLAIMER.md               Honest limitations of estimation
├── CONTRIBUTING.md              How to contribute
├── CODE_OF_CONDUCT.md           Community guidelines
├── LICENSE                      MIT
├── assets/
│   └── banner.png
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
└── skills/
    └── progressive-estimation/
        ├── SKILL.md             Workflow map (loaded first)
        ├── references/
        │   ├── questionnaire.md Progressive intake
        │   ├── frameworks.md    Round-based, module/wave, S-M-L
        │   ├── formulas.md      All arithmetic, single source of truth
        │   ├── output-schema.md Output formats, tracker mappings
        │   └── calibration.md   Tuning with actuals
        └── evals/
            ├── eval-quick.md
            ├── eval-hybrid.md
            ├── eval-batch.md
            └── eval-regression.md
```

---

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Key areas:

- **Calibration data** — anonymized estimated vs. actual results
- **Tracker mappings** — Asana, Notion, Shortcut, etc.
- **New skills** — add a `skills/your-skill/SKILL.md` and open a PR
- **Formulas** — improvements backed by data or research
- **Evals** — additional test cases and edge cases

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

[MIT](LICENSE) — Copyright (c) 2026 Stanislav Shymanskyi
