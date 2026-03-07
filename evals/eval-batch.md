# Eval: Batch Estimation

## Purpose
Verify batch mode handles multiple tasks with mixed types, dependencies,
PERT rollup, and anti-pattern guards correctly.

## Test Prompt

```
Estimate these tasks in quick batch mode. 2 humans, 2 agents, partial maturity.

1. Set up CI/CD pipeline
2. Implement user authentication
3. Build REST API for products (depends on #2)
4. Create admin dashboard (depends on #3)
5. Add search functionality (depends on #3)
6. Write API documentation
7. Set up monitoring and alerts (depends on #1)
```

## Expected Behaviors

1. Accepts the plain list input without asking for reformatting
2. Auto-assigns complexity (S/M/L/XL) to each task
3. Auto-assigns task_type to each task:
   - #1: infrastructure
   - #2: coding
   - #3: coding
   - #4: coding
   - #5: coding
   - #6: coding (or design)
   - #7: infrastructure
4. Shows confirmation table with inferred sizes and types before estimating
5. Respects stated dependencies
6. Produces a summary table FIRST with all 7 tasks including:
   - Task, size, type, rounds, agent time, human time, expected (PERT), committed (80%), risk, deps
7. Rollup block follows with:
   - Total effort (expected and committed)
   - Wallclock with parallelism noted
   - Critical path identified
   - Team composition
   - Size distribution
   - PERT expected total
8. Critical path follows dependency chain (likely #2 → #3 → #4 or #5)
9. Independent tasks (#1, #6) shown as parallelizable
10. Multi-agent/multi-human scaling applied to rollup
11. Infrastructure tasks (#1, #7) have 1.5x task_type_multiplier
12. Warnings block present if any anti-patterns triggered
13. Offers per-task detail as optional expansion

## Verification Checks

- All 7 tasks appear in the output
- Dependencies match the input (#3 depends on #2, #4 on #3, etc.)
- Wallclock < total effort (parallelism with 2 agents + 2 humans)
- Critical path is the longest sequential chain
- Size distribution adds up to 7
- Infrastructure tasks (#1, #7) show higher estimates than equivalent coding tasks
- PERT expected total is between min and max effort
- Committed total is approximately 1.4x expected (80% confidence)

## Failure Conditions

- Asks for tasks one at a time instead of processing the batch
- Ignores dependencies (treats all as independent)
- Missing tasks in output (fewer than 7)
- No rollup / summary — only individual estimates
- Wallclock equals total effort despite parallel capacity
- Critical path is incorrect given the dependency graph
- Task types not assigned (all default to "coding")
- No PERT expected values in batch table
- No warnings block even when warranted
