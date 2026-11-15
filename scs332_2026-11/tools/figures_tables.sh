#!/bin/zsh
# Figures and RST tables for the SCS 3.3.2 refresh, from an assembly made by assemble.py.
# Same commands as September's finalize_all.sh (site figures), with cpo3 added to the
# exclusions (Brendan 2026-11-14: no cpo3 on the SCS docs pages), no records figures, and the
# infeasibility plot rebuilt for harness #114.
# Usage: figures_tables.sh WORK_DIR    (writes WORK_DIR/fig)
# QTQP, qpo3 and cpo3 are not part of the refresh (Brendan, 2026-11-14); the exclusions stay as a guard.
set -e
setopt pipefail
W=${1:A}
V=$W/verified
H=$HOME/git/sb-refresh
PY=$HOME/git/solver_benchmarks/.venv-bench/bin/python
T=$HOME/scs33_tools/refresh_332/tools
FIG=$H/tools/make_figures.py
IPM=(--use-run clarabel=1e-6 --use-run sdp:clarabel=1e-8 --use-run piqp=1e-6 --use-run highs=1e-6 --use-run sdpa=1e-6 --use-run cvxopt=1e-6 --use-run qpo3=1e-8)
FO4=(--use-run pdlp=1e-5 --use-run proxqp=1e-5)
FO5=(--use-run pdlp=1e-6 --use-run proxqp=1e-6)
NOQ=(--exclude-solver qtqp_mkl --exclude-solver qtqp_cudss --exclude-solver qpo3 --exclude-solver cpo3)
export PYTHONPATH=$H
O=$W/fig
rm -rf $O; mkdir -p $O
cd $H

# run make_figures into DIR, then copy its summary to DIR/geomean_summary_NAME.csv after
# checking that every row is at tolerance TAG (a failed run must not leave the previous
# run's summary behind under the next name)
fig() {
  local dir=$1 name=$2 tag=$3; shift 3
  rm -f $dir/geomean_summary.csv
  $PY $FIG $dir "$@" | { grep -v "^/" || true; }
  $PY -c "import pandas as pd, sys; t = pd.read_csv('$dir/geomean_summary.csv'); bad = t[t.tol.astype(float) != float('$tag')]; sys.exit(f'tolerance mismatch in $name: {sorted(set(bad.tol))}' if len(t) == 0 or len(bad) else 0)"
  cp $dir/geomean_summary.csv $dir/geomean_summary_$name.csv
}

fig $O 1e-4 1e-4 qp=$V/qp_1e-4 lp=$V/lp_1e-4 sdp=$V/sdp_1e-4 lpbig=$V/lpbig_1e-4 --tol-tag 1e-4 $IPM $FO4 $NOQ --grid $O/landing_grid.png
fig $O 1e-5 1e-5 qp=$V/qp_1e-5 lp=$V/lp_1e-5 lpbig=$V/lpbig_1e-5 --tol-tag 1e-5 $IPM $FO5 $NOQ --grid $O/landing_grid_1e-5.png
fig $O 1e-6 1e-6 qp=$V/qp_1e-6 lp=$V/lp_1e-6 sdp=$V/sdp_1e-6 --tol-tag 1e-6 $IPM $NOQ

# Infeasibility plot (Netlib infeasible LPs): a verified certificate, or a correct status
# from a status-only solver, counts as a solve (rst_infeas.classify), as on the page since
# September. The rows are rewritten as optimal / time_limit and marked as expecting an
# optimum, so that both halves of the figure (bars: outcomes.success_mask; profile:
# status == optimal) apply that one rule; harness #114 would otherwise score them by
# certificate status, which the classification has already done.
$PY - $W <<'PYEOF'
import json, os, shutil, sys
W = sys.argv[1]
src = f"{W}/merged/infeas/results.jsonl"
sys.argv = ["x", src]
code = open(os.path.expanduser("~/scs33_tools/refresh_332/tools/rst_infeas.py")).read().split("# rows shown on the page")[0]
exec(code)
out = f"{W}/infeas_plot"
if os.path.exists(out):
    shutil.rmtree(out)
os.makedirs(out)
with open(f"{out}/results.jsonl", "w") as f:
    for r in rows:
        if r["dataset"] != "netlib_infeasible":
            continue
        c = classify(r); r = dict(r)
        r["status"] = "optimal" if c in ("certified", "status") else "time_limit"
        r["metadata"] = {**(r.get("metadata") or {}), "expected_status": "optimal"}
        f.write(json.dumps(r) + "\n")
shutil.copy(f"{W}/merged/infeas/manifest.json", f"{out}/manifest.json")
PYEOF
fig $O infeas 1e-8 infeas=$W/infeas_plot --tol-tag 1e-8 --use-run pdlp=1e-5 --exclude-solver highs --exclude-solver piqp --exclude-solver cuopt --exclude-solver pdlp_cert4 --exclude-solver qpo3_nopresolve $NOQ
# the docs reference it as infeas_pair.png
cp $O/infeas_1e-8_pair.png $O/infeas_pair.png
cp $O/geomean_summary_1e-6.csv $O/geomean_summary.csv

# tables
$PY $T/rst_tables.py $O > $O/tables.rst
$PY $T/rst_table_lpbig.py $O/geomean_summary_1e-4.csv > $O/table_lpbig.rst
VERIFIED=$V $PY $T/rst_accuracy.py > $O/table_accuracy.rst
$PY $T/rst_table_sens.py $O > $O/table_sens.rst
$PY $T/rst_infeas.py $W/merged/infeas/results.jsonl > $O/table_infeas.rst
echo FIGURES-TABLES-DONE
