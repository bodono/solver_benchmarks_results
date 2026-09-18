#!/bin/zsh
# Complete assembly: fetch every shard of every campaign, merge per family, verify at all
# thresholds, render figures (matched runs), tables, copy into the SCS docs, build docs.
set -e
SP=/Users/bodonoghue/scs33_tools
cd ~/git/solver_benchmarks
export PYTHONPATH=$HOME/git/sb-derive   # hardened kkt-verify (PR #88)
FIG=$HOME/git/sb-tooling/tools/make_figures.py  # penalty, profiles, pairs (PR #90)
IPM='--use-run clarabel=1e-6 --use-run sdp:clarabel=1e-8 --use-run piqp=1e-6 --use-run highs=1e-6 --use-run sdpa=1e-6 --use-run cvxopt=1e-6 --use-run qpo3=1e-8'
FO4='--use-run pdlp=1e-5 --use-run proxqp=1e-5'
FO5='--use-run pdlp=1e-6 --use-run proxqp=1e-6'
NOQ='--exclude-solver qtqp_mkl --exclude-solver qtqp_cudss --exclude-solver qpo3'  # QTQP is for the record only, not the SCS site
# 1. fetch: campaign name -> spec files
.venv-bench/bin/python - <<'PY'
import json, subprocess, os
specs = {"scs33": ["campaign/scs33/campaign.json"], "scs33big": ["campaign/scs33big/campaign.json", "campaign/scs33big_cl6/campaign.json", "campaign/scs33big_cl6b/campaign.json"],
         "scs33t5": ["campaign/scs33t5/campaign.json", "campaign/scs33t5all/campaign.json"], "scs33cl8": ["campaign/scs33cl8/campaign.json"], "scs33cltry": ["campaign/scs33cltry/campaign.json"], "scs33cltry2": ["campaign/scs33cltry2/campaign.json"],
         "scs33fix": ["campaign/scs33sdpfix/campaign.json", "campaign/scs33big6/campaign.json", "campaign/scs33miss4/campaign.json"],
         "scs33qtqp": ["campaign/scs33qtqp/campaign.json", "campaign/scs33qtqp8/campaign.json"], "scs33infeas": ["campaign/scs33infeas/campaign.json", "campaign/scs33infeas2/campaign.json", "campaign/scs33infeas5/campaign.json", "campaign/scs33infeas6/campaign.json"], "scs33qpo3": ["campaign/scs33qpo3/campaign.json", "campaign/scs33qpo3inf/campaign.json"]}
n = 0
for camp, files in specs.items():
    for f in files:
        for s in json.load(open(f)):
            name = s["name"]
            if name.startswith("lp_mittelmann_") or (camp == "scs33t5" and "sdp_" in name): continue
            d = f"results/{'scs33big' if name.startswith('lpbig') else 'scs33'}_shards/{name}"; os.makedirs(d, exist_ok=True)
            for fn in ("results.jsonl", "manifest.json"):
                r = subprocess.run([".venv-bench/bin/modal", "volume", "get", "scs-bench-results", f"{camp}/{name}/{fn}", f"{d}/{fn}", "--force"], capture_output=True, text=True)
            n += 1
print("fetched", n, "shards")
# drop the corrupt-archive worker_error rows for maxG55/maxG60 from the original SDPLIB shards
import glob
for f in glob.glob("results/scs33_shards/sdp_sdplib_*/results.jsonl"):
    if f.endswith("_fix/results.jsonl"): continue
    rows = [json.loads(l) for l in open(f) if l.strip()]
    keep = [r for r in rows if not (r["problem"] in ("maxG55", "maxG60", "thetaG51") and r["status"] == "worker_error")]
    if len(keep) != len(rows):
        with open(f, "w") as fh:
            for r in keep: fh.write(json.dumps(r) + "\n")
PY
# 2. merge + verify
for fam in qp lp sdp; do .venv-bench/bin/python -m solver_benchmarks.cli merge results/scs33_${fam}_merged results/scs33_shards/${fam}_* --overwrite | tail -1; done
.venv-bench/bin/python -m solver_benchmarks.cli merge results/scs33big_lpbig_merged results/scs33big_shards/lpbig_* --overwrite | tail -1
.venv-bench/bin/python -m solver_benchmarks.cli merge results/scs33_infeas_merged results/scs33_shards/infeas_* --overwrite | tail -1
for fam in qp lp sdp; do
  for pair in "1e-4:1e-3" "1e-5:1e-4" "1e-6:1e-5"; do tag=${pair%%:*}; thr=${pair##*:}
    .venv-bench/bin/python -m solver_benchmarks.cli kkt-verify results/scs33_${fam}_merged --tol $thr --promote --output-dir results/scs33_${fam}_verified_${tag} --overwrite >/dev/null
  done
done
for pair in "1e-4:1e-3" "1e-5:1e-4"; do tag=${pair%%:*}; thr=${pair##*:}
  .venv-bench/bin/python -m solver_benchmarks.cli kkt-verify results/scs33big_lpbig_merged --tol $thr --promote --output-dir results/scs33big_lpbig_verified_${tag} --overwrite >/dev/null
done
echo "verified"
# 3. figures
rm -rf $SP/fig
PYTHONPATH=$HOME/git/sb-tooling .venv-bench/bin/python $FIG $SP/fig qp=results/scs33_qp_verified_1e-4 lp=results/scs33_lp_verified_1e-4 sdp=results/scs33_sdp_verified_1e-4 lpbig=results/scs33big_lpbig_verified_1e-4 --tol-tag 1e-4 ${=IPM} ${=FO4} ${=NOQ} --grid $SP/fig/landing_grid.png | grep -v "^/"
cp $SP/fig/geomean_summary.csv $SP/fig/geomean_summary_1e-4.csv
PYTHONPATH=$HOME/git/sb-tooling .venv-bench/bin/python $FIG $SP/fig qp=results/scs33_qp_verified_1e-5 lp=results/scs33_lp_verified_1e-5 lpbig=results/scs33big_lpbig_verified_1e-5 --tol-tag 1e-5 ${=IPM} ${=FO5} ${=NOQ} --grid $SP/fig/landing_grid_1e-5.png | grep -v "^/"
cp $SP/fig/geomean_summary.csv $SP/fig/geomean_summary_1e-5.csv
PYTHONPATH=$HOME/git/sb-tooling .venv-bench/bin/python $FIG $SP/fig qp=results/scs33_qp_verified_1e-6 lp=results/scs33_lp_verified_1e-6 sdp=results/scs33_sdp_verified_1e-6 --tol-tag 1e-6 ${=IPM} ${=NOQ} | grep -v "^/"
# records-only figures with QTQP included (both tolerances), not copied into the docs
rm -rf $SP/fig_records
PYTHONPATH=$HOME/git/sb-tooling .venv-bench/bin/python $FIG $SP/fig_records qp=results/scs33_qp_verified_1e-4 lp=results/scs33_lp_verified_1e-4 lpbig=results/scs33big_lpbig_verified_1e-4 --tol-tag 1e-4 ${=IPM} ${=FO4} --use-run qtqp_mkl=1e-8 --use-run qtqp_cudss=1e-8 | grep -v "^/"
cp $SP/fig_records/geomean_summary.csv $SP/fig_records/geomean_summary_1e-4.csv
PYTHONPATH=$HOME/git/sb-tooling .venv-bench/bin/python $FIG $SP/fig_records qp=results/scs33_qp_verified_1e-6 lp=results/scs33_lp_verified_1e-6 --tol-tag 1e-6 ${=IPM} | grep -v "^/"
cp $SP/fig_records/geomean_summary.csv $SP/fig_records/geomean_summary_1e-6.csv
cp $SP/fig/geomean_summary.csv $SP/fig/geomean_summary_1e-6.csv
# 4. tables
.venv-bench/bin/python $SP/rst_tables.py $SP/fig > $SP/fig/tables.rst
.venv-bench/bin/python $SP/rst_table_lpbig.py $SP/fig/geomean_summary_1e-4.csv > $SP/fig/table_lpbig.rst
.venv-bench/bin/python $SP/rst_accuracy.py > $SP/fig/table_accuracy.rst
.venv-bench/bin/python $SP/rst_table_sens.py > $SP/fig/table_sens.rst
.venv-bench/bin/python $SP/rst_infeas.py results/scs33_infeas_merged/results.jsonl > $SP/fig/table_infeas.rst
# 5. docs
cp $SP/fig/*.png ~/git/scs/docs/src/files/bench/
# keep only the figures the docs reference
for f in ~/git/scs/docs/src/files/bench/*.png; do grep -q "$(basename $f)" ~/git/scs/docs/src/index.rst ~/git/scs/docs/src/benchmarks/index.rst || rm "$f"; done
python3 - <<'PY'
import re
SP = "/Users/bodonoghue/scs33_tools"
p = "/Users/bodonoghue/git/scs/docs/src/benchmarks/index.rst"; s = open(p).read()
tables = open(f"{SP}/fig/tables.rst").read()
parts = [x for x in re.split(r"(?=\.\. list-table:: (?:QP|LP|SDP):)", tables) if x.strip()]
tab = {re.match(r"\.\. list-table:: (QP|LP|SDP):", x).group(1): x.strip() + "\n" for x in parts}
tab["LPBIG"] = open(f"{SP}/fig/table_lpbig.rst").read().strip() + "\n"
tab["ACC"] = open(f"{SP}/fig/table_accuracy.rst").read().strip() + "\n"
tab["SENS"] = open(f"{SP}/fig/table_sens.rst").read().strip() + "\n"
tab["INFEAS"] = open(f"{SP}/fig/table_infeas.rst").read().strip() + "\n"
for key, marker, head in (("QP","QPTABLE","QP:"),("LP","LPTABLE","LP:"),("SDP","SDPTABLE","SDP:"),("LPBIG","LPBIGTABLE","Mittelmann LP set:"),("ACC","ACCURACYTABLE","Achieved accuracy"),("SENS","SENSTABLE","Verified solves and shifted geometric mean time (s) at the 1e-4 and 1e-5"),("INFEAS","INFEASTABLE","Infeasibility detection, Netlib")):
    if marker in s:
        s = s.replace(marker, tab[key])
    else:
        s = re.sub(r"\.\. list-table:: " + re.escape(head) + r".*?(?=\n\n(?:\.\. _|[A-Z]|\*\*))", lambda m: tab[key].rstrip("\n"), s, count=1, flags=re.S)
open(p, "w").write(s); print("tables updated")
PY
cd ~/git/scs/docs/src && $HOME/scs33_tools/docsvenv/bin/sphinx-build -q -b html . $HOME/scs33_tools/docs_html 2>&1 | grep -iE "warning|error" | grep -ivE "Doxyfile|obsolete|doxygen -u|\.out' not found|unknown command|duplicate C" || true
echo FINALIZE-ALL-DONE
