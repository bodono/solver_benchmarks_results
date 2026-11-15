#!/bin/zsh
# Build solver_benchmarks_results/scs332_2026-11 from a final assembly (assemble2.py + figures_tables.sh).
# Same layout as scs33_2026-09. Does not commit or push.
# Usage: build_results_dir.sh WORK_DIR
set -e
setopt pipefail
W=${1:A}
H=$HOME/git/sb-refresh
PY=$HOME/git/solver_benchmarks/.venv-bench/bin/python
T=$HOME/scs33_tools/refresh_332
R=$HOME/git/solver_benchmarks_results/scs332_2026-11
[ -f $W/assembly_report.json ] && [ -d $W/fig ] || { echo "run assemble2.py and figures_tables.sh on $W first"; exit 1; }
mkdir -p $R/{merged,configs,figures/site,figures/all,tables,per_problem,tools}

# merged rows (the Mittelmann LPs as 'mittelmann', as in September)
for fam in qp lp sdp infeas; do mkdir -p $R/merged/$fam; cp $W/merged/$fam/results.jsonl $W/merged/$fam/manifest.json $R/merged/$fam/; done
mkdir -p $R/merged/mittelmann; cp $W/merged/lpbig/results.jsonl $W/merged/lpbig/manifest.json $R/merged/mittelmann/

# configs as run: the three campaigns' specs and the YAML of every used shard
for c in scs332m scs332g2 scs332c scs332c_fill; do
  mkdir -p $R/configs/$c
  cp $H/campaign/$c/campaign.json $R/configs/$c/
  $PY - $H $c $R/configs/$c <<'PYEOF'
import json, shutil, sys
from pathlib import Path
h, c, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
for s in json.loads((h / "campaign" / c / "campaign.json").read_text()):
    if c == "scs332m" and "_limit" in s["name"]:
        continue
    shutil.copy(h / s["config"], out / Path(s["config"]).name)
PYEOF
done

# site figures: the ten the SCS docs reference
for f in landing_grid landing_grid_1e-5 qp_1e-4_pair qp_1e-6_pair_largest lp_1e-4_pair lp_1e-6_pair_largest lpbig_1e-4_pair lpbig_1e-5_pair sdp_1e-4_pair infeas_pair; do
  cp $W/fig/$f.png $R/figures/site/
done

# solver-neutral figures with every solver (README), as September's tools/make_readme.py expects
O=$W/fig_all; rm -rf $O; mkdir -p $O
IPM=(--use-run clarabel=1e-6 --use-run sdp:clarabel=1e-8 --use-run piqp=1e-6 --use-run highs=1e-6 --use-run sdpa=1e-6 --use-run cvxopt=1e-6)
V=$W/verified
cd $H
export PYTHONPATH=$H
run() { local name=$1; shift; rm -f $O/geomean_summary.csv; $PY tools/make_figures.py $O "$@" --neutral | { grep -v "^/" || true; }; [ -s $O/geomean_summary.csv ]; cp $O/geomean_summary.csv $O/geomean_summary_$name.csv; }
run 1e-4 qp=$V/qp_1e-4 lp=$V/lp_1e-4 sdp=$V/sdp_1e-4 lpbig=$V/lpbig_1e-4 --tol-tag 1e-4 $IPM --use-run pdlp=1e-5 --use-run proxqp=1e-5 --grid $O/grid_1e-4.png
run 1e-5 qp=$V/qp_1e-5 lp=$V/lp_1e-5 lpbig=$V/lpbig_1e-5 --tol-tag 1e-5 $IPM --use-run pdlp=1e-6 --use-run proxqp=1e-6 --grid $O/grid_1e-5.png
run 1e-6 qp=$V/qp_1e-6 lp=$V/lp_1e-6 --tol-tag 1e-6 $IPM
run sdp_1e-6 sdp=$V/sdp_1e-6 --tol-tag 1e-6 $IPM
run infeas infeas=$W/infeas_plot --tol-tag 1e-8 --use-run pdlp=1e-5 --exclude-solver highs --exclude-solver piqp --exclude-solver cuopt --exclude-solver pdlp_cert4
cp $O/*pair*.png $O/grid_*.png $R/figures/all/
for t in 1e-4 1e-5 1e-6 sdp_1e-6 infeas; do cp $O/geomean_summary_$t.csv $R/tables/all_geomean_summary_$t.csv; done
# site tables
cp $W/fig/geomean_summary_*.csv $W/fig/*.rst $R/tables/

# per-problem CSVs (verified status and time per solver), as September's archive.sh made them
$PY - $W $R <<'PYEOF'
import sys, pandas as pd
W, R = sys.argv[1], sys.argv[2]
sets = {"qp": "verified/qp_1e-4", "lp": "verified/lp_1e-4", "sdp": "verified/sdp_1e-4", "mittelmann": "verified/lpbig_1e-4",
        "qp_1e-5": "verified/qp_1e-5", "lp_1e-5": "verified/lp_1e-5", "mittelmann_1e-5": "verified/lpbig_1e-5",
        "qp_1e-6": "verified/qp_1e-6", "lp_1e-6": "verified/lp_1e-6", "sdp_1e-6": "verified/sdp_1e-6", "infeasible": "merged/infeas"}
for name, path in sets.items():
    v = pd.read_json(f"{W}/{path}/results.jsonl", lines=True, dtype={"problem": str})
    m = pd.json_normalize(v["metadata"]); v = pd.concat([v.drop(columns=["metadata"]), m], axis=1)
    t = v.pivot_table(index=["dataset", "problem"], columns="solver_id", values="run_time_seconds", aggfunc="first").round(2)
    st = v.pivot_table(index=["dataset", "problem"], columns="solver_id", values="status", aggfunc="first")
    st.columns = [c + "_status" for c in st.columns]
    size = v.groupby(["dataset", "problem"])[[c for c in ("n", "m", "nnz_a", "nnz_p") if c in v.columns]].max()
    size.join(t).join(st).to_csv(f"{R}/per_problem/{name}.csv")
print("per-problem CSVs written")
PYEOF

# tools used
cp $T/assemble2.py $T/figures_tables.sh $T/make_spec.py $T/make_spec_controlled.py $T/make_relaunch_spec.py \
   $T/launch_controlled.sh $T/launch_g2.sh $T/tools/rst_*.py $T/results_repo/make_readme.py $T/results_repo/build_results_dir.sh $R/tools/
cp $W/assembly_report.json $R/tables/assembly_report.json

# README from the tables and figures
cd $R && $PY tools/make_readme.py | tail -1
echo "BUILT $R (MANIFEST.md is written by hand; not committed)"
