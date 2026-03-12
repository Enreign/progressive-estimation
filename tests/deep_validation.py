#!/usr/bin/env python3
"""Deep statistical validation of progressive-estimation formula parameters.

Runs 11 analyses against 86k+ data points plus AI coding benchmarks to produce
a Parameter Audit Card.  Each weak parameter gets a current vs. recommended
value with 95% confidence intervals and a keep/adjust/flag verdict.

Analyses 1-7: Traditional estimation datasets (CESAW, SiP, Renzo, Project-22)
Analyses 8-11: AI coding benchmarks (METR, OpenHands, Aider, Tokenomics)

Usage:
    python3 tests/deep_validation.py
    python3 tests/deep_validation.py --analysis distribution
    python3 tests/deep_validation.py --analysis sensitivity
    python3 tests/deep_validation.py --list
    bash datasets/download_benchmarks.sh

Dependencies:
    Required: none (stdlib only)
    Optional: numpy, scipy (for distribution fitting / KS tests)
    Optional: PyYAML (Aider leaderboard)
"""
import argparse
import csv
import dataclasses
import json
import math
import os
import random
import sys
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_formulas import (
    BASE_ROUNDS,
    CONFIDENCE_MULTIPLIER,
    MINUTES_PER_ROUND,
    PLANNING_MINUTES,
    REVIEW_MINUTES,
    TASK_TYPE_MULTIPLIER,
    estimate,
)

try:
    import numpy as np
    import scipy.stats as stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
BENCHMARKS_DIR = os.path.join(DATASETS_DIR, "benchmarks")
SEED = 42
BOOTSTRAP_N = 1000

# ── Data Structures ──────────────────────────────────────────


@dataclasses.dataclass
class ParameterAudit:
    name: str
    current_value: Any
    recommended_value: Any
    ci_lower: float
    ci_upper: float
    sample_size: int
    test_statistic: str
    evidence_tier: int  # 1=zero, 2=weak, 3=partial
    recommendation: str  # "keep" | "adjust" | "flag"
    rationale: str


# ── Helpers ──────────────────────────────────────────────────


def pct(sorted_list, p):
    """Percentile from a pre-sorted list."""
    if not sorted_list:
        return 0
    idx = min(int(len(sorted_list) * p / 100), len(sorted_list) - 1)
    return sorted_list[idx]


def mean(lst):
    return sum(lst) / len(lst) if lst else 0


def median(lst):
    return pct(sorted(lst), 50)


def stdev(lst):
    if len(lst) < 2:
        return 0
    m = mean(lst)
    return math.sqrt(sum((x - m) ** 2 for x in lst) / (len(lst) - 1))


def bootstrap_ci(data, statistic_fn, n=BOOTSTRAP_N, seed=SEED, alpha=0.05):
    """Bootstrap confidence interval using stdlib random.choices().

    Returns (point_estimate, ci_lower, ci_upper).
    """
    rng = random.Random(seed)
    point = statistic_fn(data)
    if len(data) < 2:
        return point, point, point

    boot_stats = []
    for _ in range(n):
        sample = rng.choices(data, k=len(data))
        boot_stats.append(statistic_fn(sample))
    boot_stats.sort()

    lo_idx = max(0, int(n * alpha / 2))
    hi_idx = min(n - 1, int(n * (1 - alpha / 2)))
    return point, boot_stats[lo_idx], boot_stats[hi_idx]


def classify_hours(hrs):
    """Map estimated hours to S/M/L/XL."""
    if hrs <= 2:
        return "S"
    elif hrs <= 8:
        return "M"
    elif hrs <= 24:
        return "L"
    else:
        return "XL"


def header(title):
    w = 80
    print(f"\n{'=' * w}")
    print(f"  {title}")
    print(f"{'=' * w}")


def section(title):
    print(f"\n── {title} ──")


def tbl(headers, rows, col_widths=None):
    if not rows:
        print("  (no data)")
        return
    if not col_widths:
        col_widths = [
            max(len(str(h)), max((len(str(r[i])) for r in rows), default=4)) + 2
            for i, h in enumerate(headers)
        ]
    fmt = "  " + "".join(
        f"{{:<{w}}}" if i == 0 else f"{{:>{w}}}" for i, w in enumerate(col_widths)
    )
    print(fmt.format(*headers))
    print("  " + "".join("-" * w for w in col_widths))
    for r in rows:
        print(fmt.format(*[str(x) for x in r]))


# ── Data Loaders ─────────────────────────────────────────────


def safe_float(val):
    if not val or str(val).strip() in ("?", "NA", "", "na", "N/A"):
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, AttributeError):
        return None


def load_csv_safe(path, encoding="utf-8", delimiter=","):
    try:
        with open(path, encoding=encoding) as f:
            return list(csv.DictReader(f, delimiter=delimiter))
    except UnicodeDecodeError:
        with open(path, encoding="latin-1") as f:
            return list(csv.DictReader(f, delimiter=delimiter))


def load_estimate_actual_pairs():
    """Load all datasets with estimate-actual pairs. Returns list of dicts."""
    all_data = []

    # CESAW (61k tasks)
    path = os.path.join(DATASETS_DIR, "CESAW_task_fact.csv")
    if os.path.exists(path):
        for r in load_csv_safe(path):
            plan = safe_float(r.get("task_plan_time_minutes"))
            actual = safe_float(r.get("task_actual_time_minutes"))
            if plan and actual and plan > 0 and actual > 0:
                all_data.append(
                    {
                        "est_hrs": plan / 60,
                        "actual_hrs": actual / 60,
                        "phase": r.get("phase_short_name", ""),
                        "source": "CESAW",
                    }
                )

    # SiP (12k tasks)
    path = os.path.join(DATASETS_DIR, "Sip-task-info.csv")
    if os.path.exists(path):
        for r in load_csv_safe(path, encoding="latin-1"):
            est = safe_float(r.get("HoursEstimate"))
            actual = safe_float(r.get("HoursActual"))
            if est and actual and est > 0 and actual > 0:
                all_data.append(
                    {
                        "est_hrs": est,
                        "actual_hrs": actual,
                        "phase": r.get("SubCategory", ""),
                        "category": r.get("Category", ""),
                        "source": "SiP",
                    }
                )

    # Renzo Pomodoro (17k tasks, 25min units)
    path = os.path.join(DATASETS_DIR, "renzo-pomodoro.csv")
    if os.path.exists(path):
        for r in load_csv_safe(path):
            est = safe_float(r.get("estimate"))
            actual = safe_float(r.get("actual"))
            if est and actual and est > 0 and actual > 0:
                all_data.append(
                    {
                        "est_hrs": est * 25 / 60,
                        "actual_hrs": actual * 25 / 60,
                        "phase": "",
                        "source": "Renzo",
                    }
                )

    return all_data


def load_reviews_with_stories():
    """Load Project-22 reviews joined to stories via Branch.

    Returns list of dicts with review_min, passed, story_points, story_total_days.
    """
    # Load stories keyed by Branch
    story_path = os.path.join(DATASETS_DIR, "Project-22", "story-info.csv")
    review_path = os.path.join(DATASETS_DIR, "Project-22", "review-info.csv")

    if not os.path.exists(story_path) or not os.path.exists(review_path):
        return []

    stories_by_branch = {}
    for r in load_csv_safe(story_path):
        branch = r.get("Branch", "").strip()
        pts = safe_float(r.get("StoryPoints"))
        total = safe_float(r.get("Total"))
        if branch and pts and total and pts > 0 and total > 0:
            stories_by_branch[branch] = {
                "story_points": int(pts),
                "total_days": total,
            }

    joined = []
    for r in load_csv_safe(review_path):
        mins = safe_float(r.get("ReviewMinutes"))
        branch = r.get("Branch", "").strip()
        passed = r.get("PassedReview", "").strip().lower() == "yes"
        author = r.get("Author", "").strip()
        reviewer = r.get("Reviewer", "").strip()
        if mins and mins > 0:
            entry = {
                "review_min": mins,
                "passed": passed,
                "branch": branch,
                "author": author,
                "reviewer": reviewer,
            }
            story = stories_by_branch.get(branch)
            if story:
                entry["story_points"] = story["story_points"]
                entry["total_days"] = story["total_days"]
            joined.append(entry)

    return joined


def load_reviews_raw():
    """Load raw Project-22 reviews."""
    path = os.path.join(DATASETS_DIR, "Project-22", "review-info.csv")
    if not os.path.exists(path):
        return []
    data = []
    for r in load_csv_safe(path):
        mins = safe_float(r.get("ReviewMinutes"))
        if mins and mins > 0:
            data.append(
                {
                    "review_min": mins,
                    "passed": r.get("PassedReview", "").strip().lower() == "yes",
                    "branch": r.get("Branch", "").strip(),
                    "author": r.get("Author", "").strip(),
                    "reviewer": r.get("Reviewer", "").strip(),
                }
            )
    return data


def load_metr_runs():
    """Load METR benchmark runs from JSONL."""
    path = os.path.join(
        BENCHMARKS_DIR, "metr", "reports", "time-horizon-1-1", "data", "raw", "runs.jsonl"
    )
    if not os.path.exists(path):
        return []
    results = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            # JSON values are already typed — don't use safe_float (it rejects numeric 0)
            def _num(v):
                if v is None:
                    return None
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None

            results.append({
                "human_minutes": _num(obj.get("human_minutes")),
                "score_binarized": _num(obj.get("score_binarized")),
                "alias": obj.get("alias", ""),
                "task_id": obj.get("task_id", ""),
                "tokens_count": _num(obj.get("tokens_count")),
                "generation_cost": _num(obj.get("generation_cost")),
            })
    return results


def load_openhands_sample():
    """Load OpenHands benchmark sample from CSV."""
    path = os.path.join(BENCHMARKS_DIR, "openhands-sample.csv")
    if not os.path.exists(path):
        return []
    rows = load_csv_safe(path)
    results = []
    for r in rows:
        results.append({
            "instance_id": r.get("instance_id", ""),
            "repo": r.get("repo", ""),
            "resolved": r.get("resolved", "").strip().lower() in ("true", "1", "yes"),
            "exit_status": r.get("exit_status", ""),
        })
    return results


def load_aider_leaderboard():
    """Load Aider leaderboard data from YAML files.

    Falls back to basic line-by-line parsing if PyYAML is not available.
    """
    aider_dir = os.path.join(BENCHMARKS_DIR, "aider")
    if not os.path.exists(aider_dir):
        return []

    try:
        import yaml
        has_yaml = True
    except ImportError:
        has_yaml = False

    results = []
    for fname in sorted(os.listdir(aider_dir)):
        if not fname.endswith(".yml") and not fname.endswith(".yaml"):
            continue
        benchmark_name = os.path.splitext(fname)[0]
        fpath = os.path.join(aider_dir, fname)

        if has_yaml:
            with open(fpath, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, list):
                continue
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                results.append({
                    "model": entry.get("model", ""),
                    "benchmark": benchmark_name,
                    "pass_rate": safe_float(entry.get("pass_rate_2")),
                    "total_cost": safe_float(entry.get("total_cost")),
                    "seconds_per_case": safe_float(entry.get("seconds_per_case")),
                    "prompt_tokens": safe_float(entry.get("prompt_tokens")),
                    "completion_tokens": safe_float(entry.get("completion_tokens")),
                    "thinking_tokens": safe_float(entry.get("thinking_tokens")),
                    "test_cases": safe_float(entry.get("test_cases")),
                })
        else:
            # Basic line-by-line YAML parsing fallback
            with open(fpath, encoding="utf-8") as f:
                lines = f.readlines()
            current = {}
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("- "):
                    if current:
                        current["benchmark"] = benchmark_name
                        results.append(current)
                    current = {}
                    stripped = stripped[2:]
                if ":" in stripped:
                    key, _, val = stripped.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if key == "model":
                        current["model"] = val
                    elif key == "pass_rate_2":
                        current["pass_rate"] = safe_float(val)
                    elif key == "total_cost":
                        current["total_cost"] = safe_float(val)
                    elif key == "seconds_per_case":
                        current["seconds_per_case"] = safe_float(val)
                    elif key == "prompt_tokens":
                        current["prompt_tokens"] = safe_float(val)
                    elif key == "completion_tokens":
                        current["completion_tokens"] = safe_float(val)
                    elif key == "thinking_tokens":
                        current["thinking_tokens"] = safe_float(val)
                    elif key == "test_cases":
                        current["test_cases"] = safe_float(val)
            if current:
                current["benchmark"] = benchmark_name
                results.append(current)

    return results


def load_tokenomics():
    """Load tokenomics phase distribution from CSV."""
    path = os.path.join(BENCHMARKS_DIR, "tokenomics.csv")
    if not os.path.exists(path):
        return []
    return load_csv_safe(path)


def load_onprem_tokens():
    """Load on-prem token usage data from CSV."""
    path = os.path.join(BENCHMARKS_DIR, "onprem-tokens.csv")
    if not os.path.exists(path):
        return []
    return load_csv_safe(path)


# ── Analysis 1: Distribution Fitting ─────────────────────────


def analysis_1_distribution_fitting():
    """For each S/M/L/XL band, fit log-normal, normal, and PERT-beta to
    actual effort. KS goodness-of-fit test determines which wins."""
    header("ANALYSIS 1: DISTRIBUTION FITTING")
    print("  Fit log-normal, normal, and beta to actual effort per size band.")
    print("  KS test determines best fit. Tests our PERT-beta assumption.\n")

    data = load_estimate_actual_pairs()
    if not data:
        print("  ERROR: No estimate-actual data found.")
        return []

    audits = []

    for size in ["S", "M", "L", "XL"]:
        tasks = [d for d in data if classify_hours(d["est_hrs"]) == size]
        if len(tasks) < 30:
            continue

        actuals = [d["actual_hrs"] for d in tasks]
        actuals_sorted = sorted(actuals)
        n = len(actuals)

        section(f"Band {size} (n={n})")

        # Descriptive stats
        mn = mean(actuals)
        md = median(actuals)
        sd = stdev(actuals)
        skew_approx = 3 * (mn - md) / sd if sd > 0 else 0
        print(f"  Mean={mn:.2f}h  Median={md:.2f}h  SD={sd:.2f}h  Skew≈{skew_approx:.2f}")

        if HAS_SCIPY:
            actuals_arr = np.array(actuals)
            positive = actuals_arr[actuals_arr > 0]

            results = []

            # Normal fit
            mu_n, std_n = stats.norm.fit(positive)
            ks_n, p_n = stats.kstest(positive, "norm", args=(mu_n, std_n))
            results.append(("normal", ks_n, p_n, f"μ={mu_n:.2f}, σ={std_n:.2f}"))

            # Log-normal fit
            shape_ln, loc_ln, scale_ln = stats.lognorm.fit(positive, floc=0)
            ks_ln, p_ln = stats.kstest(
                positive, "lognorm", args=(shape_ln, loc_ln, scale_ln)
            )
            results.append(
                (
                    "log-normal",
                    ks_ln,
                    p_ln,
                    f"σ={shape_ln:.2f}, μ={math.log(scale_ln):.2f}",
                )
            )

            # Beta fit (PERT approximation)
            lo = min(positive)
            hi = max(positive)
            if hi > lo:
                scaled = (positive - lo) / (hi - lo)
                scaled = np.clip(scaled, 1e-10, 1 - 1e-10)
                try:
                    a_b, b_b, loc_b, scale_b = stats.beta.fit(
                        scaled, floc=0, fscale=1
                    )
                    ks_b, p_b = stats.kstest(scaled, "beta", args=(a_b, b_b, 0, 1))
                    results.append(
                        ("beta (PERT)", ks_b, p_b, f"α={a_b:.2f}, β={b_b:.2f}")
                    )
                except Exception:
                    # Beta fit can fail on extreme distributions
                    results.append(("beta (PERT)", 1.0, 0.0, "fit failed"))
            else:
                results.append(("beta (PERT)", 1.0, 0.0, "degenerate"))

            # Sort by KS statistic (lower = better fit)
            results.sort(key=lambda x: x[1])
            best = results[0][0]

            rows = []
            for name, ks_d, p_val, params in results:
                tag = " ← BEST" if name == best else ""
                rows.append(
                    [name, f"{ks_d:.4f}", f"{p_val:.4f}", params, tag]
                )
            tbl(
                ["Distribution", "KS D", "p-value", "Parameters", ""],
                rows,
                [14, 9, 9, 28, 8],
            )

            # Quantify PERT error if log-normal wins
            pert_ks = next(r[1] for r in results if r[0] == "beta (PERT)")
            lognorm_ks = next(r[1] for r in results if r[0] == "log-normal")
            if best == "log-normal":
                err = pert_ks - lognorm_ks
                print(
                    f"\n  PERT-beta KS penalty vs log-normal: +{err:.4f}"
                )

            audits.append(
                ParameterAudit(
                    name=f"PERT assumption ({size})",
                    current_value="beta",
                    recommended_value=best,
                    ci_lower=results[0][1],
                    ci_upper=pert_ks,
                    sample_size=n,
                    test_statistic=f"KS D={results[0][1]:.4f}",
                    evidence_tier=3,
                    recommendation="adjust" if best != "beta (PERT)" else "keep",
                    rationale=f"Best fit is {best} (KS D={results[0][1]:.4f})",
                )
            )
        else:
            # Without scipy: manual log-normal check via log-transformed normality
            log_actuals = sorted([math.log(a) for a in actuals if a > 0])
            log_mn = mean(log_actuals)
            log_sd = stdev(log_actuals)
            log_md = median(log_actuals)
            log_skew = 3 * (log_mn - log_md) / log_sd if log_sd > 0 else 0

            print(f"  Log-transform: mean={log_mn:.2f}  SD={log_sd:.2f}  skew≈{log_skew:.2f}")
            is_lognormal = abs(log_skew) < abs(skew_approx)
            verdict = "log-normal likely" if is_lognormal else "inconclusive"
            print(f"  Log-transform reduces skew: {is_lognormal} → {verdict}")
            print("  (Install scipy for KS goodness-of-fit tests)")

            audits.append(
                ParameterAudit(
                    name=f"PERT assumption ({size})",
                    current_value="beta",
                    recommended_value="log-normal (likely)" if is_lognormal else "SKIPPED",
                    ci_lower=0,
                    ci_upper=0,
                    sample_size=n,
                    test_statistic="skew heuristic",
                    evidence_tier=2,
                    recommendation="flag" if is_lognormal else "keep",
                    rationale=f"Skew raw={skew_approx:.2f}, log={log_skew:.2f}",
                )
            )

    return audits


# ── Analysis 2: Optimal Confidence Multipliers ───────────────


def analysis_2_confidence_multipliers():
    """Derive multipliers that deliver 50%/80%/90% capture rates per size band."""
    header("ANALYSIS 2: OPTIMAL CONFIDENCE MULTIPLIERS")
    print("  Derive size-dependent multipliers from actual/estimate ratios.")
    print("  Current: flat 1.0x / 1.4x / 1.8x across all sizes.\n")

    data = load_estimate_actual_pairs()
    if not data:
        print("  ERROR: No data found.")
        return []

    audits = []

    for size in ["S", "M", "L", "XL"]:
        tasks = [d for d in data if classify_hours(d["est_hrs"]) == size]
        if len(tasks) < 30:
            continue

        # actual/estimate ratio — the multiplier needed to capture each task
        ratios = sorted([d["actual_hrs"] / d["est_hrs"] for d in tasks])
        n = len(ratios)

        section(f"Band {size} (n={n})")

        rows = []
        for target_pct, current_mult in [(50, 1.0), (80, 1.4), (90, 1.8)]:
            # Quantile of ratio distribution = required multiplier
            def quantile_fn(data, p=target_pct):
                s = sorted(data)
                return pct(s, p)

            opt, ci_lo, ci_hi = bootstrap_ci(ratios, lambda d, p=target_pct: pct(sorted(d), p))

            # Actual capture rate with current multiplier
            capture = sum(1 for r in ratios if r <= current_mult) / n

            rows.append(
                [
                    f"{target_pct}%",
                    f"{current_mult:.2f}x",
                    f"{opt:.2f}x",
                    f"[{ci_lo:.2f}, {ci_hi:.2f}]",
                    f"{capture:.0%}",
                ]
            )

            audits.append(
                ParameterAudit(
                    name=f"confidence_mult {target_pct}% ({size})",
                    current_value=f"{current_mult}x",
                    recommended_value=f"{opt:.2f}x",
                    ci_lower=ci_lo,
                    ci_upper=ci_hi,
                    sample_size=n,
                    test_statistic=f"actual capture={capture:.0%}",
                    evidence_tier=2,
                    recommendation=(
                        "keep"
                        if abs(opt - current_mult) / current_mult < 0.15
                        else "adjust"
                    ),
                    rationale=f"Current {current_mult}x captures {capture:.0%} (target {target_pct}%)",
                )
            )

        tbl(
            ["Target", "Current", "Optimal", "95% CI", "Actual Capture"],
            rows,
            [8, 10, 10, 16, 16],
        )

    return audits


# ── Analysis 3: Review Time Regression ───────────────────────


def analysis_3_review_regression():
    """Regress review minutes on story size, pass/fail, author, reviewer."""
    header("ANALYSIS 3: REVIEW TIME REGRESSION")
    print("  Project-22 reviews joined to stories. Predict review time per band.\n")

    joined = load_reviews_with_stories()
    if not joined:
        print("  ERROR: No joined review-story data found.")
        return []

    # Only use reviews that joined to a story
    with_story = [r for r in joined if "story_points" in r]
    print(f"  Total reviews: {len(joined)}")
    print(f"  Joined to stories: {len(with_story)}")

    if not with_story:
        print("  No reviews could be joined to stories.")
        return []

    audits = []

    # Map story points to size bands
    def pts_to_size(pts):
        if pts <= 2:
            return "S"
        elif pts <= 5:
            return "M"
        elif pts <= 13:
            return "L"
        else:
            return "XL"

    # Review time by size band
    section("3.1 — Review Minutes by Story Size Band")
    our_review = REVIEW_MINUTES["standard"]

    rows = []
    for size in ["S", "M", "L", "XL"]:
        reviews = [
            r["review_min"] for r in with_story if pts_to_size(r["story_points"]) == size
        ]
        if len(reviews) < 5:
            rows.append([size, len(reviews), "-", "-", "-", str(our_review[size]), "-"])
            continue

        med, ci_lo, ci_hi = bootstrap_ci(reviews, median)
        mn = mean(reviews)

        rows.append(
            [
                size,
                len(reviews),
                f"{med:.0f}",
                f"{mn:.0f}",
                f"[{ci_lo:.0f}, {ci_hi:.0f}]",
                str(our_review[size]),
                "adjust" if abs(med - our_review[size]) / our_review[size] > 0.3 else "keep",
            ]
        )

        audits.append(
            ParameterAudit(
                name=f"review_minutes ({size})",
                current_value=our_review[size],
                recommended_value=f"{med:.0f}",
                ci_lower=ci_lo,
                ci_upper=ci_hi,
                sample_size=len(reviews),
                test_statistic=f"median={med:.0f}",
                evidence_tier=2,
                recommendation=(
                    "keep"
                    if abs(med - our_review[size]) / our_review[size] <= 0.3
                    else "adjust"
                ),
                rationale=f"Data median {med:.0f} vs current {our_review[size]} (human-only code)",
            )
        )

    tbl(
        ["Size", "N", "Median", "Mean", "95% CI", "Current", "Verdict"],
        rows,
        [6, 6, 8, 8, 14, 9, 8],
    )

    # Pass/fail breakdown
    section("3.2 — Review Time: Pass vs Fail")
    passed = [r["review_min"] for r in joined if r["passed"]]
    failed = [r["review_min"] for r in joined if not r["passed"]]

    if passed and failed:
        p_med, p_lo, p_hi = bootstrap_ci(passed, median)
        f_med, f_lo, f_hi = bootstrap_ci(failed, median)
        print(f"  Passed: n={len(passed)}, median={p_med:.0f}m  CI=[{p_lo:.0f}, {p_hi:.0f}]")
        print(f"  Failed: n={len(failed)}, median={f_med:.0f}m  CI=[{f_lo:.0f}, {f_hi:.0f}]")
        if p_med > 0:
            print(f"  Ratio (failed/passed): {f_med / p_med:.2f}x")

    # Author effect
    section("3.3 — Review Time by Author")
    by_author = defaultdict(list)
    for r in joined:
        by_author[r["author"]].append(r["review_min"])

    rows = []
    for author in sorted(by_author, key=lambda a: -len(by_author[a])):
        reviews = by_author[author]
        if len(reviews) < 10:
            continue
        md = median(reviews)
        rows.append([author, len(reviews), f"{md:.0f}", f"{mean(reviews):.0f}"])

    if rows:
        tbl(["Author", "N", "Median", "Mean"], rows, [8, 6, 8, 8])

    # OLS regression (manual normal equations via numpy if available)
    if HAS_SCIPY and with_story:
        section("3.4 — OLS Regression: ReviewMin ~ StoryPoints + PassFail")

        y = np.array([r["review_min"] for r in with_story])
        X = np.column_stack(
            [
                np.ones(len(with_story)),
                [r["story_points"] for r in with_story],
                [1.0 if r["passed"] else 0.0 for r in with_story],
            ]
        )

        # Normal equations: beta = (X'X)^-1 X'y
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            y_pred = X @ beta
            residuals = y - y_pred
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            print(f"  Intercept:     {beta[0]:>8.2f} min")
            print(f"  StoryPoints:   {beta[1]:>8.2f} min/point")
            print(f"  PassedReview:  {beta[2]:>8.2f} min (passed vs failed)")
            print(f"  R²:            {r_squared:.4f}")
            print(f"  n:             {len(with_story)}")
        except Exception as e:
            print(f"  OLS failed: {e}")

    return audits


# ── Analysis 4: Task Type Multiplier Derivation ──────────────


def analysis_4_task_type_multipliers():
    """Derive multipliers from actual overrun ratios relative to coding baseline."""
    header("ANALYSIS 4: TASK TYPE MULTIPLIER DERIVATION")
    print("  Derive from overrun ratios relative to coding/enhancement baseline.\n")

    data = load_estimate_actual_pairs()
    if not data:
        print("  ERROR: No data found.")
        return []

    audits = []

    # SiP data (has SubCategory)
    sip = [d for d in data if d["source"] == "SiP" and d.get("phase")]
    if sip:
        section("4.1 — SiP: Overrun Ratios by SubCategory")
        by_cat = defaultdict(list)
        for d in sip:
            ratio = d["actual_hrs"] / d["est_hrs"]
            by_cat[d["phase"]].append(ratio)

        # Baseline = Enhancement (maps to "coding")
        baseline_ratios = by_cat.get("Enhancement", [])
        if baseline_ratios:
            baseline_med = median(baseline_ratios)
            print(f"  Baseline (Enhancement): median ratio = {baseline_med:.3f}, n={len(baseline_ratios)}")

            # Mapping from SiP SubCategory to our task types
            sip_mapping = {
                "Enhancement": "coding",
                "Bug": "bug-fix",
                "In House Support": "infrastructure",
                "External Support": "infrastructure",
                "Configuration": "infrastructure",
            }

            rows = []
            for subcat, our_type in sorted(sip_mapping.items()):
                ratios = by_cat.get(subcat, [])
                if len(ratios) < 10:
                    continue

                cat_med = median(ratios)
                derived_mult = cat_med / baseline_med if baseline_med > 0 else 0

                def ratio_fn(d):
                    return median(d) / baseline_med if baseline_med > 0 else 0

                _, ci_lo, ci_hi = bootstrap_ci(ratios, ratio_fn)
                current = TASK_TYPE_MULTIPLIER.get(our_type, 1.0)

                rows.append(
                    [
                        subcat,
                        our_type,
                        len(ratios),
                        f"{cat_med:.3f}",
                        f"{derived_mult:.2f}x",
                        f"[{ci_lo:.2f}, {ci_hi:.2f}]",
                        f"{current:.1f}x",
                    ]
                )

                audits.append(
                    ParameterAudit(
                        name=f"task_type_mult ({our_type}, SiP)",
                        current_value=f"{current}x",
                        recommended_value=f"{derived_mult:.2f}x",
                        ci_lower=ci_lo,
                        ci_upper=ci_hi,
                        sample_size=len(ratios),
                        test_statistic=f"median_ratio={cat_med:.3f}",
                        evidence_tier=3,
                        recommendation=(
                            "keep"
                            if abs(derived_mult - current) / max(current, 0.01) < 0.25
                            else "adjust"
                        ),
                        rationale=f"SiP {subcat}: derived {derived_mult:.2f}x vs current {current}x",
                    )
                )

            tbl(
                ["SubCategory", "Our Type", "N", "Med Ratio", "Derived", "95% CI", "Current"],
                rows,
                [22, 16, 6, 11, 9, 16, 9],
            )

    # CESAW data (has phase_short_name)
    cesaw = [d for d in data if d["source"] == "CESAW" and d.get("phase")]
    if cesaw:
        section("4.2 — CESAW: Overrun Ratios by Phase")
        by_phase = defaultdict(list)
        for d in cesaw:
            ratio = d["actual_hrs"] / d["est_hrs"]
            by_phase[d["phase"]].append(ratio)

        # Find a coding-like baseline
        coding_phases = ["CODE", "Code", "UT", "Coding"]
        baseline = []
        baseline_name = None
        for cp in coding_phases:
            if cp in by_phase and len(by_phase[cp]) > 50:
                baseline = by_phase[cp]
                baseline_name = cp
                break

        if not baseline:
            # Use the largest phase as baseline
            baseline_name = max(by_phase, key=lambda k: len(by_phase[k]))
            baseline = by_phase[baseline_name]

        baseline_med = median(baseline)
        print(f"  Baseline phase ({baseline_name}): median ratio = {baseline_med:.3f}, n={len(baseline)}")

        rows = []
        for phase in sorted(by_phase, key=lambda k: -len(by_phase[k]))[:12]:
            ratios = by_phase[phase]
            if len(ratios) < 20:
                continue
            cat_med = median(ratios)
            derived = cat_med / baseline_med if baseline_med > 0 else 0
            rows.append([phase, len(ratios), f"{cat_med:.3f}", f"{derived:.2f}x"])

        tbl(
            ["Phase", "N", "Med Ratio", "Relative"],
            rows,
            [25, 7, 11, 10],
        )

    # Combined: inverse-variance weighted multiplier per type
    if sip and cesaw:
        section("4.3 — Combined Multiplier Estimates (inverse-variance weighted)")
        print("  Combining SiP and CESAW where both have mapped categories.\n")

        # We only have reliable SiP mappings, so report those as primary
        print("  Primary source: SiP (direct SubCategory mapping)")
        print("  CESAW phases are less directly mappable — used as directional support.")

    return audits


# ── Analysis 5: Human Fix Ratio Proxy ────────────────────────


def analysis_5_fix_ratio():
    """Estimate rework overhead from review pass/fail patterns."""
    header("ANALYSIS 5: HUMAN FIX RATIO PROXY")
    print("  Estimate rework from review cycles. Current human_fix_ratio = 0.20.\n")

    reviews = load_reviews_raw()
    if not reviews:
        print("  ERROR: No review data found.")
        return []

    # Group reviews by branch
    by_branch = defaultdict(list)
    for r in reviews:
        by_branch[r["branch"]].append(r)

    audits = []

    section("5.1 — Review Cycles per Branch")
    cycle_counts = []
    rework_ratios = []

    for branch, revs in by_branch.items():
        n_reviews = len(revs)
        cycle_counts.append(n_reviews)

        # Sort by review order (they appear chronologically in the data)
        total_min = sum(r["review_min"] for r in revs)
        if n_reviews > 1 and total_min > 0:
            # Rework time = all reviews except the last passing one
            final_pass = [r for r in revs if r["passed"]]
            if final_pass:
                final_min = final_pass[-1]["review_min"]
                rework_min = total_min - final_min
                rework_ratios.append(rework_min / total_min)
            else:
                # All failed — 100% rework
                rework_ratios.append(1.0)
        elif n_reviews == 1:
            if revs[0]["passed"]:
                rework_ratios.append(0.0)
            else:
                rework_ratios.append(1.0)

    n_branches = len(cycle_counts)
    print(f"  Unique branches: {n_branches}")
    print(f"  Avg reviews/branch: {mean(cycle_counts):.1f}")
    print(f"  Branches with >1 review: {sum(1 for c in cycle_counts if c > 1)}")

    cycle_dist = defaultdict(int)
    for c in cycle_counts:
        cycle_dist[min(c, 5)] += 1

    rows = []
    for k in sorted(cycle_dist):
        label = f"{k}" if k < 5 else "5+"
        rows.append([label, cycle_dist[k], f"{cycle_dist[k] / n_branches:.0%}"])
    tbl(["Cycles", "Count", "Pct"], rows, [8, 8, 8])

    section("5.2 — Fix Ratio Estimate")
    if rework_ratios:
        fix, ci_lo, ci_hi = bootstrap_ci(rework_ratios, mean)
        fix_med, med_lo, med_hi = bootstrap_ci(rework_ratios, median)

        print(f"  Mean fix_ratio:   {fix:.3f}  CI=[{ci_lo:.3f}, {ci_hi:.3f}]")
        print(f"  Median fix_ratio: {fix_med:.3f}  CI=[{med_lo:.3f}, {med_hi:.3f}]")
        print(f"  Current value:    0.20")

        recommendation = "keep" if abs(fix - 0.20) < 0.08 else "adjust"
        audits.append(
            ParameterAudit(
                name="human_fix_ratio",
                current_value=0.20,
                recommended_value=f"{fix:.3f}",
                ci_lower=ci_lo,
                ci_upper=ci_hi,
                sample_size=len(rework_ratios),
                test_statistic=f"mean rework ratio={fix:.3f}",
                evidence_tier=2,
                recommendation=recommendation,
                rationale=f"Proxy from {n_branches} review branches, mean rework={fix:.3f}",
            )
        )

        print(
            f"\n  NOTE: This is a proxy from code review cycles, not direct rework measurement."
        )
        print(
            f"  The actual human_fix_ratio includes non-review rework (debugging, refactoring)."
        )

    return audits


# ── Analysis 6: Base Rounds Calibration ──────────────────────


def analysis_6_base_rounds():
    """Reverse-engineer implied base rounds from actual effort data."""
    header("ANALYSIS 6: BASE ROUNDS CALIBRATION")
    print("  Invert formula to find implied rounds from actual effort.\n")

    data = load_estimate_actual_pairs()
    if not data:
        print("  ERROR: No data found.")
        return []

    audits = []

    # Default parameters used to invert
    risk_coeff = 1.3
    domain_fam = 1.0
    integration_overhead = 0.15
    human_fix_ratio = 0.20
    mpr_min, mpr_max = MINUTES_PER_ROUND["partial"]  # 2, 3
    review_depth = "standard"
    org = 1.0  # solo-startup

    section("6.1 — Implied Base Rounds per Band")
    print("  Formula inversion: actual_min = rounds × mpr × (1 + integration + adj_fix)")
    print("                     + review + planning")
    print("  Solving for rounds.\n")

    for size in ["S", "M", "L", "XL"]:
        tasks = [d for d in data if classify_hours(d["est_hrs"]) == size]
        if len(tasks) < 30:
            continue

        from test_formulas import AGENT_EFFECTIVENESS

        ae = AGENT_EFFECTIVENESS[size]
        adj_fix = human_fix_ratio + (1 - ae) * 0.3
        review = REVIEW_MINUTES[review_depth][size]
        plan_min, plan_max = PLANNING_MINUTES[size]

        # Invert: actual_minutes = rounds × mpr × (1 + integration + adj_fix) × org
        #                         + review × org + planning × org
        # Simplified for task_type=coding (mult=1.0):
        # actual_min = rounds × mpr × (1 + overhead_factor) + human_fixed
        overhead_factor = integration_overhead + adj_fix
        human_fixed_min = (review + plan_min) * org
        human_fixed_max = (review + plan_max) * org

        implied_rounds = []
        for d in tasks:
            actual_min = d["actual_hrs"] * 60  # convert to minutes
            # Use midpoint of mpr range
            mpr_mid = (mpr_min + mpr_max) / 2
            human_fixed_mid = (human_fixed_min + human_fixed_max) / 2

            agent_portion = actual_min - human_fixed_mid
            if agent_portion > 0:
                raw_rounds = agent_portion / (mpr_mid * (1 + overhead_factor))
                # Undo risk_coeff and domain_fam to get base rounds
                base_rounds = raw_rounds / (risk_coeff * domain_fam)
                if 0 < base_rounds < 10000:  # sanity check
                    implied_rounds.append(base_rounds)

        if not implied_rounds:
            continue

        n = len(implied_rounds)
        implied_sorted = sorted(implied_rounds)

        p25, p25_lo, p25_hi = bootstrap_ci(implied_rounds, lambda d: pct(sorted(d), 25))
        p75, p75_lo, p75_hi = bootstrap_ci(implied_rounds, lambda d: pct(sorted(d), 75))

        current_min, current_max = BASE_ROUNDS[size]

        section(f"Band {size} (n={n})")
        print(f"  Implied base rounds distribution:")
        print(f"    p10={pct(implied_sorted, 10):.0f}  p25={p25:.0f}  p50={pct(implied_sorted, 50):.0f}  p75={p75:.0f}  p90={pct(implied_sorted, 90):.0f}")
        print(f"  Current BASE_ROUNDS: ({current_min}, {current_max})")
        print(f"  Suggested (p25-p75): ({p25:.0f}, {p75:.0f})")
        print(f"    p25 CI: [{p25_lo:.0f}, {p25_hi:.0f}]")
        print(f"    p75 CI: [{p75_lo:.0f}, {p75_hi:.0f}]")

        audits.append(
            ParameterAudit(
                name=f"BASE_ROUNDS ({size})",
                current_value=f"({current_min}, {current_max})",
                recommended_value=f"({p25:.0f}, {p75:.0f})",
                ci_lower=p25_lo,
                ci_upper=p75_hi,
                sample_size=n,
                test_statistic=f"p25={p25:.0f}, p75={p75:.0f}",
                evidence_tier=2,
                recommendation=(
                    "keep"
                    if (
                        abs(p25 - current_min) / max(current_min, 1) < 0.4
                        and abs(p75 - current_max) / max(current_max, 1) < 0.4
                    )
                    else "adjust"
                ),
                rationale=f"Implied rounds p25-p75 from {n} tasks",
            )
        )

    return audits


# ── Analysis 7: Sensitivity Analysis ─────────────────────────


def analysis_7_sensitivity():
    """Tornado chart data — which parameters have the most impact."""
    header("ANALYSIS 7: SENSITIVITY ANALYSIS")
    print("  Sweep each parameter from min to max, measure delta in PERT estimate.\n")

    audits = []

    # Parameter ranges from formulas.md
    params = [
        ("risk_coefficient", 1.0, 2.5, 1.3),
        ("integration_overhead", 0.05, 0.30, 0.15),
        ("domain_familiarity", 0.8, 1.5, 1.0),
        ("human_fix_ratio", 0.05, 0.50, 0.20),
    ]

    # Discrete parameters
    discrete_params = [
        ("review_depth", ["light", "standard", "deep"]),
        ("confidence_level", [50, 80, 90]),
        ("definition_phase", ["ready", "design", "requirements", "concept"]),
        ("org_size", ["solo-startup", "growth", "enterprise"]),
        ("maturity", ["mostly-automated", "partial", "exploratory"]),
    ]

    for complexity in ["S", "M", "L", "XL"]:
        section(f"Sensitivity for {complexity}")

        # Baseline
        base = estimate(complexity=complexity)
        base_pert = base["pert_expected_minutes"]

        results = []

        # Continuous parameters
        for pname, lo, hi, default in params:
            kwargs_lo = {pname: lo}
            kwargs_hi = {pname: hi}
            r_lo = estimate(complexity=complexity, **kwargs_lo)
            r_hi = estimate(complexity=complexity, **kwargs_hi)
            pert_lo = r_lo["pert_expected_minutes"]
            pert_hi = r_hi["pert_expected_minutes"]
            delta = abs(pert_hi - pert_lo)
            pct_delta = delta / base_pert * 100 if base_pert > 0 else 0
            results.append((pname, pert_lo, pert_hi, delta, pct_delta, f"{lo}-{hi}"))

        # Discrete parameters
        for pname, values in discrete_params:
            perts = []
            for v in values:
                r = estimate(complexity=complexity, **{pname: v})
                perts.append(r["pert_expected_minutes"])
            pert_lo = min(perts)
            pert_hi = max(perts)
            delta = pert_hi - pert_lo
            pct_delta = delta / base_pert * 100 if base_pert > 0 else 0
            results.append(
                (pname, pert_lo, pert_hi, delta, pct_delta, f"{values[0]}..{values[-1]}")
            )

        # Sort by delta (tornado order)
        results.sort(key=lambda x: -x[3])

        rows = []
        for pname, p_lo, p_hi, delta, pct_d, range_str in results:
            bar_len = min(int(pct_d / 5), 30)
            bar = "█" * bar_len
            rows.append(
                [
                    pname,
                    range_str,
                    f"{p_lo:.0f}",
                    f"{p_hi:.0f}",
                    f"{delta:.0f}",
                    f"{pct_d:.0f}%",
                    bar,
                ]
            )

        tbl(
            ["Parameter", "Range", "Min", "Max", "Delta", "%Base", "Impact"],
            rows,
            [22, 22, 7, 7, 7, 7, 32],
        )

        # Record top 3 for audit
        for pname, p_lo, p_hi, delta, pct_d, _ in results[:3]:
            audits.append(
                ParameterAudit(
                    name=f"sensitivity ({pname}, {complexity})",
                    current_value="N/A",
                    recommended_value="N/A",
                    ci_lower=p_lo,
                    ci_upper=p_hi,
                    sample_size=0,
                    test_statistic=f"delta={delta:.0f}min ({pct_d:.0f}%)",
                    evidence_tier=3,
                    recommendation="flag" if pct_d > 50 else "keep",
                    rationale=f"Top sensitivity driver for {complexity}",
                )
            )

    # Flag parameters with zero data
    section("Parameters with Zero Empirical Data")
    print("  These cannot be validated with available datasets:\n")

    zero_data = [
        ("integration_overhead", 0.15, "No proxy dataset. Sensitivity shows moderate impact."),
        ("minutes_per_round", "1-5 by maturity", "No public round-level data exists."),
    ]

    for pname, current, note in zero_data:
        print(f"  {pname}: current={current}")
        print(f"    {note}")
        audits.append(
            ParameterAudit(
                name=pname,
                current_value=str(current),
                recommended_value="—",
                ci_lower=0,
                ci_upper=0,
                sample_size=0,
                test_statistic="none",
                evidence_tier=1,
                recommendation="flag",
                rationale=note,
            )
        )

    return audits


# ── Analysis 8: Agent Effectiveness (METR) ───────────────────


def analysis_8_agent_effectiveness():
    """Validate AGENT_EFFECTIVENESS against METR benchmark runs."""
    header("ANALYSIS 8: AGENT EFFECTIVENESS (METR)")
    print("  Compare METR task-horizon success rates to AGENT_EFFECTIVENESS.\n")

    runs = load_metr_runs()
    if not runs:
        print("  No data. Run: bash datasets/download_benchmarks.sh")
        return []

    from test_formulas import AGENT_EFFECTIVENESS

    audits = []

    # Filter runs with valid human_minutes and score
    valid = [r for r in runs if r["human_minutes"] is not None and r["score_binarized"] is not None]
    print(f"  Total runs loaded: {len(runs)}")
    print(f"  Valid runs (with human_minutes + score): {len(valid)}")

    if not valid:
        return []

    # Map human_minutes to size bands
    def classify_minutes(mins):
        hrs = mins / 60
        if hrs <= 2:
            return "S"
        elif hrs <= 8:
            return "M"
        elif hrs <= 24:
            return "L"
        else:
            return "XL"

    section("8.1 — Success Rate by Size Band")
    bands = defaultdict(list)
    for r in valid:
        band = classify_minutes(r["human_minutes"])
        bands[band].append(r["score_binarized"])

    rows = []
    for size in ["S", "M", "L", "XL"]:
        scores = bands.get(size, [])
        if not scores:
            continue
        rate, ci_lo, ci_hi = bootstrap_ci(scores, mean)
        expected = AGENT_EFFECTIVENESS[size]
        diff = rate - expected
        verdict = "keep" if abs(diff) < 0.15 else "adjust"
        rows.append([size, len(scores), f"{rate:.3f}", f"[{ci_lo:.3f}, {ci_hi:.3f}]",
                      f"{expected:.1f}", f"{diff:+.3f}", verdict.upper()])
        audits.append(ParameterAudit(
            name=f"AGENT_EFFECTIVENESS ({size})",
            current_value=expected,
            recommended_value=f"{rate:.3f}",
            ci_lower=ci_lo,
            ci_upper=ci_hi,
            sample_size=len(scores),
            test_statistic=f"success_rate={rate:.3f}",
            evidence_tier=2,
            recommendation=verdict,
            rationale=f"METR {size}-band success rate from {len(scores)} runs",
        ))

    tbl(["Band", "N", "Rate", "95% CI", "Current", "Diff", "Verdict"], rows,
        [6, 7, 8, 20, 9, 9, 8])

    # Success rate by agent (top 10 by count)
    section("8.2 — Success Rate by Agent (top 10)")
    by_agent = defaultdict(list)
    for r in valid:
        agent = r["alias"] or "unknown"
        by_agent[agent].append(r["score_binarized"])

    agent_rows = []
    for agent, scores in sorted(by_agent.items(), key=lambda x: -len(x[1])):
        agent_rows.append([agent[:30], len(scores), f"{mean(scores):.3f}"])
    tbl(["Agent", "N", "Rate"], agent_rows[:10], [32, 7, 8])

    # Token consumption per run
    section("8.3 — Token Consumption per Run")
    token_runs = [r["tokens_count"] for r in valid if r["tokens_count"] is not None and r["tokens_count"] > 0]
    if token_runs:
        t_med, t_lo, t_hi = bootstrap_ci(token_runs, median)
        t_mean = mean(token_runs)
        print(f"  Runs with token data: {len(token_runs)}")
        print(f"  Median tokens/run: {t_med:,.0f}  CI=[{t_lo:,.0f}, {t_hi:,.0f}]")
        print(f"  Mean tokens/run:   {t_mean:,.0f}")
        sorted_tokens = sorted(token_runs)
        print(f"  p10={pct(sorted_tokens, 10):,.0f}  p25={pct(sorted_tokens, 25):,.0f}  "
              f"p75={pct(sorted_tokens, 75):,.0f}  p90={pct(sorted_tokens, 90):,.0f}")
    else:
        print("  No token data available.")

    # Cost per run
    section("8.4 — Cost per Run")
    cost_runs = [r["generation_cost"] for r in valid if r["generation_cost"] is not None and r["generation_cost"] > 0]
    if cost_runs:
        c_med, c_lo, c_hi = bootstrap_ci(cost_runs, median)
        c_mean = mean(cost_runs)
        print(f"  Runs with cost data: {len(cost_runs)}")
        print(f"  Median cost/run: ${c_med:.2f}  CI=[${c_lo:.2f}, ${c_hi:.2f}]")
        print(f"  Mean cost/run:   ${c_mean:.2f}")
    else:
        print("  No cost data available.")

    return audits


# ── Analysis 9: Token Consumption ────────────────────────────


def analysis_9_token_consumption():
    """Validate TOKENS_PER_ROUND and OUTPUT_TOKEN_RATIO against benchmark data."""
    header("ANALYSIS 9: TOKEN CONSUMPTION")
    print("  Cross-reference token data from Tokenomics, On-prem, and Aider.\n")

    from test_formulas import TOKENS_PER_ROUND, OUTPUT_TOKEN_RATIO

    audits = []

    # 9.1 — Tokenomics phase distribution
    section("9.1 — Tokenomics Phase Distribution")
    tokenomics = load_tokenomics()
    if tokenomics:
        rows = []
        output_pcts = []
        for r in tokenomics:
            phase = r.get("phase", "")
            inp = safe_float(r.get("input_tokens_pct"))
            out = safe_float(r.get("output_tokens_pct"))
            reasoning = safe_float(r.get("reasoning_tokens_pct"))
            total = safe_float(r.get("total_tokens_pct"))
            rows.append([phase,
                         f"{inp:.1f}%" if inp is not None else "—",
                         f"{out:.1f}%" if out is not None else "—",
                         f"{reasoning:.1f}%" if reasoning is not None else "—",
                         f"{total:.1f}%" if total is not None else "—"])
            # Output ratio = (output + reasoning) / total (as proportions)
            if out is not None and total is not None and total > 0:
                out_total = (out or 0) + (reasoning or 0)
                output_pcts.append(out_total / 100.0)
        tbl(["Phase", "Input%", "Output%", "Reasoning%", "Total%"], rows,
            [20, 10, 10, 12, 10])

        if output_pcts:
            overall_out = mean(output_pcts)
            print(f"\n  Overall output ratio (output+reasoning / 100): {overall_out:.3f}")
            current_avg = mean([OUTPUT_TOKEN_RATIO[s] for s in ["S", "M", "L", "XL"]])
            print(f"  Current OUTPUT_TOKEN_RATIO avg: {current_avg:.3f}")
    else:
        print("  No data. Run: bash datasets/download_benchmarks.sh")

    # 9.2 — On-prem token usage
    section("9.2 — On-Prem Coding Task Token Usage")
    onprem = load_onprem_tokens()
    if onprem:
        rows = []
        for r in onprem:
            cat = r.get("category", "")
            task = r.get("task", "")
            desc = r.get("description", "")[:40]
            inp = safe_float(r.get("input_tokens"))
            out_n = safe_float(r.get("output_tokens_normal"))
            out_r = safe_float(r.get("output_tokens_reasoning"))
            rows.append([cat, task[:20],
                         f"{inp:,.0f}" if inp is not None else "—",
                         f"{out_n:,.0f}" if out_n is not None else "—",
                         f"{out_r:,.0f}" if out_r is not None else "—"])
        tbl(["Category", "Task", "Input", "Out(normal)", "Out(reasoning)"], rows,
            [12, 22, 12, 14, 16])
    else:
        print("  No data. Run: bash datasets/download_benchmarks.sh")

    # 9.3 — Aider token data
    section("9.3 — Aider Tokens per Case & Cost per Suite")
    aider = load_aider_leaderboard()
    aider_with_tokens = [a for a in aider
                         if a.get("prompt_tokens") is not None
                         and a.get("completion_tokens") is not None
                         and a.get("test_cases") is not None
                         and a["test_cases"] > 0]
    if aider_with_tokens:
        tokens_per_case = []
        rows = []
        for a in aider_with_tokens[:15]:  # show top 15
            prompt = a["prompt_tokens"] or 0
            completion = a["completion_tokens"] or 0
            thinking = a.get("thinking_tokens") or 0
            total = prompt + completion + thinking
            tpc = total / a["test_cases"]
            tokens_per_case.append(tpc)
            cost = a.get("total_cost")
            rows.append([a["model"][:25], a["benchmark"][:15],
                         f"{tpc:,.0f}",
                         f"${cost:.2f}" if cost is not None else "—"])
        tbl(["Model", "Benchmark", "Tok/Case", "Total$"], rows,
            [27, 17, 12, 10])

        if tokens_per_case:
            tpc_med, tpc_lo, tpc_hi = bootstrap_ci(tokens_per_case, median)
            print(f"\n  Median tokens/case: {tpc_med:,.0f}  CI=[{tpc_lo:,.0f}, {tpc_hi:,.0f}]")

            # Compare to TOKENS_PER_ROUND partial/S as a single-round proxy
            current_tpr_s = TOKENS_PER_ROUND["partial"]["S"]
            print(f"  Current TOKENS_PER_ROUND (partial, S): {current_tpr_s:,}")

            audits.append(ParameterAudit(
                name="tokens_per_case (Aider)",
                current_value=f"{current_tpr_s:,}",
                recommended_value=f"{tpc_med:,.0f}",
                ci_lower=tpc_lo,
                ci_upper=tpc_hi,
                sample_size=len(tokens_per_case),
                test_statistic=f"median tokens/case={tpc_med:,.0f}",
                evidence_tier=2,
                recommendation="keep" if abs(tpc_med - current_tpr_s) / current_tpr_s < 0.5 else "flag",
                rationale=f"Aider benchmark tokens per test case from {len(tokens_per_case)} entries",
            ))
    elif aider:
        print("  Aider data loaded but no entries with token data.")
    else:
        print("  No Aider data. Run: bash datasets/download_benchmarks.sh")

    return audits


# ── Analysis 10: Output Token Ratio ──────────────────────────


def analysis_10_output_ratio():
    """Validate OUTPUT_TOKEN_RATIO from Aider and Tokenomics data."""
    header("ANALYSIS 10: OUTPUT TOKEN RATIO")
    print("  Compute observed output ratios and compare to OUTPUT_TOKEN_RATIO.\n")

    from test_formulas import OUTPUT_TOKEN_RATIO

    audits = []
    combined_ratios = []

    # From Aider: output ratio = (completion + thinking) / (prompt + completion + thinking)
    section("10.1 — Output Ratios from Aider")
    aider = load_aider_leaderboard()
    aider_ratios = []
    for a in aider:
        prompt = a.get("prompt_tokens")
        completion = a.get("completion_tokens")
        thinking = a.get("thinking_tokens") or 0
        if prompt is not None and completion is not None and prompt > 0:
            total = prompt + completion + thinking
            ratio = (completion + thinking) / total
            aider_ratios.append(ratio)

    if aider_ratios:
        ar_med, ar_lo, ar_hi = bootstrap_ci(aider_ratios, median)
        ar_mean = mean(aider_ratios)
        print(f"  Entries with token data: {len(aider_ratios)}")
        print(f"  Median output ratio: {ar_med:.3f}  CI=[{ar_lo:.3f}, {ar_hi:.3f}]")
        print(f"  Mean output ratio:   {ar_mean:.3f}")
        combined_ratios.extend(aider_ratios)
    else:
        print("  No Aider token data available.")

    # From Tokenomics
    section("10.2 — Output Ratios from Tokenomics")
    tokenomics = load_tokenomics()
    tok_ratios = []
    for r in tokenomics:
        out = safe_float(r.get("output_tokens_pct"))
        reasoning = safe_float(r.get("reasoning_tokens_pct")) or 0
        inp = safe_float(r.get("input_tokens_pct"))
        if out is not None and inp is not None and (inp + out + reasoning) > 0:
            ratio = (out + reasoning) / (inp + out + reasoning)
            tok_ratios.append(ratio)

    if tok_ratios:
        tr_med, tr_lo, tr_hi = bootstrap_ci(tok_ratios, median)
        print(f"  Entries: {len(tok_ratios)}")
        print(f"  Median output ratio: {tr_med:.3f}  CI=[{tr_lo:.3f}, {tr_hi:.3f}]")
        combined_ratios.extend(tok_ratios)
    else:
        print("  No Tokenomics data available.")

    # Combined
    section("10.3 — Combined Output Ratio vs. OUTPUT_TOKEN_RATIO")
    if combined_ratios:
        cr_point, cr_lo, cr_hi = bootstrap_ci(combined_ratios, mean)
        cr_med, cm_lo, cm_hi = bootstrap_ci(combined_ratios, median)
        print(f"  Combined entries: {len(combined_ratios)}")
        print(f"  Mean output ratio:   {cr_point:.3f}  CI=[{cr_lo:.3f}, {cr_hi:.3f}]")
        print(f"  Median output ratio: {cr_med:.3f}  CI=[{cm_lo:.3f}, {cm_hi:.3f}]")

        rows = []
        for size in ["S", "M", "L", "XL"]:
            current = OUTPUT_TOKEN_RATIO[size]
            diff = cr_point - current
            verdict = "keep" if abs(diff) < 0.10 else "adjust"
            rows.append([size, f"{current:.2f}", f"{cr_point:.3f}",
                         f"[{cr_lo:.3f}, {cr_hi:.3f}]", f"{diff:+.3f}", verdict.upper()])
            audits.append(ParameterAudit(
                name=f"OUTPUT_TOKEN_RATIO ({size})",
                current_value=current,
                recommended_value=f"{cr_point:.3f}",
                ci_lower=cr_lo,
                ci_upper=cr_hi,
                sample_size=len(combined_ratios),
                test_statistic=f"mean output ratio={cr_point:.3f}",
                evidence_tier=2,
                recommendation=verdict,
                rationale=f"Combined Aider+Tokenomics output ratio from {len(combined_ratios)} entries",
            ))

        tbl(["Band", "Current", "Observed", "95% CI", "Diff", "Verdict"], rows,
            [6, 9, 10, 20, 9, 8])
    else:
        print("  No data. Run: bash datasets/download_benchmarks.sh")

    return audits


# ── Analysis 11: Cost Model Validation ───────────────────────


def analysis_11_cost_model():
    """Validate cost model against Aider benchmark costs."""
    header("ANALYSIS 11: COST MODEL VALIDATION")
    print("  Compare Aider benchmark costs to estimate_tokens() predictions.\n")

    from test_formulas import estimate_tokens

    audits = []

    aider = load_aider_leaderboard()
    costed = [a for a in aider if a.get("total_cost") is not None and a["total_cost"] > 0
              and a.get("test_cases") is not None and a["test_cases"] > 0]

    if not costed:
        print("  No data. Run: bash datasets/download_benchmarks.sh")
        return []

    # Classify models into tiers
    def classify_tier(model_name):
        name = model_name.lower()
        if any(k in name for k in ("haiku", "mini", "flash", "gemma", "phi")):
            return "economy"
        if any(k in name for k in ("opus", "gpt-5", "o1", "o3")):
            return "premium"
        return "standard"

    section("11.1 — Cost per Case by Model Tier")
    by_tier = defaultdict(list)
    for a in costed:
        tier = classify_tier(a["model"])
        cost_per_case = a["total_cost"] / a["test_cases"]
        by_tier[tier].append(cost_per_case)

    rows = []
    for tier in ["economy", "standard", "premium"]:
        costs = by_tier.get(tier, [])
        if not costs:
            continue
        med, ci_lo, ci_hi = bootstrap_ci(costs, median)
        avg = mean(costs)

        # Compare to formula estimate
        t = estimate_tokens(complexity="S", show_cost=True, model_tier=tier)
        formula_cost = t.get("pert_expected_cost_usd")
        formula_str = f"${formula_cost:.4f}" if formula_cost is not None else "—"
        diff = ""
        verdict = "keep"
        if formula_cost is not None and formula_cost > 0:
            ratio = med / formula_cost
            diff = f"{ratio:.1f}x"
            verdict = "keep" if 0.3 < ratio < 3.0 else "adjust"

        rows.append([tier, len(costs), f"${med:.4f}", f"[${ci_lo:.4f}, ${ci_hi:.4f}]",
                      formula_str, diff, verdict.upper()])
        audits.append(ParameterAudit(
            name=f"cost_per_case ({tier})",
            current_value=formula_str,
            recommended_value=f"${med:.4f}",
            ci_lower=ci_lo,
            ci_upper=ci_hi,
            sample_size=len(costs),
            test_statistic=f"median cost/case=${med:.4f}",
            evidence_tier=2,
            recommendation=verdict,
            rationale=f"Aider {tier}-tier median cost from {len(costs)} entries",
        ))

    tbl(["Tier", "N", "Median$/case", "95% CI", "Formula$", "Ratio", "Verdict"], rows,
        [10, 5, 14, 26, 10, 8, 8])

    # Overall cost distribution
    section("11.2 — Overall Cost Distribution")
    all_costs = [a["total_cost"] / a["test_cases"] for a in costed]
    sorted_costs = sorted(all_costs)
    print(f"  Total entries: {len(all_costs)}")
    print(f"  p10=${pct(sorted_costs, 10):.4f}  p25=${pct(sorted_costs, 25):.4f}  "
          f"p50=${pct(sorted_costs, 50):.4f}  p75=${pct(sorted_costs, 75):.4f}  "
          f"p90=${pct(sorted_costs, 90):.4f}")
    print(f"  Mean=${mean(all_costs):.4f}  Stdev=${stdev(all_costs):.4f}")

    return audits


# ── Parameter Audit Card ─────────────────────────────────────


def print_audit_card(all_audits: List[ParameterAudit]):
    """Print the final Parameter Audit Card."""
    header("PARAMETER AUDIT CARD")
    print("  Each weak parameter: current vs recommended with 95% CI.\n")

    tier_labels = {1: "T1", 2: "T2", 3: "T3"}

    # Deduplicate: prefer higher evidence tier, then keep first
    seen = {}
    for a in all_audits:
        key = a.name
        if key not in seen or a.evidence_tier > seen[key].evidence_tier:
            seen[key] = a

    # Group by recommendation
    adjusts = [a for a in seen.values() if a.recommendation == "adjust"]
    flags = [a for a in seen.values() if a.recommendation == "flag"]
    keeps = [a for a in seen.values() if a.recommendation == "keep"]

    def fmt_ci(a):
        if a.ci_lower == 0 and a.ci_upper == 0:
            return "—"
        return f"[{a.ci_lower:.2f}, {a.ci_upper:.2f}]"

    def audit_row(a):
        return [
            a.name,
            tier_labels.get(a.evidence_tier, "?"),
            str(a.current_value),
            str(a.recommended_value),
            fmt_ci(a),
            a.sample_size if a.sample_size > 0 else "—",
            a.recommendation.upper(),
        ]

    widths = [34, 5, 16, 14, 20, 7, 8]

    if adjusts:
        section("ADJUST — Data suggests different value")
        tbl(
            ["Parameter", "Tier", "Current", "Recommended", "95% CI", "N", "Verdict"],
            [audit_row(a) for a in sorted(adjusts, key=lambda x: x.name)],
            widths,
        )

    if flags:
        section("FLAG — No data available, cannot validate")
        tbl(
            ["Parameter", "Tier", "Current", "Recommended", "95% CI", "N", "Verdict"],
            [audit_row(a) for a in sorted(flags, key=lambda x: x.name)],
            widths,
        )

    if keeps:
        section("KEEP — Current value within acceptable range")
        tbl(
            ["Parameter", "Tier", "Current", "Recommended", "95% CI", "N", "Verdict"],
            [audit_row(a) for a in sorted(keeps, key=lambda x: x.name)],
            widths,
        )

    # Summary stats
    print(f"\n  Total parameters audited: {len(seen)}")
    print(f"    ADJUST: {len(adjusts)}")
    print(f"    FLAG:   {len(flags)}")
    print(f"    KEEP:   {len(keeps)}")

    if not HAS_SCIPY:
        print("\n  NOTE: scipy not installed. KS goodness-of-fit tests were SKIPPED.")
        print("  Install with: pip install scipy numpy")


# ── Main ─────────────────────────────────────────────────────

ANALYSES = {
    "distribution": ("Analysis 1: Distribution Fitting", analysis_1_distribution_fitting),
    "confidence": ("Analysis 2: Optimal Confidence Multipliers", analysis_2_confidence_multipliers),
    "review": ("Analysis 3: Review Time Regression", analysis_3_review_regression),
    "tasktype": ("Analysis 4: Task Type Multipliers", analysis_4_task_type_multipliers),
    "fixratio": ("Analysis 5: Human Fix Ratio Proxy", analysis_5_fix_ratio),
    "rounds": ("Analysis 6: Base Rounds Calibration", analysis_6_base_rounds),
    "sensitivity": ("Analysis 7: Sensitivity Analysis", analysis_7_sensitivity),
    "effectiveness": ("Analysis 8: Agent Effectiveness (METR)", analysis_8_agent_effectiveness),
    "tokens": ("Analysis 9: Token Consumption", analysis_9_token_consumption),
    "outratio": ("Analysis 10: Output Token Ratio", analysis_10_output_ratio),
    "cost": ("Analysis 11: Cost Model Validation", analysis_11_cost_model),
}


def main():
    parser = argparse.ArgumentParser(
        description="Deep statistical validation of formula parameters."
    )
    parser.add_argument(
        "--analysis",
        choices=list(ANALYSES.keys()) + ["all"],
        default="all",
        help="Run a specific analysis or all (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available analyses and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("\nAvailable analyses:")
        for key, (desc, _) in ANALYSES.items():
            print(f"  {key:<14} {desc}")
        return

    print("\n" + "=" * 80)
    print("  PROGRESSIVE ESTIMATION — DEEP PARAMETER VALIDATION")
    print(f"  Bootstrap: n={BOOTSTRAP_N}, seed={SEED}")
    print(f"  scipy: {'available' if HAS_SCIPY else 'NOT available (KS tests skipped)'}")
    print("=" * 80)

    all_audits = []

    if args.analysis == "all":
        for key, (desc, fn) in ANALYSES.items():
            audits = fn()
            all_audits.extend(audits)
    else:
        desc, fn = ANALYSES[args.analysis]
        audits = fn()
        all_audits.extend(audits)

    if all_audits:
        print_audit_card(all_audits)


if __name__ == "__main__":
    main()
