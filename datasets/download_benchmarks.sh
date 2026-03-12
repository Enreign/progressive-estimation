#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_DIR="$SCRIPT_DIR/benchmarks"
mkdir -p "$BENCH_DIR"

echo "=== Downloading benchmark datasets ==="
echo "Target: $BENCH_DIR"
echo ""

# 1. METR eval-analysis-public (228 tasks with human duration + agent scores)
echo "[1/4] METR Time Horizons..."
if [ ! -d "$BENCH_DIR/metr" ]; then
    git clone --depth 1 https://github.com/METR/eval-analysis-public.git "$BENCH_DIR/metr"
    RUNS_FILE="$BENCH_DIR/metr/reports/time-horizon-1-1/data/raw/runs.jsonl"
    if [ -f "$RUNS_FILE" ]; then
        echo "  Done: $(wc -l < "$RUNS_FILE" | tr -d ' ') runs"
    else
        echo "  WARNING: runs.jsonl not found at expected path"
        echo "  Check: ls $BENCH_DIR/metr/reports/"
    fi
else
    echo "  Already exists, skipping"
fi
echo ""

# 2. OpenHands SWE-bench trajectories (sample from 67k)
echo "[2/4] OpenHands trajectories (sample)..."
if [ ! -f "$BENCH_DIR/openhands-sample.csv" ]; then
    echo "  Downloading parquet and converting to CSV..."
    echo "  Requires: pip install pandas pyarrow"
    python3 -c "
import pandas as pd
import sys
url = 'https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet'
# Read only metadata columns (skip huge trajectory column)
cols = ['instance_id', 'repo', 'exit_status', 'resolved']
print('  Downloading metadata columns (skipping trajectories)...')
df = pd.read_parquet(url, columns=cols)
# Take stratified sample: up to 500 per resolved status
# Stratified sample: 500 resolved + 500 unresolved
resolved = df[df['resolved'] == 1].sample(n=min(500, (df['resolved'] == 1).sum()), random_state=42)
unresolved = df[df['resolved'] == 0].sample(n=min(500, (df['resolved'] == 0).sum()), random_state=42)
sample = pd.concat([resolved, unresolved])
outpath = '$BENCH_DIR/openhands-sample.csv'
sample.to_csv(outpath, index=False)
print(f'  Saved {len(sample)} rows ({int(sample.resolved.sum())} resolved) to {outpath}')
" 2>&1 || echo "  WARNING: Failed. Install deps: pip install pandas pyarrow"
else
    echo "  Already exists, skipping"
fi
echo ""

# 3. Aider leaderboard data
echo "[3/4] Aider leaderboard..."
mkdir -p "$BENCH_DIR/aider"
for f in edit_leaderboard.yml polyglot_leaderboard.yml refactor_leaderboard.yml; do
    if [ ! -f "$BENCH_DIR/aider/$f" ]; then
        curl -sL -o "$BENCH_DIR/aider/$f" \
            "https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/_data/$f"
        echo "  Downloaded $f"
    else
        echo "  $f already exists, skipping"
    fi
done
echo ""

# 4. Bundled files check
echo "[4/4] Checking bundled files..."
for f in tokenomics.csv onprem-tokens.csv; do
    if [ -f "$BENCH_DIR/$f" ]; then
        echo "  $f present"
    else
        echo "  WARNING: $f missing (should be committed to repo)"
    fi
done

echo ""
echo "=== Download complete ==="
echo ""
echo "Run analyses:"
echo "  python3 tests/deep_validation.py --analysis effectiveness  # METR agent data"
echo "  python3 tests/deep_validation.py --analysis tokens         # Token consumption"
echo "  python3 tests/deep_validation.py --analysis cost           # Cost model"
echo "  python3 tests/deep_validation.py                           # All 11 analyses"
