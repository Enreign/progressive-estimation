# Eval: Quick Path — Single Task

## Purpose
Verify the quick estimation path produces a valid estimate with minimal input,
including PERT expected value, confidence bands, and anti-pattern guards.

## Test Prompt

```
Estimate this task: "Add a password reset flow to our Express.js app.
It needs email sending, token generation, and a reset form."
Use quick mode. 1 human, 1 agent, partial automation.
```

## Expected Behaviors

1. Does NOT ask more than 4 questions (quick path)
2. Auto-assigns task type as "coding" (1.0x multiplier)
3. Assigns complexity M or L (either is acceptable)
4. Produces a one-line summary FIRST including Expected and Committed values
5. Includes PERT expected value with standard deviation
6. Shows confidence bands (68% and 95%)
7. Shows both "expected" and "committed (80%)" estimates
8. Breakdown table includes all canonical fields from formulas.md
9. Agent effectiveness adjustment applied (0.7 for M, 0.5 for L)
10. Risk level is medium (API/email integration, moderate ambiguity)
11. Applies default values (risk=1.3, integration=15%, org=solo-startup, etc.)
12. Offers tracker output as a follow-up, does not assume a tracker

## Verification Checks

- PERT expected value is between the min and max range
- Committed (80%) value is approximately 1.4x the expected value
- Standard deviation is (max - min) / 6
- Agent effectiveness for the assigned complexity is reflected in human fix ratio

## Failure Conditions

- Asks 5+ questions before producing an estimate
- Omits the one-line summary or PERT expected value
- Shows only a range without PERT expected and committed values
- Committed estimate is lower than expected estimate
- Forgets to mention agent rounds or human review time
- No confidence bands shown
