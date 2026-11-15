#!/bin/bash
# SCS GPU re-run with the cuDSS fix (campaign scs332g2, Brendan 2026-11-14 ~22:30) plus the two
# Clarabel fill shards (campaign scs332c), on the controlled hardware: GPU kinds on the A100-SXM4-80GB
# with an AMD Zen 3 Milan host, CPU kinds on Milan only. One orchestrator at a time.
# Usage: launch_g2.sh BUDGET_USD SCS_PYTHON_COMMIT   (spend counts from $0 for this orchestrator)
set -u
BUDGET=${1:?budget in USD}
export SCS_PYTHON_REF=${2:?scs-python commit whose scs_source has the cuDSS fix}
cd /Users/bodonoghue/git/sb-refresh || exit 1
export CPO3_REPO=/nonexistent
L=/Users/bodonoghue/scs33_tools/refresh_332/logs
LOG=$L/campaign_g2_$(date +%Y%m%d_%H%M).log
rm -f $L/DONE
echo "launch $(date) budget=$BUDGET scs_python=$SCS_PYTHON_REF head=$(git rev-parse --short HEAD) dirty=$(git status --porcelain tools | wc -l)" | tee "$LOG"
caffeinate -dims /Users/bodonoghue/git/solver_benchmarks/.venv-bench/bin/modal run tools/bench_modal.py \
  --campaign scs332g2 --spec campaign/scs332g2_run/campaign.json \
  --require-cpu 25/1 --require-gpu "NVIDIA A100-SXM4-80GB|25/1" --budget-usd "$BUDGET" 2>&1 | tee -a "$LOG"
echo "EXIT=${PIPESTATUS[0]} $(date)" | tee -a "$LOG"
echo "$LOG" > $L/DONE
