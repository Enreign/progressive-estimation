# Eval: Detailed Path — Hybrid Team

## Purpose
Verify detailed estimation with multiple humans and agents produces correct
multi-team scaling, PERT statistics, confidence levels, org overhead, and
cone of uncertainty adjustments.

## Test Prompt

```
I need a detailed estimate for migrating our monolith's user service to a
standalone microservice. We have 3 developers and 2 agents. The team is
familiar with the domain but this is our first microservice extraction.

Details:
- Risk: unknown API surface, external service dependencies
- Integration: heavy (existing systems)
- Domain: familiar but new territory for microservice extraction
- Review depth: deep
- Human fix ratio: significant (30-50%)
- Confidence: 90% (external deadline)
- Definition phase: requirements defined
- Org size: growth (25 people)
- We use JIRA with embedded mode.
```

## Expected Behaviors

1. Asks all detailed-path questions (or accepts the provided answers)
2. Complexity assigned as L or XL
3. Task type: infrastructure (1.5x) or coding (1.0x) — either acceptable
4. Domain familiarity: somewhat new (1.3x) — familiar domain but new pattern
5. Risk coefficient elevated (1.5-2.0) from risk factors:
   - Unknown API surface: +0.3
   - External service dependencies: +0.2
   - Base 1.0 + increments
6. Integration overhead: 0.25 (heavy)
7. Human fix ratio: 0.30-0.50 (significant)
8. Confidence multiplier: 1.8x (90% commitment)
9. Spread multiplier: 1.5x (requirements defined phase)
10. Org overhead: 1.15x (growth)
11. Agent effectiveness applied for the assigned size (0.5 for L, 0.3 for XL)
12. Multi-human adjustment: 3 developers with communication overhead (1.3x)
13. Multi-agent adjustment: 2 agents with coordination overhead (1.1x)
14. Output starts with one-line summary including Expected and Committed (90%)
15. PERT block with SD and confidence bands shown
16. JIRA embedded format used (markdown table in Description)
17. Subtasks generated for logical extraction phases
18. Anti-pattern warnings triggered if task is XL

## Verification Checks

- `num_humans=3` and `num_agents=2` appear in the team field
- Communication overhead (15% per extra human) is applied to human time
- Coordination overhead (10% per extra agent) is applied to agent time
- Org overhead (1.15x) is applied to human time only
- Wallclock time is less than total effort (parallelism)
- Committed estimate is 1.8x the expected (90% confidence)
- Range is widened by 1.5x spread (requirements defined)
- JIRA output uses Description field, not custom fields

## Failure Conditions

- Skips detailed questions and jumps to estimate
- Ignores multi-team scaling (same estimate as 1 human + 1 agent)
- Uses native JIRA mode when embedded was specified
- Wallclock equals total effort despite multiple agents
- Omits PERT expected value or confidence bands
- Committed estimate uses 80% (1.4x) instead of requested 90% (1.8x)
- Domain familiarity set to "expert" despite first microservice extraction
- Cone of uncertainty spread not applied despite requirements-only phase
