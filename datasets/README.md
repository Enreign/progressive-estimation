# Research Datasets

Data files in this directory are `.gitignore`d — download them locally for validation and calibration analysis.

## Download Instructions

### 1. Derek Jones Collection (203k+ tasks) — HIGHEST VALUE

```bash
git clone https://github.com/Derek-Jones/Software-estimation-datasets.git datasets/derek-jones
```

Key files:
- `CESAW/` — 203,621 tasks with estimated vs actual person-hours
- `SiP/` — 10,100 tasks with estimated vs actual effort
- `Project-22/` — 630 tasks with story points + actual hours
- `renzo-pomodoro/` — 17,764 tasks in Pomodoro units

### 2. Deep-SE Story Points (23k JIRA issues)

```bash
git clone https://github.com/barkhahbpp/deepsedataset.git datasets/deep-se
```

Story point data from 16 open-source JIRA projects.

### 3. SWE-bench (cost/rounds data)

```bash
pip install swebench
# Or browse leaderboard at https://swebench.com for per-instance cost data
```

### 4. ISBSG (10k+ projects, paid)

Request at https://isbsg.org — free for university research.

## What to Validate

| Dataset | Parameter | Analysis |
|---------|-----------|----------|
| CESAW (203k) | Base rounds, PERT | Fit actual effort distributions to our S/M/L/XL ranges |
| SiP (10k) | Confidence multipliers | Compare PERT predictions to actual overrun rates |
| Project-22 (630) | Story points | Map actual points to our 1-2/3-5/8-13/20-40 ranges |
| Deep-SE (23k) | Story points | Validate point distributions across real projects |
| SWE-bench costs | Token estimation | Back-calculate tokens/round from total cost data |

### 5. AI Coding Benchmarks (for token/agent validation)

```bash
bash datasets/download_benchmarks.sh
```

Downloads:
- **METR Time Horizons** — 228 tasks with human expert duration + agent pass/fail scores ([source](https://github.com/METR/eval-analysis-public))
- **OpenHands SWE-bench** — 1000-row sample from 67k agent trajectories on real GitHub issues ([source](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories))
- **Aider Leaderboard** — ~50 models with cost, tokens, and pass rates ([source](https://github.com/Aider-AI/aider))

Bundled (already in repo):
- **Tokenomics** — per-stage token breakdown from 30 ChatDev tasks (arXiv 2601.14470)
- **onprem.ai tokens** — token estimates for common coding tasks

| Dataset | Parameter | Analysis |
|---------|-----------|----------|
| METR (228) | Agent effectiveness | Fit success rate vs task duration to our S/M/L/XL |
| OpenHands (1k) | Tokens per round | Derive tokens from trajectory metadata |
| Aider (~50 models) | Cost model | Compare reported cost to our tier pricing |
| Tokenomics (30) | Output token ratio | Per-stage token splits vs our 0.25-0.35 |
| onprem.ai (64) | Tokens per task type | Token counts by coding task category |

## Analysis Scripts

Use the estimation calculator (`tests/test_formulas.py`) to generate predictions, then compare against dataset actuals:

```python
from tests.test_formulas import estimate, estimate_tokens

# Generate prediction for an M coding task
pred = estimate(complexity="M", task_type="coding", maturity="partial")
tokens = estimate_tokens(complexity="M", maturity="partial", show_cost=True)

# Compare pred["pert_expected_hours"] against dataset actuals
```
