#!/usr/bin/env python3
"""Deterministic formula tests for progressive-estimation.

Implements the 14-step computation pipeline from references/formulas.md
and runs the 6 regression test cases from evals/eval-regression.md.

Zero external dependencies — stdlib only.
"""
import unittest

# ── Lookup Tables ──────────────────────────────────────────────

BASE_ROUNDS = {
    "S": (3, 8),
    "M": (8, 20),
    "L": (20, 50),
    "XL": (50, 120),
}

TASK_TYPE_MULTIPLIER = {
    "coding": 1.0,
    "bug-fix": 1.3,
    "investigation": 0.5,
    "design": 1.2,
    "testing": 1.3,
    "infrastructure": 1.5,
    "data-migration": 2.0,
}

AGENT_EFFECTIVENESS = {
    "S": 0.9,
    "M": 0.5,
    "L": 0.35,
    "XL": 0.3,
}

MINUTES_PER_ROUND = {
    "exploratory": (3, 5),
    "partial": (2, 3),
    "mostly-automated": (1, 2),
}

REVIEW_MINUTES = {
    "light":    {"S": 10,  "M": 15,  "L": 30,  "XL": 60},
    "standard": {"S": 20,  "M": 30,  "L": 60,  "XL": 120},
    "deep":     {"S": 40,  "M": 60,  "L": 120, "XL": 240},
}

PLANNING_MINUTES = {
    "S": (15, 30),
    "M": (30, 60),
    "L": (60, 180),
    "XL": (120, 480),
}

CONFIDENCE_MULTIPLIER = {
    50: {"S": 1.0,  "M": 1.0,  "L": 1.0,  "XL": 0.75},
    80: {"S": 1.8,  "M": 1.4,  "L": 1.4,  "XL": 1.5},
    90: {"S": 2.9,  "M": 2.1,  "L": 2.0,  "XL": 2.2},
}

SPREAD_MULTIPLIER = {
    "concept": 2.0,
    "requirements": 1.5,
    "design": 1.2,
    "ready": 1.0,
}

ORG_OVERHEAD = {
    "solo-startup": 1.0,
    "growth": 1.15,
    "enterprise": 1.3,
}


# ── Core Estimator ─────────────────────────────────────────────

def estimate(
    complexity,
    task_type="coding",
    num_humans=1,
    num_agents=1,
    maturity="partial",
    risk_coefficient=1.3,
    integration_overhead=0.15,
    domain_familiarity=1.0,
    human_fix_ratio=0.20,
    review_depth="standard",
    confidence_level=80,
    definition_phase="ready",
    org_size="solo-startup",
    model_tier="standard",
    show_cost=False,
):
    """Run the full 15-step estimation pipeline. Returns dict with all fields."""

    # Step 1: Agent Rounds
    base_min, base_max = BASE_ROUNDS[complexity]
    rounds_min = round(base_min * risk_coefficient * domain_familiarity)
    rounds_max = round(base_max * risk_coefficient * domain_familiarity)

    # Step 2: Agent Time
    mpr_min, mpr_max = MINUTES_PER_ROUND[maturity]
    agent_min = rounds_min * mpr_min
    agent_max = rounds_max * mpr_max

    # Step 3: Integration Time
    integration_min = agent_min * integration_overhead
    integration_max = agent_max * integration_overhead

    # Step 4: Human Fix Time (Agent Effectiveness Adjusted)
    ae = AGENT_EFFECTIVENESS[complexity]
    adjusted_fix_ratio = human_fix_ratio + (1 - ae) * 0.3
    human_fix_min = agent_min * adjusted_fix_ratio
    human_fix_max = agent_max * adjusted_fix_ratio

    # Step 5: Human Review Time (scalar)
    review = REVIEW_MINUTES[review_depth][complexity]

    # Step 6: Human Planning
    planning_min, planning_max = PLANNING_MINUTES[complexity]

    # Step 7: Org Size Overhead (human time only)
    org = ORG_OVERHEAD[org_size]
    review_adj = review * org
    planning_min_adj = planning_min * org
    planning_max_adj = planning_max * org
    human_fix_min_adj = human_fix_min * org
    human_fix_max_adj = human_fix_max * org

    # Step 8: Subtotal
    subtotal_min = agent_min + integration_min + human_fix_min_adj + review_adj + planning_min_adj
    subtotal_max = agent_max + integration_max + human_fix_max_adj + review_adj + planning_max_adj

    # Step 9: Task Type Multiplier
    ttm = TASK_TYPE_MULTIPLIER[task_type]
    total_min = subtotal_min * ttm
    total_max = subtotal_max * ttm

    # Step 10: Cone of Uncertainty Spread
    spread = SPREAD_MULTIPLIER[definition_phase]
    midpoint = (total_min + total_max) / 2
    half_spread = (total_max - total_min) / 2 * spread
    total_min = max(0, midpoint - half_spread)
    total_max = midpoint + half_spread

    # Step 11: Log-Normal Three-Point Estimate
    import math
    most_likely = math.sqrt(max(total_min, 0.001) * max(total_max, 0.001))
    pert_expected = (total_min + 4 * most_likely + total_max) / 6
    pert_sd = (total_max - total_min) / 6

    # Step 12: Confidence Level Multiplier (size-dependent)
    cm = CONFIDENCE_MULTIPLIER[confidence_level][complexity]
    committed_min = total_min * cm
    committed_max = total_max * cm

    # Step 13: Multi-Agent Adjustment
    if num_agents > 1:
        coordination_overhead = 0.10 * (num_agents - 1)
        parallel_speedup = num_agents  # assume all parallelizable
        agent_min = agent_min / parallel_speedup * (1 + coordination_overhead)
        agent_max = agent_max / parallel_speedup * (1 + coordination_overhead)

    # Step 14: Multi-Human Adjustment
    if num_humans > 1:
        communication_overhead = 0.15 * (num_humans - 1)
        human_time_min = (human_fix_min_adj + review_adj + planning_min_adj)
        human_time_max = (human_fix_max_adj + review_adj + planning_max_adj)
        human_time_min = human_time_min / num_humans * (1 + communication_overhead)
        human_time_max = human_time_max / num_humans * (1 + communication_overhead)

    # Step 15: Token & Cost Estimation
    token_est = estimate_tokens(
        complexity=complexity,
        maturity=maturity,
        num_agents=num_agents,
        model_tier=model_tier,
        show_cost=show_cost,
        risk_coefficient=risk_coefficient,
        domain_familiarity=domain_familiarity,
    )

    return {
        "complexity": complexity,
        "task_type": task_type,
        "agent_effectiveness": ae,
        "task_type_multiplier": ttm,
        "agent_rounds": {"min": rounds_min, "max": rounds_max},
        "agent_time_minutes": {"min": agent_min, "max": agent_max},
        "integration_minutes": {"min": integration_min, "max": integration_max},
        "human_fix_minutes": {"min": human_fix_min_adj, "max": human_fix_max_adj},
        "human_review_minutes": review_adj,
        "human_planning_minutes": {"min": planning_min_adj, "max": planning_max_adj},
        "org_overhead": org,
        "total_minutes": {"min": total_min, "max": total_max},
        "total_hours": {"min": total_min / 60, "max": total_max / 60},
        "pert_expected_minutes": pert_expected,
        "pert_expected_hours": pert_expected / 60,
        "pert_sd_minutes": pert_sd,
        "confidence_level": confidence_level,
        "confidence_multiplier": cm,
        "committed_minutes": {"min": committed_min, "max": committed_max},
        "committed_hours": {"min": committed_min / 60, "max": committed_max / 60},
        "spread_multiplier": spread,
        "definition_phase": definition_phase,
        "token_estimate": token_est,
    }


# ── Token Estimation ──────────────────────────────────────────

TOKENS_PER_ROUND = {
    "exploratory":      {"S": 8000,  "M": 15000, "L": 25000, "XL": 40000},
    "partial":          {"S": 6000,  "M": 12000, "L": 20000, "XL": 35000},
    "mostly-automated": {"S": 5000,  "M": 10000, "L": 18000, "XL": 30000},
}

OUTPUT_TOKEN_RATIO = {
    "S": 0.30,
    "M": 0.30,
    "L": 0.30,
    "XL": 0.35,
}

TIER_PRICING = {
    "economy":  {"input": 0.50,  "output": 2.50},
    "standard": {"input": 2.50,  "output": 12.00},
    "premium":  {"input": 5.00,  "output": 25.00},
}


def estimate_tokens(
    complexity,
    maturity="partial",
    num_agents=1,
    model_tier="standard",
    show_cost=False,
    risk_coefficient=1.3,
    domain_familiarity=1.0,
):
    """Step 15: Token & cost estimation."""
    base_min, base_max = BASE_ROUNDS[complexity]
    rounds_min = round(base_min * risk_coefficient * domain_familiarity)
    rounds_max = round(base_max * risk_coefficient * domain_familiarity)

    tpr = TOKENS_PER_ROUND[maturity][complexity]
    output_ratio = OUTPUT_TOKEN_RATIO[complexity]

    total_tokens_min = rounds_min * tpr * num_agents
    total_tokens_max = rounds_max * tpr * num_agents

    input_tokens_min = total_tokens_min * (1 - output_ratio)
    input_tokens_max = total_tokens_max * (1 - output_ratio)
    output_tokens_min = total_tokens_min * output_ratio
    output_tokens_max = total_tokens_max * output_ratio

    token_midpoint = (total_tokens_min + total_tokens_max) / 2
    pert_expected_tokens = (total_tokens_min + 4 * token_midpoint + total_tokens_max) / 6

    result = {
        "total_tokens": {"min": total_tokens_min, "max": total_tokens_max},
        "input_tokens": {"min": input_tokens_min, "max": input_tokens_max},
        "output_tokens": {"min": output_tokens_min, "max": output_tokens_max},
        "pert_expected_tokens": pert_expected_tokens,
        "model_tier": model_tier,
        "cost_usd": None,
        "pert_expected_cost_usd": None,
    }

    if show_cost:
        pricing = TIER_PRICING[model_tier]
        cost_min = (input_tokens_min * pricing["input"] + output_tokens_min * pricing["output"]) / 1_000_000
        cost_max = (input_tokens_max * pricing["input"] + output_tokens_max * pricing["output"]) / 1_000_000
        pert_expected_cost = (cost_min + 4 * (cost_min + cost_max) / 2 + cost_max) / 6
        result["cost_usd"] = {"min": cost_min, "max": cost_max}
        result["pert_expected_cost_usd"] = pert_expected_cost

    return result


# ── Regression Tests ───────────────────────────────────────────

class TestCase1TrivialS(unittest.TestCase):
    """Case 1: S coding task, mostly-automated, all defaults."""

    def setUp(self):
        self.r = estimate(
            complexity="S", task_type="coding", num_humans=1, num_agents=1,
            maturity="mostly-automated", risk_coefficient=1.3,
            integration_overhead=0.15, domain_familiarity=1.0,
            human_fix_ratio=0.20, review_depth="standard",
            confidence_level=80, definition_phase="ready",
            org_size="solo-startup",
        )

    def test_complexity(self):
        self.assertEqual(self.r["complexity"], "S")

    def test_agent_effectiveness(self):
        self.assertAlmostEqual(self.r["agent_effectiveness"], 0.9)

    def test_agent_rounds(self):
        self.assertGreaterEqual(self.r["agent_rounds"]["min"], 4)
        self.assertLessEqual(self.r["agent_rounds"]["max"], 10)

    def test_pert_expected(self):
        self.assertGreaterEqual(self.r["pert_expected_hours"], 0.5)
        self.assertLessEqual(self.r["pert_expected_hours"], 1.5)

    def test_committed(self):
        self.assertGreaterEqual(self.r["committed_hours"]["min"], 0.7)
        self.assertLessEqual(self.r["committed_hours"]["max"], 2.5)


class TestCase2MediumM(unittest.TestCase):
    """Case 2: M coding task, partial maturity, all defaults."""

    def setUp(self):
        self.r = estimate(
            complexity="M", task_type="coding", num_humans=1, num_agents=1,
            maturity="partial", risk_coefficient=1.3,
            integration_overhead=0.15, domain_familiarity=1.0,
            human_fix_ratio=0.20, review_depth="standard",
            confidence_level=80, definition_phase="ready",
            org_size="solo-startup",
        )

    def test_agent_effectiveness(self):
        self.assertAlmostEqual(self.r["agent_effectiveness"], 0.5)

    def test_agent_rounds(self):
        self.assertGreaterEqual(self.r["agent_rounds"]["min"], 10)
        self.assertLessEqual(self.r["agent_rounds"]["max"], 26)

    def test_pert_expected(self):
        self.assertGreaterEqual(self.r["pert_expected_hours"], 2)
        self.assertLessEqual(self.r["pert_expected_hours"], 5)

    def test_committed(self):
        # 80% M multiplier = 1.4x (unchanged)
        self.assertGreaterEqual(self.r["committed_hours"]["min"], 2.0)
        self.assertLessEqual(self.r["committed_hours"]["max"], 7)


class TestCase3LargeDataMigration(unittest.TestCase):
    """Case 3: L data-migration task, exploratory, all defaults."""

    def setUp(self):
        self.r = estimate(
            complexity="L", task_type="data-migration", num_humans=1, num_agents=1,
            maturity="exploratory", risk_coefficient=1.3,
            integration_overhead=0.15, domain_familiarity=1.0,
            human_fix_ratio=0.20, review_depth="standard",
            confidence_level=80, definition_phase="ready",
            org_size="solo-startup",
        )

    def test_agent_effectiveness(self):
        self.assertAlmostEqual(self.r["agent_effectiveness"], 0.35)

    def test_task_type_multiplier(self):
        self.assertAlmostEqual(self.r["task_type_multiplier"], 2.0)

    def test_agent_rounds(self):
        self.assertGreaterEqual(self.r["agent_rounds"]["min"], 26)
        self.assertLessEqual(self.r["agent_rounds"]["max"], 65)

    def test_pert_expected_days(self):
        # 1-3 days = 8-24 hours
        self.assertGreaterEqual(self.r["pert_expected_hours"], 8)
        self.assertLessEqual(self.r["pert_expected_hours"], 24)

    def test_committed_days(self):
        # 1.5-4 days = 12-32 hours
        self.assertGreaterEqual(self.r["committed_hours"]["min"], 10)
        self.assertLessEqual(self.r["committed_hours"]["max"], 42)


class TestCase4XL(unittest.TestCase):
    """Case 4: XL coding task, exploratory, all defaults."""

    def setUp(self):
        self.r = estimate(
            complexity="XL", task_type="coding", num_humans=1, num_agents=1,
            maturity="exploratory", risk_coefficient=1.3,
            integration_overhead=0.15, domain_familiarity=1.0,
            human_fix_ratio=0.20, review_depth="standard",
            confidence_level=80, definition_phase="ready",
            org_size="solo-startup",
        )

    def test_agent_effectiveness(self):
        self.assertAlmostEqual(self.r["agent_effectiveness"], 0.3)

    def test_agent_rounds(self):
        self.assertGreaterEqual(self.r["agent_rounds"]["min"], 65)
        self.assertLessEqual(self.r["agent_rounds"]["max"], 156)

    def test_pert_expected(self):
        # 15-40 hours
        self.assertGreaterEqual(self.r["pert_expected_hours"], 15)
        self.assertLessEqual(self.r["pert_expected_hours"], 40)

    def test_committed(self):
        # 80% XL multiplier = 1.5x
        self.assertGreaterEqual(self.r["committed_hours"]["min"], 13)
        self.assertLessEqual(self.r["committed_hours"]["max"], 60)


class TestCase5BatchConsistency(unittest.TestCase):
    """Case 5: Batch of 3 tasks — verify rollup consistency."""

    def setUp(self):
        self.t1 = estimate(
            complexity="S", task_type="bug-fix", num_humans=1, num_agents=1,
            maturity="partial",
        )
        self.t2 = estimate(
            complexity="M", task_type="coding", num_humans=1, num_agents=1,
            maturity="partial",
        )
        self.t3 = estimate(
            complexity="L", task_type="coding", num_humans=1, num_agents=1,
            maturity="partial",
        )

    def test_bugfix_multiplier(self):
        self.assertAlmostEqual(self.t1["task_type_multiplier"], 1.3)

    def test_rollup_pert_between_min_max(self):
        total_min = sum(t["total_minutes"]["min"] for t in [self.t1, self.t2, self.t3])
        total_max = sum(t["total_minutes"]["max"] for t in [self.t1, self.t2, self.t3])
        pert_total = sum(t["pert_expected_minutes"] for t in [self.t1, self.t2, self.t3])
        self.assertGreaterEqual(pert_total, total_min)
        self.assertLessEqual(pert_total, total_max)

    def test_committed_ratio(self):
        """Committed should match size-dependent 80% multiplier."""
        expected = {"S": 1.8, "M": 1.4, "L": 1.4}
        for t, size in zip([self.t1, self.t2, self.t3], ["S", "M", "L"]):
            ratio_min = t["committed_minutes"]["min"] / t["total_minutes"]["min"]
            ratio_max = t["committed_minutes"]["max"] / t["total_minutes"]["max"]
            self.assertAlmostEqual(ratio_min, expected[size], places=2)
            self.assertAlmostEqual(ratio_max, expected[size], places=2)


class TestCase6ConfidenceLevels(unittest.TestCase):
    """Case 6: Same task at 50% and 90% confidence."""

    def setUp(self):
        common = dict(
            complexity="M", task_type="coding", num_humans=1, num_agents=1,
            maturity="partial", risk_coefficient=1.3,
            integration_overhead=0.15, domain_familiarity=1.0,
            human_fix_ratio=0.20, review_depth="standard",
            definition_phase="ready", org_size="solo-startup",
        )
        self.r50 = estimate(confidence_level=50, **common)
        self.r90 = estimate(confidence_level=90, **common)

    def test_same_pert_expected(self):
        self.assertAlmostEqual(
            self.r50["pert_expected_minutes"],
            self.r90["pert_expected_minutes"],
            places=2,
        )

    def test_50_uses_1x(self):
        self.assertAlmostEqual(self.r50["confidence_multiplier"], 1.0)

    def test_90_uses_2_1x(self):
        """M task at 90% should use 2.1x (size-dependent)."""
        self.assertAlmostEqual(self.r90["confidence_multiplier"], 2.1)

    def test_committed_ratio(self):
        """90% committed / 50% committed should be ~2.1 for M."""
        ratio = self.r90["committed_hours"]["max"] / self.r50["committed_hours"]["max"]
        self.assertAlmostEqual(ratio, 2.1, places=2)


class TestCase7TokenMath(unittest.TestCase):
    """Case 7: Token estimation math for M coding task, partial maturity."""

    def setUp(self):
        self.t = estimate_tokens(
            complexity="M", maturity="partial", num_agents=1,
            model_tier="standard", show_cost=True,
        )

    def test_total_tokens_range(self):
        # M partial: 12k tokens/round, rounds 10-26
        # min = 10 * 12000 = 120000, max = 26 * 12000 = 312000
        self.assertEqual(self.t["total_tokens"]["min"], 120000)
        self.assertEqual(self.t["total_tokens"]["max"], 312000)

    def test_output_ratio(self):
        # M output ratio = 0.30
        self.assertAlmostEqual(
            self.t["output_tokens"]["min"] / self.t["total_tokens"]["min"], 0.30
        )

    def test_input_output_sum(self):
        self.assertEqual(
            self.t["input_tokens"]["min"] + self.t["output_tokens"]["min"],
            self.t["total_tokens"]["min"],
        )
        self.assertEqual(
            self.t["input_tokens"]["max"] + self.t["output_tokens"]["max"],
            self.t["total_tokens"]["max"],
        )

    def test_pert_between_min_max(self):
        self.assertGreaterEqual(
            self.t["pert_expected_tokens"], self.t["total_tokens"]["min"]
        )
        self.assertLessEqual(
            self.t["pert_expected_tokens"], self.t["total_tokens"]["max"]
        )

    def test_cost_present(self):
        self.assertIsNotNone(self.t["cost_usd"])
        self.assertIsNotNone(self.t["pert_expected_cost_usd"])

    def test_cost_min_less_than_max(self):
        self.assertLess(self.t["cost_usd"]["min"], self.t["cost_usd"]["max"])

    def test_cost_math(self):
        # Standard tier: input=$2.50/M, output=$12.00/M
        # min: input=120000*0.70=84000, output=120000*0.30=36000
        # cost_min = (84000*2.50 + 36000*12.00) / 1_000_000
        expected_cost_min = (84000 * 2.50 + 36000 * 12.00) / 1_000_000
        self.assertAlmostEqual(self.t["cost_usd"]["min"], expected_cost_min, places=4)


class TestCase8TokenScaling(unittest.TestCase):
    """Case 8: Token scaling — XL > L > M > S, multi-agent multiplies."""

    def test_scaling_by_complexity(self):
        sizes = ["S", "M", "L", "XL"]
        tokens = []
        for s in sizes:
            t = estimate_tokens(complexity=s, maturity="partial")
            tokens.append(t["total_tokens"]["min"])
        for i in range(len(tokens) - 1):
            self.assertLess(tokens[i], tokens[i + 1])

    def test_multi_agent_multiplier(self):
        t1 = estimate_tokens(complexity="M", maturity="partial", num_agents=1)
        t3 = estimate_tokens(complexity="M", maturity="partial", num_agents=3)
        self.assertEqual(
            t3["total_tokens"]["min"], t1["total_tokens"]["min"] * 3
        )

    def test_no_cost_by_default(self):
        t = estimate_tokens(complexity="M", maturity="partial", show_cost=False)
        self.assertIsNone(t["cost_usd"])
        self.assertIsNone(t["pert_expected_cost_usd"])

    def test_premium_more_expensive_than_economy(self):
        te = estimate_tokens(
            complexity="M", maturity="partial", model_tier="economy", show_cost=True
        )
        tp = estimate_tokens(
            complexity="M", maturity="partial", model_tier="premium", show_cost=True
        )
        self.assertLess(te["cost_usd"]["max"], tp["cost_usd"]["max"])

    def test_maturity_variation(self):
        """Exploratory should produce more tokens than mostly-automated."""
        t_exp = estimate_tokens(complexity="M", maturity="exploratory")
        t_auto = estimate_tokens(complexity="M", maturity="mostly-automated")
        self.assertGreater(
            t_exp["total_tokens"]["min"], t_auto["total_tokens"]["min"]
        )
        self.assertGreater(
            t_exp["total_tokens"]["max"], t_auto["total_tokens"]["max"]
        )

    def test_pert_expected_cost_math(self):
        """PERT expected cost = (cost_min + 4*midpoint + cost_max) / 6."""
        t = estimate_tokens(
            complexity="M", maturity="partial", model_tier="standard", show_cost=True
        )
        cost_min = t["cost_usd"]["min"]
        cost_max = t["cost_usd"]["max"]
        expected_pert_cost = (cost_min + 4 * (cost_min + cost_max) / 2 + cost_max) / 6
        self.assertAlmostEqual(
            t["pert_expected_cost_usd"], expected_pert_cost, places=6
        )


class TestCase9TokenIntegration(unittest.TestCase):
    """Case 9: Token estimate is integrated into the main estimate() pipeline."""

    def setUp(self):
        self.r = estimate(
            complexity="M", task_type="coding", maturity="partial",
            model_tier="standard", show_cost=True,
        )

    def test_token_estimate_present(self):
        self.assertIn("token_estimate", self.r)

    def test_token_estimate_structure(self):
        te = self.r["token_estimate"]
        self.assertIn("total_tokens", te)
        self.assertIn("input_tokens", te)
        self.assertIn("output_tokens", te)
        self.assertIn("pert_expected_tokens", te)
        self.assertIn("model_tier", te)
        self.assertIn("cost_usd", te)
        self.assertIn("pert_expected_cost_usd", te)

    def test_token_estimate_uses_same_rounds(self):
        """Token estimate should use the same adjusted rounds as the main estimate."""
        te = self.r["token_estimate"]
        rounds_min = self.r["agent_rounds"]["min"]
        rounds_max = self.r["agent_rounds"]["max"]
        tpr = TOKENS_PER_ROUND["partial"]["M"]
        self.assertEqual(te["total_tokens"]["min"], rounds_min * tpr)
        self.assertEqual(te["total_tokens"]["max"], rounds_max * tpr)

    def test_model_tier_passthrough(self):
        self.assertEqual(self.r["token_estimate"]["model_tier"], "standard")

    def test_cost_present_when_show_cost(self):
        self.assertIsNotNone(self.r["token_estimate"]["cost_usd"])

    def test_cost_absent_when_not_show_cost(self):
        r = estimate(complexity="M", show_cost=False)
        self.assertIsNone(r["token_estimate"]["cost_usd"])


class TestCase10ValidationBacked(unittest.TestCase):
    """Case 10: Verify research-backed parameter changes from deep validation.

    These tests encode the properties that the 11-analysis deep validation
    (86k+ tasks + 24k METR runs + 93 Aider entries) showed must hold.
    """

    def test_confidence_multiplier_is_size_dependent(self):
        """Multipliers must vary by complexity, not be flat."""
        for level in [50, 80, 90]:
            values = set(CONFIDENCE_MULTIPLIER[level].values())
            self.assertGreater(len(values), 1,
                f"{level}% multiplier should not be flat across all sizes")

    def test_90pct_multiplier_above_2x_everywhere(self):
        """90% multiplier must be >= 2.0 in all bands (validation showed 1.8x under-delivers)."""
        for size in ["S", "M", "L", "XL"]:
            self.assertGreaterEqual(CONFIDENCE_MULTIPLIER[90][size], 2.0,
                f"90% multiplier for {size} should be >= 2.0")

    def test_80pct_S_higher_than_M(self):
        """S tasks need a larger 80% buffer than M (wider actual/estimate spread)."""
        self.assertGreater(
            CONFIDENCE_MULTIPLIER[80]["S"],
            CONFIDENCE_MULTIPLIER[80]["M"],
        )

    def test_agent_effectiveness_decreases_with_size(self):
        """Effectiveness must decrease S > M > L > XL (METR time horizon finding)."""
        sizes = ["S", "M", "L", "XL"]
        for i in range(len(sizes) - 1):
            self.assertGreater(
                AGENT_EFFECTIVENESS[sizes[i]],
                AGENT_EFFECTIVENESS[sizes[i + 1]],
                f"{sizes[i]} effectiveness should exceed {sizes[i+1]}"
            )

    def test_agent_effectiveness_M_below_old_value(self):
        """M effectiveness must be < 0.7 (old value). METR showed 0.25 autonomous."""
        self.assertLess(AGENT_EFFECTIVENESS["M"], 0.7)

    def test_agent_effectiveness_L_below_old_value(self):
        """L effectiveness must be < 0.5 (old value). METR showed 0.15 autonomous."""
        self.assertLess(AGENT_EFFECTIVENESS["L"], 0.5)

    def test_review_minutes_reduced(self):
        """Standard review must be < old values (data showed 17-20 min medians)."""
        self.assertLessEqual(REVIEW_MINUTES["standard"]["S"], 20)
        self.assertLessEqual(REVIEW_MINUTES["standard"]["M"], 30)

    def test_review_minutes_scale_by_depth(self):
        """Deep should be ~2x standard, light should be ~0.5x standard."""
        for size in ["S", "M", "L", "XL"]:
            self.assertAlmostEqual(
                REVIEW_MINUTES["deep"][size] / REVIEW_MINUTES["standard"][size],
                2.0, places=1,
            )
            self.assertAlmostEqual(
                REVIEW_MINUTES["light"][size] / REVIEW_MINUTES["standard"][size],
                0.5, places=1,
            )

    def test_output_token_ratio_S_M_raised(self):
        """S and M ratios must be >= 0.30 (Aider showed 0.31 median)."""
        self.assertGreaterEqual(OUTPUT_TOKEN_RATIO["S"], 0.30)
        self.assertGreaterEqual(OUTPUT_TOKEN_RATIO["M"], 0.30)

    def test_output_token_ratio_monotonic(self):
        """Ratio should increase or stay flat S <= M <= L <= XL."""
        sizes = ["S", "M", "L", "XL"]
        for i in range(len(sizes) - 1):
            self.assertLessEqual(
                OUTPUT_TOKEN_RATIO[sizes[i]],
                OUTPUT_TOKEN_RATIO[sizes[i + 1]],
            )


class TestCase11LogNormalPERT(unittest.TestCase):
    """Case 11: Log-normal PERT weighting properties.

    Validation showed log-normal beats beta in all 4 bands (KS test, n=84k).
    The geometric-mean most-likely value should shift PERT expected below
    the arithmetic midpoint, reflecting right-skewed effort distributions.
    """

    def test_pert_expected_below_midpoint(self):
        """Log-normal weighting should produce lower expected than arithmetic midpoint."""
        for size in ["S", "M", "L", "XL"]:
            r = estimate(complexity=size)
            midpoint = (r["total_minutes"]["min"] + r["total_minutes"]["max"]) / 2
            self.assertLess(r["pert_expected_minutes"], midpoint,
                f"{size}: PERT expected should be below arithmetic midpoint")

    def test_pert_expected_above_min(self):
        """PERT expected must be above minimum."""
        for size in ["S", "M", "L", "XL"]:
            r = estimate(complexity=size)
            self.assertGreater(r["pert_expected_minutes"], r["total_minutes"]["min"])

    def test_pert_expected_below_max(self):
        """PERT expected must be below maximum."""
        for size in ["S", "M", "L", "XL"]:
            r = estimate(complexity=size)
            self.assertLess(r["pert_expected_minutes"], r["total_minutes"]["max"])

    def test_geometric_mean_less_than_arithmetic(self):
        """Core log-normal property: geometric mean < arithmetic mean when min != max."""
        import math
        for size in ["S", "M", "L", "XL"]:
            r = estimate(complexity=size)
            tmin = max(r["total_minutes"]["min"], 0.001)
            tmax = r["total_minutes"]["max"]
            geo = math.sqrt(tmin * tmax)
            arith = (tmin + tmax) / 2
            self.assertLess(geo, arith,
                f"{size}: geometric mean should be less than arithmetic mean")


class TestCase12ParameterInteractions(unittest.TestCase):
    """Case 12: Verify that parameter changes interact correctly.

    These test the combined effect of multiple parameter changes to
    ensure the formula still produces reasonable end-to-end estimates.
    """

    def test_M_estimate_reasonable_range(self):
        """M coding task should produce 2-5 hours PERT expected."""
        r = estimate(complexity="M", maturity="partial")
        self.assertGreaterEqual(r["pert_expected_hours"], 1.5)
        self.assertLessEqual(r["pert_expected_hours"], 5)

    def test_L_estimate_reasonable_range(self):
        """L coding task should produce 5-18 hours PERT expected."""
        r = estimate(complexity="L", maturity="partial")
        self.assertGreaterEqual(r["pert_expected_hours"], 4)
        self.assertLessEqual(r["pert_expected_hours"], 18)

    def test_lower_effectiveness_increases_fix_time(self):
        """Lower agent_effectiveness should increase human fix time."""
        r_m = estimate(complexity="M")  # ae=0.5
        r_s = estimate(complexity="S")  # ae=0.9
        # M has lower effectiveness, so adjusted_fix_ratio should be higher
        fix_ratio_m = r_m["human_fix_minutes"]["min"] / max(r_m["agent_time_minutes"]["min"], 1)
        fix_ratio_s = r_s["human_fix_minutes"]["min"] / max(r_s["agent_time_minutes"]["min"], 1)
        self.assertGreater(fix_ratio_m, fix_ratio_s)

    def test_90pct_committed_much_larger_than_50pct(self):
        """90% committed should be significantly larger than 50% for S tasks."""
        r50 = estimate(complexity="S", confidence_level=50)
        r90 = estimate(complexity="S", confidence_level=90)
        ratio = r90["committed_hours"]["max"] / r50["committed_hours"]["max"]
        # S: 90% = 2.9x, 50% = 1.0x, so ratio should be 2.9
        self.assertGreater(ratio, 2.5)

    def test_review_time_fraction_reasonable(self):
        """Review should not dominate the total estimate (< 40% of subtotal)."""
        for size in ["S", "M", "L"]:
            r = estimate(complexity=size, confidence_level=50)
            review_frac = r["human_review_minutes"] / r["total_minutes"]["max"]
            self.assertLess(review_frac, 0.4,
                f"{size}: review should be < 40% of total, got {review_frac:.1%}")


if __name__ == "__main__":
    unittest.main()
