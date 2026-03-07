# Estimation Frameworks

## 1. Round-Based Framework (Single Agent Tasks)

A "round" is one agent invocation cycle: prompt → reasoning → code/output → validation.

### Complexity-to-Rounds Lookup

| Complexity | Rounds | Description |
|------------|--------|-------------|
| S | 3-8 | Single file/concern, clear spec, minimal integration |
| M | 8-20 | Multi-file, some integration, moderate ambiguity |
| L | 20-50 | Cross-module, significant integration, design decisions |
| XL | 50-120 | Architectural, multi-system, high ambiguity |

### Agent Effectiveness by Size

Based on METR research (2025-2026): AI agents achieve ~100% success on tasks
taking humans <4 minutes, but <10% on tasks >4 hours. Agent capability
"time horizon" doubles every ~7 months.

| Complexity | Agent Effectiveness | Implication |
|------------|-------------------|-------------|
| S | 0.9 | Agent handles ~90%, minimal human correction |
| M | 0.7 | Agent handles ~70%, moderate human intervention |
| L | 0.5 | Agent handles ~50%, significant human steering needed |
| XL | 0.3 | Agent handles ~30%, human-driven with agent assist |

This shifts the human_fix_ratio upward for larger tasks automatically.

### Round Timing

| Maturity Level | Minutes per Round | Notes |
|----------------|-------------------|-------|
| Exploratory | 3-5 | More back-and-forth, corrections |
| Partial | 2-3 | Established patterns, some iteration |
| Mostly-automated | 1-2 | Well-defined prompts, minimal correction |

### Formula

```
agent_rounds = base_rounds × risk_coefficient × domain_familiarity
agent_minutes = agent_rounds × minutes_per_round
integration_minutes = agent_minutes × integration_overhead
human_review_minutes = review_minutes[review_depth][complexity] × org_overhead
human_planning_minutes = planning_minutes[complexity] × org_overhead
human_fix_minutes = agent_minutes × adjusted_fix_ratio × org_overhead
subtotal = agent_minutes + integration_minutes + human_review_minutes + human_planning_minutes + human_fix_minutes
total_minutes = subtotal × task_type_multiplier
→ apply cone of uncertainty spread
→ compute PERT expected value + SD
→ apply confidence multiplier for committed estimate
```

See formulas.md for complete lookup tables, PERT formulas, and all multipliers.

## 2. Cone of Uncertainty

Estimates narrow as work becomes better defined. This is not just time
passing — it requires decisions that eliminate variability.

| Definition Phase | Spread Multiplier | Typical Accuracy |
|-----------------|-------------------|------------------|
| Concept | 2.0x | Estimate can be off by 2-4x |
| Requirements defined | 1.5x | Major decisions made, 1.5-2x variance |
| Design complete | 1.2x | Most unknowns resolved |
| Ready to build | 1.0x | Clear spec, baseline accuracy |

The spread multiplier widens the min/max range around the midpoint without
shifting the expected value. This prevents false precision on early estimates.

**Key insight from research:** The cone narrows only when decisions are made
that eliminate variability — not merely by the passage of time. Short iterations
exploit this by moving quickly from high to low uncertainty.

## 3. Module/Wave Framework (Multi-Agent Projects)

For projects with multiple agents working in parallel or sequence.

### Structure

- **Module**: a discrete unit of work assignable to one agent
- **Wave**: a set of modules that can execute in parallel
- **Sequence**: waves that must execute in order (dependency chain)

### Mapping

1. Break project into modules
2. Assign complexity (S/M/L/XL) per module
3. Estimate each module using round-based framework
4. Group into waves based on dependencies
5. Total wallclock = sum of longest module in each sequential wave

```
Wave 1: [Auth service (M), Email templates (S)]     → parallel, wallclock = max(Auth, Email)
Wave 2: [Payment integration (L)]                    → depends on Wave 1
Wave 3: [Dashboard (M), Reports (M)]                → parallel, depends on Wave 2
Total wallclock = Wave1.max + Wave2.max + Wave3.max
Total effort = sum of all modules
```

### Multi-Agent Scaling

```
parallel_speedup = min(num_agents, modules_in_wave)
wave_wallclock = longest_module_in_wave
coordination_overhead = 10% per additional agent beyond 1
```

## 4. S-M-L Conversion (Backlog Import / Rough Sizing)

For quick sizing when you have a list of tasks without detailed specs.

### Defaults (Agent-Assisted, Coding Type, 80% Confidence)

| Size | Agent Rounds | Agent Time | Human Time | Expected (PERT) | Committed (80%) |
|------|-------------|------------|------------|-----------------|-----------------|
| S | 3-8 | 6-24 min | 45-75 min | ~1.2 hrs | ~1.5 hrs |
| M | 8-20 | 16-60 min | 1.5-3 hrs | ~3 hrs | ~4 hrs |
| L | 20-50 | 40-150 min | 3-7 hrs | ~7 hrs | ~10 hrs |
| XL | 50-120 | 100-360 min | 6-16 hrs | ~2.5 days | ~3.5 days |

These are baseline ranges at partial maturity, 1 human + 1 agent, risk 1.0,
coding task type (1.0x), solo/startup org. For other contexts, apply multipliers:

- Task type: data-migration 2.0x, infrastructure 1.5x, testing 1.3x, bug-fix 1.2x, design 1.2x
- Org size: growth 1.15x (human time), enterprise 1.3x (human time)
- Confidence: 50% use 1.0x, 90% use 1.8x

### Story Points (Optional, On Request)

```
S  = 1-2 points
M  = 3-5 points
L  = 8-13 points
XL = 20-40 points
```

Warning: Story points measure relative complexity, not time. This mapping
is a starting reference only — calibrate with your team's actual velocity.
Do NOT convert story points to hours for reporting.

### Batch Rollup

For a batch of N tasks:

```
total_effort = sum(each task's total range)
total_wallclock = sequenced effort (respecting dependencies)
parallel_wallclock = total_wallclock / parallel_speedup
```

## 5. Dependency Sequencing (Batch Estimates)

When estimating multiple tasks, identify:

- **Independent**: can run in any order or parallel
- **Sequential**: must complete before next starts
- **Partially dependent**: can start after a milestone in the blocker (not full completion)

### Sequencing Rules

1. Build a dependency graph from task list
2. Identify the critical path (longest sequential chain)
3. Wallclock estimate = critical path duration
4. Effort estimate = sum of all tasks (regardless of sequencing)
5. Flag circular dependencies as errors

### Visualization (for batch output)

```
[Auth (M)] ──→ [Payment (L)] ──→ [Dashboard (M)]
[Email (S)] ─────────────────────→ [Reports (M)]

Critical path: Auth → Payment → Dashboard = 10.5 hrs
Parallel work: Email + Reports overlap with main chain
```

## 6. Re-estimation Triggers

Flag for re-estimation when:

| Trigger | Action |
|---------|--------|
| Scope change | Re-run intake for affected tasks |
| Blocked >1 day | Reassess dependencies, adjust wallclock |
| Midpoint drift >30% | Re-estimate remaining work with actuals so far |
| Team change | Recalculate with new human/agent counts |
| Maturity shift | Update minutes-per-round, recompute |
| New information | Update risk coefficient, domain familiarity |
| Definition phase advances | Narrow the cone of uncertainty spread |

## 7. Estimation Anti-Patterns (Guards)

The skill should actively warn against these research-identified anti-patterns:

| Anti-Pattern | Why It's Harmful | Guard |
|-------------|-----------------|-------|
| Single-point estimates | Creates false certainty, sets up failure | Always output ranges + PERT expected |
| Converting points to hours | Defeats relative sizing, invites gaming | Warn if user requests conversion |
| Estimating in isolation | Misses edge cases, QA concerns, ops issues | Suggest team review for L/XL tasks |
| Estimates as commitments | Teams pad defensively, trust erodes | Separate "expected" from "committed" |
| Velocity as performance metric | Teams game velocity, quality suffers | Never present velocity as productivity |
| Estimating everything upfront | Waste — stories become outdated | Recommend just-in-time estimation |
| XL tasks without decomposition | High uncertainty, low accuracy | Suggest breaking down XL items |
