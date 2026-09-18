set -e
SP=$HOME/scs33_tools; cd ~/git/solver_benchmarks && R=results/scs33_campaign_2026-09; mkdir -p $R/figures_1e-5 $R/figures_records; cp -r results/scs33_shards/* $R/raw_shards/; cp -r results/scs33big_shards/* $R/raw_shards/; for d in results/scs33_*_merged results/scs33big_*_merged; do cp -r $d $R/merged/; done; for d in results/scs33_*_verified_* results/scs33big_*_verified_*; do cp -r $d $R/verified/; done; cp $SP/fig/*.png $R/figures/; cp $SP/fig_records/*.png $R/figures_records/ 2>/dev/null; cp $SP/fig/geomean_summary_*.csv $SP/fig/*.rst $SP/finalize_all.sh $SP/rst_*.py $SP/compare_tol.py $R/tables/; cp $SP/fig_records/geomean_summary_*.csv $R/figures_records/ 2>/dev/null; cp -r campaign/scs33* $R/campaign_configs/; cp /private/tmp/claude-501/-Users-bodonoghue-git/6aaba7c7-1dd3-45c8-9bab-7e3aaa50f769/scratchpad/modal/campaign_scs33*.log $R/modal_logs/ 2>/dev/null; cp $SP/finalize_all*.log $R/modal_logs/ 2>/dev/null; .venv-bench/bin/python - <<'EOF'
import pandas as pd
R = "results/scs33_campaign_2026-09"
for fam, path in (("qp","results/scs33_qp_verified_1e-4"),("lp","results/scs33_lp_verified_1e-4"),("sdp","results/scs33_sdp_verified_1e-4"),
                  ("qp_1e-5","results/scs33_qp_verified_1e-5"),("lp_1e-5","results/scs33_lp_verified_1e-5"),("mittelmann_1e-5","results/scs33big_lpbig_verified_1e-5"),
                  ("qp_1e-6","results/scs33_qp_verified_1e-6"),("lp_1e-6","results/scs33_lp_verified_1e-6"),("sdp_1e-6","results/scs33_sdp_verified_1e-6"),
                  ("mittelmann","results/scs33big_lpbig_verified_1e-4"),("infeasible","results/scs33_infeas_merged")):
    v = pd.read_json(path + "/results.jsonl", lines=True, dtype={"problem": str})
    m = pd.json_normalize(v["metadata"]); v = pd.concat([v.drop(columns=["metadata"]), m], axis=1)
    t = v.pivot_table(index=["dataset","problem"], columns="solver_id", values="run_time_seconds", aggfunc="first").round(2)
    st = v.pivot_table(index=["dataset","problem"], columns="solver_id", values="status", aggfunc="first"); st.columns = [c + "_status" for c in st.columns]
    size = v.groupby(["dataset","problem"])[[c for c in ("n","m","nnz_a","nnz_p") if c in v.columns]].max()
    size.join(t).join(st).to_csv(f"{R}/per_problem/{fam}.csv")
print("per-problem CSVs refreshed")
EOF
cd ~ && tar czf ~/scs33_benchmarks_2026-09.tar.gz -C ~/git/solver_benchmarks/results scs33_campaign_2026-09 && du -sh ~/git/solver_benchmarks/results/scs33_campaign_2026-09 ~/scs33_benchmarks_2026-09.tar.gz | awk '{print $1, $2}'