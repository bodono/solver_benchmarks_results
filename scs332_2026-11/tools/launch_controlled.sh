#!/bin/bash
# The controlled-hardware completion of the SCS 3.3.2 refresh (make_spec_controlled.py):
# CPU kinds on AMD Zen 3 Milan only, GPU kinds on the A100 80GB PCIe with an Intel 6/106 host.
# SPEC defaults to campaign/scs332_controlled/campaign.json (scs332g + scs332c); a spec that
# also lists the unfinished scs332m shards runs everything in one orchestrator.
# Usage: launch_controlled.sh BUDGET_USD   (spend counts from $0 for this orchestrator)
set -u
BUDGET=${1:?budget in USD}
cd /Users/bodonoghue/git/sb-refresh || exit 1
export SCS_PYTHON_REF=91df3fcd59757ba65e416cdf820880b4026415d7   # bodono/scs-python#263: SCS core 0e7b36ae (3.3.2)
export CPO3_REPO=/nonexistent
L=/Users/bodonoghue/scs33_tools/refresh_332/logs
LOG=$L/campaign_controlled_$(date +%Y%m%d_%H%M).log
rm -f $L/DONE
echo "launch $(date) budget=$BUDGET head=$(git rev-parse --short HEAD) dirty=$(git status --porcelain tools | wc -l)" | tee "$LOG"
caffeinate -dims /Users/bodonoghue/git/solver_benchmarks/.venv-bench/bin/modal run tools/bench_modal.py \
  --campaign scs332 --spec "${SPEC:-campaign/scs332_controlled/campaign.json}" \
  --require-cpu 25/1 --require-gpu "NVIDIA A100-SXM4-80GB|25/1" --budget-usd "$BUDGET" 2>&1 | tee -a "$LOG"
echo "EXIT=${PIPESTATUS[0]} $(date)" | tee -a "$LOG"
echo "$LOG" > $L/DONE
