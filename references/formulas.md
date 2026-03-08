# Canonical Formulas

This file is the single source of truth for all estimation arithmetic.
Claude uses these formulas inline. They also serve as the spec for generating
standalone calculator scripts in any language.

## Inputs

| Input | Type | Default | Range |
|-------|------|---------|-------|
| complexity | S/M/L/XL | M | — |
| task_type | coding/bug-fix/investigation/infrastructure/data-migration/testing/design | coding | — |
| num_humans | integer | 1 | 1-20 |
| num_agents | integer | 1 | 1-10 |
| maturity | exploratory/partial/mostly-automated | partial | — |
| risk_coefficient | float | 1.3 | 1.0-2.5 |
| integration_overhead | float | 0.15 | 0.05-0.30 |
| domain_familiarity | float | 1.0 | 0.8-1.5 |
| human_fix_ratio | float | 0.20 | 0.05-0.50 |
| review_depth | light/standard/deep | standard | — |
| confidence_level | 50/80/90 | 80 | — |
| definition_phase | concept/requirements/design/ready | ready | — |
| org_size | solo-startup/growth/enterprise | solo-startup | — |

## Lookup Tables

### Base Rounds by Complexity

```
S:  min=3,   max=8
M:  min=8,   max=20
L:  min=20,  max=50
XL: min=50,  max=120
```

### Task Type Multiplier

Different kinds of work have different lifecycle overhead beyond pure coding.
This multiplier accounts for planning, environment setup, deployment,
coordination, testing, and non-coding effort.

```
coding:          1.0   (baseline — mostly code, some review)
bug-fix:         1.2   (debugging overhead, reproduction, regression testing)
investigation:   0.5   (timebox — output is a plan/report, not code)
design:          1.2   (mockups, iteration with stakeholders, design system alignment)
testing:         1.3   (test environment setup, fixture creation, flakiness debugging)
infrastructure:  1.5   (environment provisioning, CI/CD config, deployment verification)
data-migration:  2.0   (migration planning, data validation, rollback strategy, staged rollout)
```

Apply task_type_multiplier to the TOTAL estimate (not just agent rounds),
because lifecycle overhead affects all phases — agent work, human review,
integration, and fixes.

### Agent Effectiveness by Task Size

Based on METR research: agent success rate drops sharply as task complexity
grows. This shifts effort from agent to human for larger tasks.

```
S:  agent_effectiveness = 0.9   (agents handle ~90% of work well)
M:  agent_effectiveness = 0.7   (agents handle ~70%, more human intervention)
L:  agent_effectiveness = 0.5   (agents handle ~50%, significant human steering)
XL: agent_effectiveness = 0.3   (agents handle ~30%, mostly human-driven)
```

Effect: increases human_fix_ratio for larger tasks.

```
adjusted_human_fix_ratio = human_fix_ratio + (1 - agent_effectiveness) × 0.3
```

### Minutes per Round by Maturity

```
exploratory:       min=3, max=5
partial:           min=2, max=3
mostly-automated:  min=1, max=2
```

### Review Minutes by Depth and Complexity

Human review time — how long a human spends reviewing, testing, and
verifying the agent's output.

```
            S      M      L      XL
light:      15     30     60     120
standard:   30     60     120    240
deep:       60     120    240    480
```

### Human Planning & Coordination Minutes by Complexity

Non-review human time: thinking, discussing, making decisions, writing specs,
coordinating with others. This is SEPARATE from review time.

```
S:   15-30 min
M:   30-60 min
L:   60-180 min
XL:  120-480 min
```

### Confidence Level Multiplier

Based on James Shore's risk management research. Applied to the final
estimate to convert from "expected" to "committable."

```
50%:  1.0   (stretch goal — equal chance of over/under)
80%:  1.4   (likely — reasonable buffer for unknowns)
90%:  1.8   (safe commitment — high confidence delivery)
```

Quick path defaults to 80%. Detailed path asks the user.

### Cone of Uncertainty — Definition Phase Spread

How defined the work is affects the width of the estimate range.
Applied as a multiplier to the spread between min and max.

```
concept:       spread_multiplier = 2.0   (very wide range, high uncertainty)
requirements:  spread_multiplier = 1.5   (narrowing, major decisions made)
design:        spread_multiplier = 1.2   (most unknowns resolved)
ready:         spread_multiplier = 1.0   (baseline — ready to build)
```

Effect: widens the gap between min and max estimates without shifting
the midpoint. Applied after all other calculations.

```
midpoint = (total_min + total_max) / 2
half_spread = (total_max - total_min) / 2 × spread_multiplier
adjusted_min = midpoint - half_spread
adjusted_max = midpoint + half_spread
```

### Organization Size Overhead

Larger organizations have more process, coordination, and review overhead.

```
solo-startup:  1.0    (minimal process, fast decisions)
growth:        1.15   (some process, light review, moderate coordination)
enterprise:    1.3    (formal review, compliance, multi-team coordination)
```

Applied to human time only (planning, review, fix), not agent time.

## Formulas

### Step 1: Agent Rounds

```
adjusted_rounds_min = base_rounds_min × risk_coefficient × domain_familiarity
adjusted_rounds_max = base_rounds_max × risk_coefficient × domain_familiarity
```

Round to nearest integer.

### Step 2: Agent Time

```
agent_minutes_min = adjusted_rounds_min × minutes_per_round_min
agent_minutes_max = adjusted_rounds_max × minutes_per_round_max
```

### Step 3: Integration Time

```
integration_minutes_min = agent_minutes_min × integration_overhead
integration_minutes_max = agent_minutes_max × integration_overhead
```

### Step 4: Human Fix Time (Agent Effectiveness Adjusted)

```
adjusted_fix_ratio = human_fix_ratio + (1 - agent_effectiveness[complexity]) × 0.3
human_fix_minutes_min = agent_minutes_min × adjusted_fix_ratio
human_fix_minutes_max = agent_minutes_max × adjusted_fix_ratio
```

### Step 5: Human Review Time

```
human_review_minutes = review_minutes[review_depth][complexity]
```

(Fixed value, not a range.)

### Step 6: Human Planning & Coordination Time

```
human_planning_min = planning_minutes[complexity].min
human_planning_max = planning_minutes[complexity].max
```

### Step 7: Apply Org Size Overhead (Human Time Only)

```
human_review_adjusted = human_review_minutes × org_overhead
human_planning_min_adjusted = human_planning_min × org_overhead
human_planning_max_adjusted = human_planning_max × org_overhead
human_fix_min_adjusted = human_fix_minutes_min × org_overhead
human_fix_max_adjusted = human_fix_minutes_max × org_overhead
```

### Step 8: Subtotal (before task type)

```
subtotal_min = agent_minutes_min + integration_minutes_min + human_fix_min_adjusted + human_review_adjusted + human_planning_min_adjusted
subtotal_max = agent_minutes_max + integration_minutes_max + human_fix_max_adjusted + human_review_adjusted + human_planning_max_adjusted
```

### Step 9: Apply Task Type Multiplier

```
total_min = subtotal_min × task_type_multiplier
total_max = subtotal_max × task_type_multiplier
```

### Step 10: Apply Cone of Uncertainty Spread

```
midpoint = (total_min + total_max) / 2
half_spread = (total_max - total_min) / 2 × spread_multiplier[definition_phase]
total_min = max(0, midpoint - half_spread)
total_max = midpoint + half_spread
```

### Step 11: PERT Three-Point Estimate

Compute a weighted expected value and standard deviation for stakeholder
communication. Uses the PERT beta distribution formula.

```
total_midpoint = (total_min + total_max) / 2
pert_expected = (total_min + 4 × total_midpoint + total_max) / 6
pert_sd = (total_max - total_min) / 6

confidence_68_min = pert_expected - pert_sd
confidence_68_max = pert_expected + pert_sd
confidence_95_min = pert_expected - 2 × pert_sd
confidence_95_max = pert_expected + 2 × pert_sd
```

Note: PERT uses asymmetric distributions in practice (software tasks skew
toward overruns). The midpoint here is a simplification — for more accuracy,
use the geometric mean or weight the most-likely value closer to the minimum.

### Step 12: Apply Confidence Level Multiplier

Convert from expected estimate to committed estimate at the user's chosen
confidence level.

```
committed_min = total_min × confidence_multiplier[confidence_level]
committed_max = total_max × confidence_multiplier[confidence_level]
```

Present both the "expected" and "committed" values:
- Expected (50%): the raw PERT expected value
- Committed (80% or 90%): the risk-adjusted delivery commitment

### Step 13: Multi-Agent Adjustment

When num_agents > 1 and tasks can be parallelized:

```
coordination_overhead = 0.10 × (num_agents - 1)
parallel_speedup = min(num_agents, parallelizable_tasks)
adjusted_agent_time = agent_time / parallel_speedup × (1 + coordination_overhead)
```

### Step 14: Multi-Human Adjustment

When num_humans > 1:

```
human_parallel_factor = min(num_humans, parallelizable_tasks)
adjusted_human_time = human_time / human_parallel_factor
communication_overhead = 0.15 × (num_humans - 1)
adjusted_human_time = adjusted_human_time × (1 + communication_overhead)
```

## Anti-Pattern Guards

After computing estimates, check for these patterns and append warnings:

| Pattern | Warning |
|---------|---------|
| Complexity = XL | "Consider breaking this into smaller tasks for more accurate estimation." |
| Total > 2 weeks | "This estimate has high uncertainty (Cone of Uncertainty). Consider phased delivery with re-estimation at each phase." |
| Spread ratio (max/min) > 3 | "Wide estimate range indicates high uncertainty. Consider decomposing or running a timeboxed investigation first." |
| Definition phase = concept | "Concept-phase estimates can be off by 2-4x. Narrow the scope before committing to deadlines." |
| task_type = investigation | "Investigation tasks should be timeboxed. The output is a plan, not finished work." |

## Output Units

Present estimates in the most readable unit:
- Under 2 hours: show minutes
- 2-16 hours: show hours (e.g., "3-6 hrs")
- Over 16 hours: show days (assuming 8-hour workday, e.g., "2-4 days")
- Over 2 weeks: show weeks (e.g., "2-4 weeks")

## Story Points (Mode-Aware)

Story point guidance adapts to the detected cooperation mode.

### Human-Only Mode

Standard story points work well. Use for both sizing and velocity tracking.

```
S  = 1-2 points
M  = 3-5 points
L  = 8-13 points
XL = 20-40 points
```

Velocity in points/sprint is stable and predictable. Plan sprints by filling to velocity.

### Hybrid Mode (Dual-Track)

Use points for **relative sizing and prioritization only**. Use hours for **sprint planning and velocity**.

```
S  = 1-2 points
M  = 3-5 points
L  = 8-13 points
XL = 20-40 points
```

Track two velocities each sprint:
- **Points velocity**: points completed (useful for trend)
- **Hours velocity**: hours completed (useful for planning)

When points velocity rises but hours velocity is flat, the team has hit its
human review ceiling — agents are producing more, but humans can't review faster.

Warning: "In hybrid teams, story points measure complexity but not delivery
speed. A 5-point task may take 8 hours without an agent or 2 hours with one.
Plan sprints in hours."

### Agent-First Mode

Do not use points for velocity — it produces meaningless noise. Optionally
use points for rough relative sizing ("is this bigger than that?").

Plan sprints by human review capacity:

```
available_capacity = review_hours_per_sprint × tasks_per_review_hour
```

The bottleneck is human review throughput, not task complexity. Track agent
rounds separately to optimize agent configuration, but plan sprints by
human hours.

Warning: "In agent-first teams, velocity in story points is unreliable
because agent throughput varies wildly by task type. Plan by human review
capacity instead."

## Batch Rollup

For N tasks:

```
total_effort_min = sum(task[i].total_min for i in 1..N)
total_effort_max = sum(task[i].total_max for i in 1..N)

critical_path = longest dependency chain (sum of sequential tasks)
parallel_groups = tasks grouped by dependency wave
wallclock_min = sum(max(task.total_min for task in wave) for wave in sequential_waves)
wallclock_max = sum(max(task.total_max for task in wave) for wave in sequential_waves)
```

## Output Fields

Every estimation must produce these canonical fields:

```
{
  "title":              string,
  "complexity":         "S" | "M" | "L" | "XL",
  "task_type":          "coding" | "bug-fix" | "investigation" | "infrastructure" | "data-migration" | "testing" | "design",
  "agent_rounds":       { "min": int, "max": int },
  "agent_time_minutes": { "min": int, "max": int },
  "agent_effectiveness": float,
  "human_review_minutes": int,
  "human_planning_minutes": { "min": int, "max": int },
  "human_fix_minutes":  { "min": int, "max": int },
  "integration_minutes":{ "min": int, "max": int },
  "task_type_multiplier": float,
  "org_overhead":       float,
  "confidence_level":   int,
  "confidence_multiplier": float,
  "definition_phase":   string,
  "spread_multiplier":  float,
  "total_minutes":      { "min": int, "max": int },
  "total_hours":        { "min": float, "max": float },
  "pert_expected_minutes": float,
  "pert_sd_minutes":    float,
  "committed_hours":    { "min": float, "max": float },
  "risk_level":         "low" | "medium" | "high",
  "risk_notes":         string,
  "assumptions":        string[],
  "warnings":           string[],
  "team": {
    "humans": int,
    "agents": int
  },
  "story_points":       int | null
}
```

For batch, wrap in:

```
{
  "tasks": [ ...individual estimates... ],
  "rollup": {
    "total_effort_hours":   { "min": float, "max": float },
    "committed_effort_hours": { "min": float, "max": float },
    "wallclock_hours":      { "min": float, "max": float },
    "pert_expected_hours":  float,
    "critical_path":        string[],
    "task_count":           int,
    "size_distribution":    { "S": int, "M": int, "L": int, "XL": int },
    "warnings":             string[]
  }
}
```

## Calculator Generation

When a user requests a standalone script, generate from these formulas.
The script must:

1. Accept all inputs from the Inputs table via CLI args or stdin JSON
2. Apply all lookup tables and formulas exactly as defined above
3. Output the canonical JSON output fields
4. Have zero external dependencies
5. Be a single self-contained file
6. Include a --help flag with usage instructions

Supported target languages (generate on request):
Python, TypeScript, JavaScript, Rust, Go, Ruby, Java, C#, Swift, Kotlin
