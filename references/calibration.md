# Calibration: Tuning Estimates with Actuals

## Purpose

Estimation ratios drift over time as teams, tools, and maturity change.
Calibration closes the loop by comparing estimates to actuals and adjusting
the default values in formulas.md.

Research shows calibration feedback improves estimation accuracy from 64% to
81% (Jorgensen & Grimstad, 2004). The goal is to reach and maintain PRED(25).

## Target Metric: PRED(25)

**PRED(25)** = the percentage of estimates where the actual effort falls
within 25% of the PERT expected value.

```
pred_25 = count(abs(actual - pert_expected) / pert_expected <= 0.25) / total_tasks
```

| PRED(25) Score | Rating | Action |
|---------------|--------|--------|
| < 50% | Poor | Calibrate weekly, review all formula inputs |
| 50-65% | Developing | Calibrate bi-weekly, focus on worst-performing task types |
| 65-75% | Good | Calibrate monthly, fine-tune specific multipliers |
| > 75% | Excellent | Calibrate quarterly, maintain reference stories |

Target: PRED(25) >= 75% within 5-10 calibration cycles.

## Actuals Log Format

After completing estimated work, log actuals in this format:

### Per-Task Log Entry

```
| Field | Estimated | Actual | Delta |
|-------|-----------|--------|-------|
| Task | Auth service | — | — |
| Complexity | M | M | — |
| Task Type | coding | coding | — |
| Agent Rounds | 10-26 | 14 | within range |
| Agent Time | 20-78 min | 42 min | within range |
| Human Review | 60 min | 75 min | +25% |
| Human Planning | 30-60 min | 45 min | within range |
| Human Fix | 8-30 min | 22 min | within range |
| Integration | 3-12 min | 10 min | within range |
| PERT Expected | 4 hrs | — | — |
| Actual Total | — | 4.8 hrs | +20% vs PERT |
| Within PRED(25)? | — | Yes | 20% < 25% |
| Risk | medium | — | 1 surprise (auth library) |
| Notes | Review took longer due to unfamiliar auth library |
```

### Batch Log Summary

```
| Metric | Estimated | Actual | Score |
|--------|-----------|--------|-------|
| PERT Expected Total | 65 hrs | 72 hrs | +11% |
| Committed (80%) Total | 91 hrs | 72 hrs | delivered under |
| PRED(25) | — | 28/36 | 78% |
| Tasks over committed | — | 2/36 | 6% |
| Tasks under expected | — | 8/36 | 22% |
| Largest overrun | Task #14 | +65% | flagged |
| Largest underrun | Task #7 | -40% | flagged |
```

## Reference Story Library

Maintain one concrete example per complexity level per task type. These serve
as calibration anchors — when estimating a new task, compare it against
the reference story for that size/type combination.

### Format

```
reference_stories:
  coding:
    S:
      title: "Add 404 error page"
      actual_rounds: 4
      actual_total: 1.2 hrs
      notes: "Single component, clear spec, no API"
    M:
      title: "Stripe payment integration"
      actual_rounds: 15
      actual_total: 4.5 hrs
      notes: "External API, webhook handling, error states"
    L:
      title: "Refactor data layer to ORM"
      actual_rounds: 38
      actual_total: 12 hrs
      notes: "12 tables, raw SQL conversion, migration scripts"
  data-migration:
    L:
      title: "MySQL to PostgreSQL migration"
      actual_rounds: 45
      actual_total: 3 days
      notes: "Schema translation, query rewrite, staged rollout"
  testing:
    M:
      title: "E2E tests for checkout flow"
      actual_rounds: 18
      actual_total: 5 hrs
      notes: "Playwright setup, 8 test scenarios, CI integration"
```

Update reference stories when actuals deviate significantly from existing
references, or when a better representative example is completed.

## Where to Store Logs

Options (choose what fits your workflow):
- **Markdown file** in repo: `estimates/actuals-log.md`
- **Spreadsheet**: export the tables above
- **Tracker**: add actual time to the same issue (native or embedded)
- **JSON**: append to a `calibration-data.json` for programmatic analysis

## Adjustment Rules

After collecting 10+ data points, review patterns and adjust defaults:

### When to Adjust

| Pattern | Adjustment |
|---------|------------|
| PRED(25) < 50% | Major recalibration — review all inputs |
| >60% of tasks exceed committed estimate | Increase confidence multiplier or base rounds |
| >60% of tasks below expected estimate | Decrease base rounds or risk coefficient |
| Human review consistently over | Increase review_minutes lookup values |
| Human fix consistently over | Increase human_fix_ratio |
| Integration consistently over | Increase integration_overhead |
| One complexity band is off, others fine | Adjust that band's rounds only |
| One task type consistently off | Adjust that type's multiplier |
| Maturity improved (faster rounds) | Move to next maturity level |
| Agent effectiveness differs from table | Adjust agent_effectiveness per size |

### How Much to Adjust

Small, incremental changes:
- Rounds: +/- 2-3 per band
- Ratios: +/- 0.05 per cycle
- Minutes per round: +/- 0.5
- Task type multiplier: +/- 0.1
- Agent effectiveness: +/- 0.1

Never adjust more than 20% in a single calibration cycle.

### Calibration Cycle

Recommended cadence based on PRED(25) score:

| PRED(25) | Cadence |
|----------|---------|
| < 50% | Weekly |
| 50-65% | Bi-weekly |
| 65-75% | Monthly |
| > 75% | Quarterly |

Convergence expectation: most teams reach PRED(25) >= 65% within 3-5 cycles
and >= 75% within 8-12 cycles if they consistently log actuals.

## Calibration Metrics

Track these over time:

```
pred_25 = tasks_within_25pct_of_expected / total_tasks
accuracy_rate = tasks_within_range / total_tasks
over_rate = tasks_over_committed / total_tasks
avg_deviation = mean(actual - pert_expected) / pert_expected
bias_direction = sign(avg_deviation)  # positive = consistently under-estimating
```

### Bias Detection

| Bias | Meaning | Fix |
|------|---------|-----|
| avg_deviation > +0.15 | Systematically under-estimating | Increase base rounds or risk coefficient |
| avg_deviation < -0.15 | Systematically over-estimating | Decrease base rounds or risk coefficient |
| High variance, low bias | Inconsistent estimation | Improve reference stories, add decomposition |
| Low variance, high bias | Consistent but wrong | Single multiplier adjustment fixes it |

## Sprint Velocity Tracking

### Completed Points per Sprint

Track story points completed each sprint to build a velocity baseline:

```
sprint_log:
  - sprint: "2026-S1"
    completed_points: 34
    planned_points: 40
    team_size: 4
  - sprint: "2026-S2"
    completed_points: 38
    planned_points: 38
    team_size: 4
  - sprint: "2026-S3"
    completed_points: 31
    planned_points: 36
    team_size: 3  # someone was out
```

### Rolling Velocity Average

Compute rolling velocity over the last 3-5 sprints:

```
rolling_velocity = mean(last_n_sprints.completed_points)  # n = 3 to 5
```

Use the last 3 sprints for fast-changing teams, last 5 for stable teams.

### Capacity Planning Formula

```
available_points = rolling_velocity × (1 - buffer%)
```

Default buffer: **20%** (accounts for unplanned work, bugs, meetings).

| Buffer | Use Case |
|--------|----------|
| 10% | Stable team, low interrupt environment |
| 20% | Standard (default) |
| 30% | New team, high interrupt, or major unknowns |

### Sprint Fit Check

When batch estimating, compare total estimated points against available capacity:

```
total_estimated = sum(task_points)
fit_ratio = total_estimated / available_points
```

| Fit Ratio | Status | Action |
|-----------|--------|--------|
| < 0.8 | Under-planned | Room for more work or buffer is conservative |
| 0.8 - 1.0 | Good fit | Proceed |
| 1.0 - 1.2 | Tight | Flag risk, identify deferrable tasks |
| > 1.2 | Overflow | Must cut scope or split across sprints |

Warn on overflow: "Estimated total ({total_estimated} pts) exceeds sprint
capacity ({available_points} pts). Consider deferring {overflow} points of
lower-priority work."

### Velocity Trend Detection

Compare the last 3 sprints to the previous 3 to detect trends:

```
recent_avg = mean(sprints[-3:].completed_points)
previous_avg = mean(sprints[-6:-3].completed_points)
trend_ratio = recent_avg / previous_avg
```

| Trend Ratio | Label | Interpretation |
|-------------|-------|----------------|
| > 1.10 | Improving | Team is accelerating; may increase capacity |
| 0.90 - 1.10 | Stable | Predictable velocity |
| < 0.90 | Declining | Investigate — burnout, tech debt, team changes? |

### Integration with Batch Estimation

When batch estimating a sprint's worth of work, append a sprint fit summary:

```
Sprint Fit Summary
  Rolling velocity (3-sprint avg): 35 pts
  Buffer: 20%
  Available capacity: 28 pts
  Total estimated: 31 pts
  Fit ratio: 1.11 (Tight)
  Velocity trend: Stable
  ⚠ Consider deferring 3 pts of lower-priority work
```

## Team-Specific Profiles

If multiple teams use this skill, maintain separate calibration profiles:

```
team_profile:
  name: "Backend Team"
  data_points: 47
  pred_25: 0.78
  accuracy_rate: 0.81
  avg_deviation: +0.08
  bias: "slight under-estimation"
  adjustments:
    risk_coefficient: 1.4  (was 1.3)
    human_fix_ratio: 0.25  (was 0.20)
    review_depth_override: deep  (team preference)
    org_overhead: 1.15  (growth-stage company)
  reference_stories: 12 logged
  last_calibrated: 2025-01-15
  next_calibration: 2025-02-15
```
