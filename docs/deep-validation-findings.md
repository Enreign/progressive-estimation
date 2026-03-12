# Deep Validation: Combined Findings & Recommendations

> **Generated:** 2026-03-12 | **Script:** `tests/deep_validation.py` (11 analyses)
> **Data:** 86k+ software estimation tasks + AI coding benchmarks (24k METR runs, 93 Aider entries, 30 Tokenomics phases, 10 onprem tasks)

## Executive Summary

53 parameters audited across 11 analyses using bootstrap CIs (n=1000, seed=42) and KS goodness-of-fit tests. **22 ADJUST, 7 FLAG, 24 KEEP.**

The formula's core structure is sound — most parameters land within acceptable ranges. The biggest issues are: (1) the PERT-beta assumption is wrong (log-normal fits better), (2) the 90% confidence multiplier is too aggressive (under-delivers everywhere), (3) review time estimates are 2-6x too high, and (4) AGENT_EFFECTIVENESS for M/L tasks is far too optimistic.

---

## Recommended Changes

### 1. PERT Distribution Assumption → Log-Normal

| Band | n | KS D (log-normal) | KS D (beta) | Winner |
|------|---|-------------------|-------------|--------|
| S | 61,514 | 0.073 | 0.178 | log-normal |
| M | 16,611 | 0.086 | 0.101 | log-normal |
| L | 4,000 | 0.108 | 1.000 (fit failed) | log-normal |
| XL | 1,459 | 0.094 | 0.249 | log-normal |

**Recommendation: ADJUST.** Log-normal beats PERT-beta in all 4 bands. The practical impact is that PERT underestimates tail risk — real effort distributions have heavier right tails than beta allows. Consider switching the three-point estimate from PERT-weighted `(O + 4M + P) / 6` to log-normal parameterization using the same min/max/mode inputs.

**Data:** CESAW (61k tasks, person-hours) + SiP (12k tasks) + Renzo (10k tasks, Pomodoro units) from [Derek Jones Software Estimation Datasets](https://github.com/Derek-Jones/Software-estimation-datasets).

**Caveat:** This is human-only estimation data (pre-AI). The distribution shape may differ for AI-assisted work, but no large-scale AI task duration dataset exists yet.

---

### 2. Confidence Multipliers → Size-Dependent

**Current:** Flat 1.0x / 1.4x / 1.8x for 50% / 80% / 90% across all sizes.

| Band | 50% | | 80% | | 90% | |
|------|-----|-|-----|-|-----|-|
| | Current | Optimal | Current | Optimal | Current | Optimal |
| S | 1.0x ✓ | 1.00x | **1.4x** | **1.77x** | **1.8x** | **2.92x** |
| M | 1.0x ✓ | 0.93x | 1.4x ✓ | 1.42x | **1.8x** | **2.12x** |
| L | 1.0x ✓ | 0.93x | 1.4x ✓ | 1.39x | 1.8x ✓ | 2.02x |
| XL | **1.0x** | **0.73x** | 1.4x ✓ | 1.46x | **1.8x** | **2.20x** |

**Recommendation: ADJUST the 90% multiplier everywhere (1.8x → 2.0-2.9x), and the 80% S multiplier (1.4x → 1.77x).**

The 50% and 80% multipliers are well-calibrated for M/L/XL. The 90% multiplier under-delivers in every band — it currently captures only 80-88% of tasks, not 90%. Small tasks need the largest correction because their actual/estimate ratio has the widest spread.

**Data:** 84k estimate-actual pairs from CESAW + SiP + Renzo + Project-22. Bootstrap 95% CIs from 1000 resamples.

---

### 3. Review Minutes → Lower Values

| Band | Current | Recommended | 95% CI | n |
|------|---------|-------------|--------|---|
| S | 30 min | 17 min | [15, 21] | 84 |
| M | 60 min | 20 min | [17, 23] | 197 |
| L | 120 min | 19 min | [15, 20] | 9 |
| XL | 240 min | — (no data) | — | 0 |

**Recommendation: ADJUST with caveat.** Data shows 17-20 minute medians regardless of size, which is much lower than our lookup. However, the data is from Project-22 code reviews of human-written code (n=290 joined reviews), not AI-generated code reviews which are the primary use case for our formula.

**Suggested action:** Lower S to 20 min, M to 30 min, keep L/XL as-is until AI review time data is available. The current values may be appropriate for AI-generated code which requires more careful review.

**Data:** [Project-22](https://github.com/Derek-Jones/Software-estimation-datasets) — 1,441 reviews joined to 616 stories via Branch. OLS regression R²=0.039 (story points are a weak predictor of review time).

---

### 4. AGENT_EFFECTIVENESS → Lower for M/L

| Band | Current | METR Observed | 95% CI | n |
|------|---------|--------------|--------|---|
| S | 0.9 | 0.832 | [0.83, 0.84] | 18,207 |
| M | **0.7** | **0.252** | [0.24, 0.26] | 4,019 |
| L | **0.5** | **0.147** | [0.13, 0.16] | 1,687 |
| XL | 0.3 | 0.221 | [0.15, 0.32] | 95 |

**Recommendation: ADJUST M and L, but NOT a direct replacement.**

Critical distinction: METR measures *autonomous completion rate* (binary pass/fail on 228 task types across ~24k runs). Our `AGENT_EFFECTIVENESS` measures *work acceleration* — an agent that fails to fully solve a task can still provide 50%+ of the solution (code scaffolding, research, partial implementation). These are fundamentally different metrics.

**Suggested action:** Use METR as a lower bound. Reasonable adjusted values:
- M: 0.7 → 0.5 (METR shows 0.25, but partial credit brings real acceleration higher)
- L: 0.5 → 0.35 (METR shows 0.15, same partial-credit argument)
- S and XL: keep as-is (within range)

**Data:** [METR eval-analysis-public](https://github.com/METR/eval-analysis-public) — 24,008 runs across 228 tasks with human expert duration estimates. Top agents: Claude Opus 4.6 (0.837), GPT-5.3-Codex (0.803), GPT-5 (0.797).

---

### 5. BASE_ROUNDS → Wider Ranges

| Band | Current | Implied (p25-p75) | 95% CI |
|------|---------|-------------------|--------|
| S | (3, 8) | (4, 21) | [3.9, 21.7] |
| M | (8, 20) | (15, 67) | [14.3, 67.3] |
| L | (20, 50) | (59, 185) | [56.4, 192.2] |
| XL | (50, 120) | (174, 757) | [155.9, 816.1] |

**Recommendation: ADJUST with major caveat.** The implied rounds are derived by inverting the formula against human-only actual effort data. Our formula models AI-assisted work which should compress rounds significantly. The current ranges may be correct for the *AI-assisted* scenario; the data just shows they're too narrow for *human-only* work.

**Suggested action:** Widen the upper bound modestly (e.g., S: 3-12, M: 8-30, L: 20-80, XL: 50-200) rather than adopting the full implied range. The current min values are approximately correct.

**Data:** 37,867 tasks from CESAW + SiP + Project-22 + Renzo, classified by estimated hours into S/M/L/XL bands.

---

### 6. OUTPUT_TOKEN_RATIO → Raise S/M Slightly

| Band | Current | Observed | 95% CI | Verdict |
|------|---------|----------|--------|---------|
| S | 0.25 | 0.392 | [0.32, 0.47] | ADJUST |
| M | 0.28 | 0.392 | [0.32, 0.47] | ADJUST |
| L | 0.30 | 0.392 | [0.32, 0.47] | KEEP |
| XL | 0.35 | 0.392 | [0.32, 0.47] | KEEP |

**Recommendation: ADJUST S to 0.30, M to 0.30.** The observed 0.39 is inflated by Tokenomics data which includes reasoning tokens (median 0.68 for Tokenomics vs 0.31 for Aider). Aider's 0.31 (which excludes thinking tokens) is the more relevant comparison. Current L/XL values are fine.

**Data:** 23 Aider model entries + 6 Tokenomics phase entries (n=29 combined). Aider from [Aider leaderboard](https://github.com/Aider-AI/aider). Tokenomics from [arXiv 2601.14470](https://arxiv.org/abs/2601.14470).

---

### 7. Cost Model (Standard Tier) → Over-Estimates

| Tier | Formula | Observed Median | Ratio | n |
|------|---------|----------------|-------|---|
| Economy | $0.042 | $0.038 | 0.9x ✓ | 23 |
| **Standard** | **$0.205** | **$0.030** | **0.1x** | 56 |
| Premium | $0.420 | $0.292 | 0.7x ✓ | 14 |

**Recommendation: FLAG (not a direct formula change).** The standard tier over-estimate is because Aider benchmark cases are single-function edits (~S complexity with 1 round), while our formula estimates multi-round sessions. The formula is correct for its intended use; the benchmark just tests a simpler scenario.

**Data:** 93 Aider leaderboard entries mapped to model tiers by pricing. [Aider leaderboard](https://github.com/Aider-AI/aider).

---

### 8. Task Type Multipliers → Flatter Than Expected

| Type | Current | SiP Observed | 95% CI | n |
|------|---------|-------------|--------|---|
| coding | 1.0x | 1.00x | [1.00, 1.00] | 3,072 |
| bug-fix | 1.3x | 1.00x | [1.00, 1.00] | 2,308 |
| infrastructure | 1.5x | 1.00x | [1.00, 1.00] | 1,244 |

**Recommendation: KEEP with caveat.** SiP data shows all categories have identical median overrun ratios (1.00x), suggesting the multipliers don't affect *relative overrun*. However, this could mean the team already accounts for task type in their estimates (i.e., bug-fixes get estimated higher). The multipliers model *absolute effort differences* which the ratio analysis can't capture. CESAW phase data is directionally consistent (most phases cluster around 1.0x relative to code baseline).

**Data:** SiP 12k tasks from [Derek Jones datasets](https://github.com/Derek-Jones/Software-estimation-datasets). 3 categories mapped: Enhancement→coding, Bug→bug-fix, In House Support→infrastructure.

---

### 9. Human Fix Ratio → Current Value Conservative but OK

| | Current | Observed | 95% CI | n |
|-|---------|----------|--------|---|
| human_fix_ratio | 0.20 | 0.129 | [0.11, 0.15] | 1,156 |

**Recommendation: KEEP.** Proxy from code review cycles (85% single-pass, 10% two rounds, 5% three+). The 0.129 is a lower bound because it only captures review-cycle rework, not debugging or refactoring rework. Current 0.20 is conservative but defensible.

**Data:** Project-22 — 1,156 unique branches with review cycle counts.

---

## Parameters With No Data (FLAG)

| Parameter | Current | Impact (Sensitivity) | Status |
|-----------|---------|---------------------|--------|
| `integration_overhead` | 0.15 | 6-7% of estimate | No proxy available |
| `minutes_per_round` | 1-5 by maturity | Foundational parameter | No public round-level timing data exists |
| `tokens_per_case` | 6,000/round (S) | — | Aider shows 18k/case but cases ≠ rounds |

`review_depth` and `risk_coefficient` are flagged in sensitivity analysis as high-impact parameters (42-57% and 40-53% of estimate respectively for S/M/L/XL) that lack dedicated validation data.

---

## Sensitivity Rankings (Most to Least Impact)

For a medium (M) task with default settings:

| Rank | Parameter | Impact Range | % of Base |
|------|-----------|-------------|-----------|
| 1 | review_depth | 146–236 min | 51% |
| 2 | risk_coefficient | 160–242 min | 47% |
| 3 | maturity | 150–220 min | 40% |
| 4 | domain_familiarity | 162–212 min | 29% |
| 5 | org_size | 176–211 min | 20% |
| 6 | human_fix_ratio | 168–190 min | 13% |
| 7 | integration_overhead | 171–183 min | 7% |
| 8 | confidence_level | 176–176 min | 0% |
| 9 | definition_phase | 176–176 min | 0% |

The top 3 parameters account for ~90% of estimate variance. `confidence_level` and `definition_phase` show zero sensitivity because they apply as post-hoc adjustments, not to the base calculation.

---

## Summary Action Table

| # | Parameter | Action | Current → Suggested | Priority |
|---|-----------|--------|--------------------|----|
| 1 | 90% confidence multiplier | **ADJUST** | 1.8x → size-dependent (2.0–2.9x) | High |
| 2 | AGENT_EFFECTIVENESS M/L | **ADJUST** | 0.7/0.5 → 0.5/0.35 | High |
| 3 | PERT assumption | **ADJUST** | Beta → Log-normal | Medium |
| 4 | review_minutes S/M | **ADJUST** | 30/60 → 20/30 | Medium |
| 5 | OUTPUT_TOKEN_RATIO S/M | **ADJUST** | 0.25/0.28 → 0.30/0.30 | Low |
| 6 | 80% confidence multiplier S | **ADJUST** | 1.4x → 1.77x | Medium |
| 7 | BASE_ROUNDS upper bounds | **ADJUST** | Widen ~50% | Low |
| 8 | Standard tier cost formula | **FLAG** | Over-estimates 7x for simple cases | Low |
| 9 | task_type_mult infrastructure | **KEEP** | Data inconclusive | — |
| 10 | human_fix_ratio | **KEEP** | 0.20 (conservative, defensible) | — |
| 11 | integration_overhead | **FLAG** | No data | — |
| 12 | minutes_per_round | **FLAG** | No data | — |

---

## Data Sources

| Dataset | Size | Source | Used In |
|---------|------|--------|---------|
| CESAW | 61,514 tasks | [Derek Jones](https://github.com/Derek-Jones/Software-estimation-datasets) | Analyses 1, 2, 4, 6 |
| SiP | 12,100 tasks | [Derek Jones](https://github.com/Derek-Jones/Software-estimation-datasets) | Analyses 2, 4, 6 |
| Renzo Pomodoro | 10,464 tasks | [Derek Jones](https://github.com/Derek-Jones/Software-estimation-datasets) | Analyses 2, 6 |
| Project-22 | 616 stories + 1,441 reviews | [Derek Jones](https://github.com/Derek-Jones/Software-estimation-datasets) | Analyses 3, 5 |
| METR Time Horizons | 24,008 runs / 228 tasks | [METR](https://github.com/METR/eval-analysis-public) | Analysis 8 |
| Aider Leaderboard | ~50 models / 93 entries | [Aider](https://github.com/Aider-AI/aider) | Analyses 9, 10, 11 |
| Tokenomics (ChatDev) | 30 tasks / 6 phases | [arXiv 2601.14470](https://arxiv.org/abs/2601.14470) | Analyses 9, 10 |
| onprem.ai | 10 coding tasks | Bundled (`datasets/benchmarks/onprem-tokens.csv`) | Analysis 9 |

**Total data points:** ~110k (86k estimation + 24k agent runs)

---

## Reproducing

```bash
# Install datasets
git clone https://github.com/Derek-Jones/Software-estimation-datasets.git datasets/derek-jones
bash datasets/download_benchmarks.sh  # METR, OpenHands, Aider

# Optional: pip install scipy numpy (for KS distribution tests)

# Run all 11 analyses
python3 tests/deep_validation.py

# Run individual analysis
python3 tests/deep_validation.py --analysis distribution
python3 tests/deep_validation.py --analysis effectiveness
python3 tests/deep_validation.py --analysis cost
python3 tests/deep_validation.py --list  # show all analysis names
```
