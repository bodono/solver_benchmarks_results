"""SCS MKL (and any other solver with 1e-5 rows) at 1e-4 / 1e-5 / 1e-6: verified counts and shifted geomeans."""
import pandas as pd, numpy as np, glob, sys
SP = "/Users/bodonoghue/scs33_tools"
SOLVER = sys.argv[1] if len(sys.argv) > 1 else "scs_cpu"
def worst(k): return max(k.get("primal_res_rel", np.nan), k.get("dual_res_rel", np.nan), k.get("duality_gap_rel", np.nan))
PROM = {"optimal", "optimal_inaccurate", "max_iter_reached", "time_limit"}
def ok(df, thr):
    if df.empty: return pd.Series(False, index=df.index, dtype=bool)
    w = df["kkt"].apply(lambda k: worst(k) if isinstance(k, dict) and "primal_res_rel" in k else np.nan)
    return df.status.isin(PROM) & (w <= thr)
def sgm(t): return np.exp(np.log(t + 1).mean()) - 1
def load(f): 
    d = pd.read_json(f, lines=True, dtype={"problem": str}); d["problem"] = d["problem"].astype(str); return d
files = [f for f in glob.glob(f"{SP}/res_peek/*_{SOLVER}_1e-5.jsonl") if "sdp_" not in f and "lp_mittelmann_" not in f]
t5 = pd.concat([load(f) for f in files], ignore_index=True) if files else pd.DataFrame()
fams = {"qp": ("results/scs33_qp_merged/results.jsonl", {"maros_meszaros", "qplib"}),
        "lp": ("results/scs33_lp_merged/results.jsonl", {"netlib", "kennington", "miplib_relax"}),
        "lpbig": ("results/scs33big_lpbig_merged/results.jsonl", {"mittelmann0", "mittelmann1", "mittelmann2"})}
rows = []
for fam, (path, dsets) in fams.items():
    m = load(path); m = m[m.dataset.isin(dsets)].copy()
    x5 = t5[t5.dataset.isin(dsets)].copy() if not t5.empty else t5
    n = m.groupby(["dataset", "problem"]).ngroups
    meta = pd.json_normalize(m["metadata"]); meta.index = m.index
    m["sz"] = meta.get("nnz_a", pd.Series(0, index=m.index)).fillna(0) + meta.get("nnz_p", pd.Series(0, index=m.index)).fillna(0)
    big = m.groupby(["dataset", "problem"])["sz"].max(); cut = big.quantile(0.75); bigset = set(big[big >= cut].index)
    runs = [("1e-4", m[m.solver_id == f"{SOLVER}_1e-4"], 1e-3), ("1e-5", x5, 1e-4), ("1e-6", m[m.solver_id == f"{SOLVER}_1e-6"], 1e-5)]
    if SOLVER == "ipm":
        runs = [(f"{ipm}@{thr:.0e}", m[m.solver_id == f"{ipm}_1e-6"], thr) for ipm in ("clarabel", "piqp", "highs") for thr in (1e-3, 1e-4)]
    for sid, df, thr in runs:
        for sub, sel in (("all", None), ("largest", bigset)):
            mask = pd.Series(True, index=df.index) if sel is None else pd.Series([(a, b) in sel for a, b in zip(df.dataset, df.problem)], index=df.index, dtype=bool)
            d = df.loc[mask]; nn = n if sel is None else len(sel)
            if d.empty: rows.append((fam, sub, sid, nn, np.nan, np.nan)); continue
            o = ok(d, thr); tt = d.run_time_seconds.where(o, 1000.0).clip(lower=0.01)
            # missing problems count as failures
            missing = nn - d.groupby(["dataset", "problem"]).ngroups
            tt = pd.concat([tt, pd.Series([1000.0] * missing)])
            rows.append((fam, sub, sid, nn, int(o.sum()), round(sgm(tt), 1)))
t = pd.DataFrame(rows, columns=["family", "subset", "run", "of", "verified", "geomean"])
print(f"== {SOLVER}"); print(t.pivot_table(index=["family", "subset", "of"], columns="run", values=["verified", "geomean"]).to_string())
