# Output Schema & Tracker Mappings

## Output Ordering (Summary First)

Every estimate output follows this order:

1. **One-line summary** — always first, always scannable
2. **PERT expected value** — the single "most likely" number
3. **Breakdown table** — agent rounds, times, human time
4. **Confidence bands** — expected vs committed estimates
5. **Risk notes & warnings** — anti-pattern guards, uncertainty flags
6. **Tracker-formatted block** — if tracker specified
7. **Subtasks** — if applicable

## Cooperation Mode Output Adaptation

Output format adapts to the detected cooperation mode:

### Human-Only Mode
- Show story points prominently alongside hours
- One-line summary includes points: `Expected: ~4 hrs (5 pts) | ...`
- Sprint fit in points
- Velocity recommendation: "Track velocity in story points."

### Hybrid Mode
- Show both points and hours, clearly labeled
- One-line summary: `Expected: ~4 hrs | 5 pts (sizing only) | ...`
- Sprint fit in hours (the real constraint)
- Add note: "Points are for sizing and prioritization. Plan sprints in hours."
- If batch: show divergence warning if applicable

### Agent-First Mode
- Lead with hours, suppress points unless requested
- One-line summary: `Expected: ~70 min (~22 min review) | ...`
- Include review hours as a separate line in breakdown
- Sprint fit in review hours
- Velocity recommendation: "Track velocity in human review hours."

### One-Line Summary Format

Single task:
```
Expected: ~4 hrs | Committed (80%): ~5.5 hrs | 10-26 agent rounds (~180k tokens) + 3 hrs human | Risk: medium | Size: M
```

Batch:
```
36 tasks | Expected: ~65 hrs | Committed (80%): ~91 hrs | 20-40 hrs wallclock (3 agents) | 12S, 15M, 7L, 2XL
```

### PERT Block

Always show after the summary line:

```
PERT Expected: 4.2 hrs (most likely outcome)
Standard Deviation: ±0.8 hrs
68% Confidence: 3.4 - 5.0 hrs
95% Confidence: 2.6 - 5.8 hrs
Committed (80%): 5.5 hrs
```

## Output Modes

### Native Fields Mode
Uses the tracker's built-in field system. Requires custom fields to be
configured for agent-specific metrics. Richer data, more setup.

### Embedded Mode (Default)
All estimation data goes into the description/body as a structured markdown
table. Zero configuration, works immediately in any tracker.

Ask the user: "Native fields or embedded in description? (default: embedded)"

## Tracker Mappings

### Canonical → Linear

**Native:**
| Canonical Field | Linear Field | Notes |
|----------------|-------------|-------|
| title | Title | — |
| complexity | Label | `estimate:S/M/L/XL` |
| pert_expected_hours | Estimate | hours as decimal |
| risk_level | Label | `risk:low/medium/high` |
| risk_notes | Comment | first comment |
| subtasks | Sub-issues | linked |
| agent_rounds | Custom field | "Agent Rounds" |
| human_review_minutes | Custom field | "Human Review (min)" |
| committed_hours | Custom field | "Committed Estimate (hrs)" |
| confidence_level | Custom field | "Confidence %" |
| priority | Priority | 1-4 mapping |
| token_estimate | Custom field | "Est. Tokens" |

**Embedded:**
```markdown
## Estimate
| Field | Value |
|-------|-------|
| Complexity | M |
| Task Type | coding |
| Agent Rounds | 10-26 |
| Agent Time | 20-78 min |
| Human Review | 60 min |
| Human Planning | 30-60 min |
| Human Fix/QA | 8-30 min |
| Integration | 3-12 min |
| **Expected (PERT)** | **~4 hrs** |
| **Committed (80%)** | **~5.5 hrs** |
| Confidence Band (68%) | 3.4-5.0 hrs |
| Token Estimate | ~180k tokens |
| Model Tier | standard |
| Est. Cost | ~$1.20 |
| Risk | medium |
| Team | 1 human, 1 agent |
```

Token Estimate and Model Tier always appear in the breakdown table.
Est. Cost only appears if `show_cost == true`.
Cost does NOT appear in the one-line summary (too noisy).

### Canonical → JIRA

**Native:**
| Canonical Field | JIRA Field | Notes |
|----------------|-----------|-------|
| title | Summary | — |
| complexity | T-Shirt Size | custom field or label |
| committed_hours | Original Estimate | seconds (×3600) |
| risk_level | Priority | maps to JIRA priority |
| risk_notes | Description | appended |
| subtasks | Sub-tasks | linked issue type |
| agent_rounds | Custom field | number type |
| human_review_minutes | Custom field | number type |
| pert_expected_hours | Custom field | "Expected Estimate (hrs)" |
| labels | Labels | array |
| token_estimate | Custom field | "Est. Tokens" (number) |

**Embedded:** Same markdown table in Description field.

### Canonical → ClickUp

**Native:**
| Canonical Field | ClickUp Field | Notes |
|----------------|--------------|-------|
| title | Task Name | — |
| complexity | Tag | `size:M` |
| committed_hours | Time Estimate | milliseconds |
| risk_level | Tag | `risk:medium` |
| risk_notes | Description | — |
| subtasks | Subtasks | nested |
| agent_rounds | Custom field | number |
| human_review_minutes | Custom field | number |
| priority | Priority | 1-4 |
| token_estimate | Custom field | "Est. Tokens" (number) |

**Embedded:** Same markdown table in Description field.

### Canonical → GitHub Issues

**Native:**
| Canonical Field | GitHub Field | Notes |
|----------------|-------------|-------|
| title | Title | — |
| complexity | Label | `size/M` |
| committed_hours | Label | `estimate/~5.5hrs` |
| risk_level | Label | `risk/medium` |
| risk_notes | Body | — |
| subtasks | Task list | `- [ ] item` in body |
| agent_rounds | Body section | no custom fields |
| human_review_minutes | Body section | no custom fields |
| labels | Labels | — |
| token_estimate | Body section | no custom fields |

**Embedded:** Markdown table in issue Body. This is the recommended mode
for GitHub Issues since it has no custom field support.

### Canonical → Monday

**Native:**
| Canonical Field | Monday Field | Notes |
|----------------|-------------|-------|
| title | Item Name | — |
| complexity | Label column | configured values |
| committed_hours | Numbers column | "Committed Est. (hrs)" |
| pert_expected_hours | Numbers column | "Expected (hrs)" |
| risk_level | Status column | low/medium/high |
| risk_notes | Updates | posted as update |
| subtasks | Subitems | — |
| agent_rounds | Numbers column | "Agent Rounds" |
| human_review_minutes | Numbers column | "Review (min)" |
| priority | Priority column | — |
| labels | Tags column | — |
| token_estimate | Numbers column | "Est. Tokens" |

**Embedded:** Markdown in Updates or Long Text column.

### Canonical → GitLab

**Native:**
| Canonical Field | GitLab Field | Notes |
|----------------|-------------|-------|
| title | Title | — |
| complexity | Label | `size::M` scoped label |
| committed_hours | Weight | integer (round up hours) |
| committed_hours (precise) | Time estimate | `/estimate 5.5h` quick action |
| risk_level | Label | `risk::medium` scoped label |
| risk_notes | Description | — |
| subtasks | Child issues | linked via epic or parent |
| agent_rounds | Description section | no custom fields in free tier |
| human_review_minutes | Description section | — |
| labels | Labels | scoped labels supported |
| token_estimate | Description section | no custom fields in free tier |

**Embedded:** Markdown table in Description. Use `/estimate` quick action
for time tracking integration.

### Canonical → Asana

**Native:**
| Canonical Field | Asana Field | Notes |
|----------------|------------|-------|
| title | Task Name | — |
| complexity | Custom field (Dropdown) | "Size" — S/M/L/XL |
| committed_hours | Custom field (Number) | "Committed Estimate (hrs)" |
| pert_expected_hours | Custom field (Number) | "Expected (hrs)" |
| risk_level | Custom field (Dropdown) | "Risk" — low/medium/high |
| risk_notes | Description | appended |
| subtasks | Subtasks | native |
| agent_rounds | Custom field (Number) | "Agent Rounds" |
| human_review_minutes | Custom field (Number) | "Review (min)" |
| token_estimate | Custom field (Number) | "Est. Tokens" |

**Embedded:** Markdown in Description. Quirks: custom fields are
project-scoped; time tracking is paid.

### Canonical → Azure DevOps

**Native:**
| Canonical Field | ADO Field | Notes |
|----------------|----------|-------|
| title | Title | — |
| complexity | Tags | `Size:M` |
| committed_hours | Original Estimate | hours (native) |
| pert_expected_hours | Custom field (Decimal) | "Expected Estimate (hrs)" |
| risk_level | Tags | `Risk:medium` |
| risk_notes | Description | HTML — use `<table>` |
| subtasks | Child work items | parent-child link |
| agent_rounds | Custom field (Integer) | "Agent Rounds" |
| story_points | Story Points | native on User Story |
| token_estimate | Custom field (Integer) | "Est. Tokens" |

**Embedded:** HTML table in Description (ADO uses HTML, not markdown).
Quirks: custom fields via Process customization; work item types matter
(User Story vs Task).

### Canonical → Zenhub

**Native:**
| Canonical Field | Zenhub Field | Notes |
|----------------|-------------|-------|
| title | Issue Title | GitHub Issue title |
| complexity | Label | `size/M` (GitHub label) |
| committed_hours | Estimate | Zenhub story points field |
| pert_expected_hours | Body section | no custom fields |
| risk_level | Label | `risk/medium` (GitHub label) |
| risk_notes | Body | — |
| subtasks | Task list | `- [ ]` in body, or child issues |
| agent_rounds | Body section | no custom fields |
| story_points | Estimate | native Zenhub field (points) |
| token_estimate | Body section | no custom fields |

**Embedded:** Markdown in GitHub Issue body (recommended). Quirks: Zenhub
layers on top of GitHub Issues — uses GitHub labels + body for most data;
Estimate field is points-only; Epics are cross-repo issue collections.

### Canonical → Shortcut

**Native:**
| Canonical Field | Shortcut Field | Notes |
|----------------|---------------|-------|
| title | Story Name | — |
| complexity | Label | `size:M` |
| committed_hours | Custom field (Number) | "Committed (hrs)" |
| pert_expected_hours | Custom field (Number) | "Expected (hrs)" |
| risk_level | Label | `risk:medium` |
| risk_notes | Description | markdown supported |
| subtasks | Tasks (within Story) | checklist-style |
| agent_rounds | Custom field (Number) | "Agent Rounds" |
| story_points | Estimate | native field (points) |
| token_estimate | Custom field (Number) | "Est. Tokens" |

**Embedded:** Markdown in Description. Quirks: custom fields on Team plan+;
native Estimate is points not hours; Stories have Tasks (checklist items).

## Batch Output Format

### Summary Table (Always First)

```
| # | Task | Size | Type | Rounds | Agent | Human | Tokens | Expected | Committed (80%) | Risk | Deps |
|---|------|------|------|--------|-------|-------|--------|----------|-----------------|------|------|
| 1 | Auth service | M | coding | 10-26 | 20-78m | 2-3h | ~180k | ~4h | ~5.5h | med | — |
| 2 | Payment | L | coding | 26-65 | 52-195m | 4-8h | ~520k | ~8h | ~11h | high | #1 |
| 3 | DB migration | L | data-mig | 26-65 | 52-195m | 4-8h | ~520k | ~16h | ~22h | high | — |
|---|------|------|------|--------|-------|-------|--------|----------|-----------------|------|------|
| | **Totals** | | | | | | **~1.2M** | **~28h** | **~38.5h** | | |
```

### Rollup Block

```
Total effort (expected): ~28 hrs
Total effort (committed 80%): ~38.5 hrs
Wallclock (sequential): 24-48 hrs
Wallclock (2 agents parallel): 14-28 hrs
Critical path: Auth → Payment → Dashboard
Team: 1 human, 2 agents
Size distribution: 1S, 2M, 2L
```

### Warnings Block

After the rollup, append any triggered anti-pattern guards:

```
Warnings:
- Task #3 (DB migration) is type=data-migration with 2.0x lifecycle overhead. Consider phased delivery.
- Task #2 (Payment) has high risk. Verify external API availability before committing.
- 2 tasks are size L. Consider decomposing for more accurate estimates.
```

### Per-Task Detail (Expandable)

After the summary table, provide full breakdown per task only if:
- User requests it
- Task has notable risk or unusual parameters
- Task has overrides from batch defaults
- Task triggered anti-pattern warnings
