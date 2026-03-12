# Eval: Regression — Known-Good Baseline

## Purpose
Detect when model updates or skill changes cause estimate drift from
established baselines. Run this eval after any change to formulas.md,
frameworks.md, or SKILL.md.

## Baseline Test Cases

### Case 1: Trivial Task (S, coding)

**Input:**
```
Quick mode. "Add a 404 error page to our Next.js app."
1 human, 1 agent, mostly-automated maturity.
```

**Expected ranges:**
- Complexity: S
- Task type: coding (1.0x)
- Agent effectiveness: 0.9
- Agent rounds: 4-10
- Expected (PERT): 0.5-1.5 hrs
- Committed (80%): 0.7-2 hrs
- Risk: low
- No anti-pattern warnings

### Case 2: Medium Task (M, coding)

**Input:**
```
Quick mode. "Add Stripe payment integration to checkout flow."
1 human, 1 agent, partial maturity.
```

**Expected ranges:**
- Complexity: M
- Task type: coding (1.0x)
- Agent effectiveness: 0.5
- Agent rounds: 10-26
- Expected (PERT): 2-5 hrs
- Committed (80%): 2-7 hrs
- Risk: medium

### Case 3: Large Task (L, data-migration)

**Input:**
```
Quick mode. "Migrate production database from MySQL to PostgreSQL,
including schema, queries, and data migration."
1 human, 1 agent, exploratory maturity.
```

**Expected ranges:**
- Complexity: L
- Task type: data-migration (2.0x)
- Agent effectiveness: 0.35
- Agent rounds: 26-65
- Expected (PERT): 1-3 days
- Committed (80%): 1-4 days
- Risk: high
- Warning triggered: "Consider phased delivery"

### Case 4: XL Task (decomposition warning)

**Input:**
```
Quick mode. "Rewrite the entire backend from Express.js to Rust/Axum,
including all 40+ API endpoints, database layer, auth, and deployment."
1 human, 1 agent, exploratory maturity.
```

**Expected ranges:**
- Complexity: XL
- Agent effectiveness: 0.3
- Agent rounds: 65-156
- Expected (PERT): 15-40 hrs (2-5 days)
- Committed (80%): 20-55 hrs (3-7 days)
- Risk: high
- Warning: "Consider breaking this into smaller tasks"
- Warning: "This estimate has high uncertainty"
- Warning: "XL estimates are directional only"

> **Note:** XL estimates are intentionally capped by the round-based model.
> The anti-pattern guard strongly recommends decomposition — treat XL numbers
> as rough sizing, not commitments.

### Case 5: Batch Consistency

**Input:**
```
Quick batch mode. 1 human, 1 agent, partial.
1. Fix login bug
2. Add user profile page
3. Implement role-based access control
```

**Expected:**
- Task types auto-assigned: bug-fix, coding, coding
- Bug fix has 1.3x multiplier applied
- Individual estimates consistent with Cases 1-3 ranges for their sizes
- PERT expected total is between batch min and max
- Committed total reflects size-dependent multipliers (S: 1.8x, M: 1.4x, L: 1.4x)

### Case 6: Confidence Level Comparison

**Input (run twice):**
```
Quick mode. "Build a REST API for user management with CRUD operations."
1 human, 1 agent, partial maturity.
```

Run once with 50% confidence, once with 90% confidence.

**Expected:**
- Same PERT expected value for both
- 50% committed = expected × 1.0 (for M)
- 90% committed = expected × 2.1 (for M, size-dependent)
- Ratio between the two committed values should be ~2.1

## Regression Criteria

An estimate is a **regression** if:
- Complexity assignment changes from baseline (S→M, M→L, etc.)
- Task type not auto-assigned when it should be
- PERT expected falls outside the expected range by >50%
- Committed estimate is not approximately confidence_multiplier × expected
- Required output fields are missing (PERT, confidence bands, warnings)
- Output ordering changes (summary not first)
- Anti-pattern warnings not triggered when they should be
- Canonical JSON structure changes

## Running This Eval

1. Run all 6 cases against the current skill version
2. Compare outputs to expected ranges above
3. Flag any regressions
4. If regressions found, check which reference file changed and why
5. Update baselines only when the change is intentional and validated
