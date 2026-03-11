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

## Analysis Scripts

Use the estimation calculator (`tests/test_formulas.py`) to generate predictions, then compare against dataset actuals:

```python
from tests.test_formulas import estimate, estimate_tokens

# Generate prediction for an M coding task
pred = estimate(complexity="M", task_type="coding", maturity="partial")
tokens = estimate_tokens(complexity="M", maturity="partial", show_cost=True)

# Compare pred["pert_expected_hours"] against dataset actuals
```
