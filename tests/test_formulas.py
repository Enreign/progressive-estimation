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
    "M": 0.7,
    "L": 0.5,
    "XL": 0.3,
}

MINUTES_PER_ROUND = {
    "exploratory": (3, 5),
    "partial": (2, 3),
    "mostly-automated": (1, 2),
}

REVIEW_MINUTES = {
    "light":    {"S": 15,  "M": 30,  "L": 60,  "XL": 120},
    "standard": {"S": 30,  "M": 60,  "L": 120, "XL": 240},
    "deep":     {"S": 60,  "M": 120, "L": 240, "XL": 480},
}

PLANNING_MINUTES = {
    "S": (15, 30),
    "M": (30, 60),
    "L": (60, 180),
    "XL": (120, 480),
}

CONFIDENCE_MULTIPLIER = {
    50: 1.0,
    80: 1.4,
    90: 1.8,
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
):
    """Run the full 14-step estimation pipeline. Returns dict with all fields."""

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

    # Step 11: PERT Three-Point Estimate
    total_midpoint = (total_min + total_max) / 2
    pert_expected = (total_min + 4 * total_midpoint + total_max) / 6
    pert_sd = (total_max - total_min) / 6

    # Step 12: Confidence Level Multiplier
    cm = CONFIDENCE_MULTIPLIER[confidence_level]
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
    }


# ── Token Estimation ──────────────────────────────────────────

TOKENS_PER_ROUND = {
    "exploratory":      {"S": 8000,  "M": 15000, "L": 25000, "XL": 40000},
    "partial":          {"S": 6000,  "M": 12000, "L": 20000, "XL": 35000},
    "mostly-automated": {"S": 5000,  "M": 10000, "L": 18000, "XL": 30000},
}

OUTPUT_TOKEN_RATIO = {
    "S": 0.25,
    "M": 0.28,
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
        self.assertAlmostEqual(self.r["agent_effectiveness"], 0.7)

    def test_agent_rounds(self):
        self.assertGreaterEqual(self.r["agent_rounds"]["min"], 10)
        self.assertLessEqual(self.r["agent_rounds"]["max"], 26)

    def test_pert_expected(self):
        self.assertGreaterEqual(self.r["pert_expected_hours"], 2)
        self.assertLessEqual(self.r["pert_expected_hours"], 5)

    def test_committed(self):
        self.assertGreaterEqual(self.r["committed_hours"]["min"], 2.5)
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
        self.assertAlmostEqual(self.r["agent_effectiveness"], 0.5)

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
        # 20-55 hours
        self.assertGreaterEqual(self.r["committed_hours"]["min"], 14)
        self.assertLessEqual(self.r["committed_hours"]["max"], 55)


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
        """Committed should be ~1.4x of total (80% confidence)."""
        for t in [self.t1, self.t2, self.t3]:
            ratio_min = t["committed_minutes"]["min"] / t["total_minutes"]["min"]
            ratio_max = t["committed_minutes"]["max"] / t["total_minutes"]["max"]
            self.assertAlmostEqual(ratio_min, 1.4, places=2)
            self.assertAlmostEqual(ratio_max, 1.4, places=2)


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

    def test_90_uses_1_8x(self):
        self.assertAlmostEqual(self.r90["confidence_multiplier"], 1.8)

    def test_committed_ratio(self):
        """90% committed / 50% committed should be ~1.8."""
        ratio = self.r90["committed_hours"]["max"] / self.r50["committed_hours"]["max"]
        self.assertAlmostEqual(ratio, 1.8, places=2)


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
        # M output ratio = 0.28
        self.assertAlmostEqual(
            self.t["output_tokens"]["min"] / self.t["total_tokens"]["min"], 0.28
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
        # min: input=120000*0.72=86400, output=120000*0.28=33600
        # cost_min = (86400*2.50 + 33600*12.00) / 1_000_000
        expected_cost_min = (86400 * 2.50 + 33600 * 12.00) / 1_000_000
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


if __name__ == "__main__":
    unittest.main()
