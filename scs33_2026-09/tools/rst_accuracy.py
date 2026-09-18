"""RST table of achieved accuracy for the runs shown in the 1e-4 plots: median and 90th
percentile of the largest relative KKT residual over each solver's own optimal returns."""
import pandas as pd, numpy as np
LABELS = {"scs_cpu": "SCS (CPU)", "scs_cudss": "SCS (GPU, cuDSS)", "osqp": "OSQP", "pdlp": "PDLP (OR-Tools)", "cuopt": "cuOpt (GPU)",
          "proxqp": "ProxQP", "clarabel": "Clarabel", "piqp": "PIQP", "highs": "HiGHS", "sdpa": "SDPA", "cvxopt": "CVXOPT"}
SHOWN = [("scs_cpu", "1e-4"), ("scs_cudss", "1e-4"), ("osqp", "1e-4"), ("pdlp", "1e-5"), ("cuopt", "1e-4"), ("proxqp", "1e-5"),
         ("clarabel", "1e-6"), ("piqp", "1e-6"), ("highs", "1e-6"), ("sdpa", "1e-6"), ("cvxopt", "1e-6")]
# Verified rows at the headline check (1e-3): the solves that count in the 1e-4 plots.
FAMS = [("qp", "results/scs33_qp_verified_1e-4/results.jsonl", {"mpc"}, "QP"), ("lp", "results/scs33_lp_verified_1e-4/results.jsonl", {"mittelmann"}, "LP"),
        ("lpbig", "results/scs33big_lpbig_verified_1e-4/results.jsonl", set(), "Mittelmann"), ("sdp", "results/scs33_sdp_verified_1e-4/results.jsonl", set(), "SDP")]
V1 = {"n9-3", "neos-3754224-navua", "neos-5075914-elvire", "rococoC11-011100", "toll-like"}
def worst(k): return max(k.get("primal_res_rel", np.nan), k.get("dual_res_rel", np.nan), k.get("duality_gap_rel", np.nan))
stats = {}
for fam, path, drop, _ in FAMS:
    m = pd.read_json(path, lines=True, dtype={"problem": str}); m = m[~m.dataset.isin(drop) & ~m.problem.isin(V1)]; m = m[m.status == "optimal"].copy()
    m["w"] = m["kkt"].apply(lambda k: worst(k) if isinstance(k, dict) and "primal_res_rel" in k else np.nan)
    for sid, g in m.groupby("solver_id"):
        w = g["w"].dropna()
        if len(w): stats[(sid, fam)] = (w.median(), w.quantile(0.9))
def fmt(x): return f"{x:.0e}".replace("e-0", "e-").replace("e+0", "e+") if pd.notna(x) else "--"
print(".. list-table:: Achieved accuracy of the runs shown in the headline plots: median and 90th percentile of the largest relative KKT residual over each solver's verified solves (returns that fail the check are excluded for every solver)")
print("   :header-rows: 2\n   :widths: 20 10 11 11 11 11 11 11 11 11\n")
print("   * - Solver\n     - run\n     - QP\n     -\n     - LP\n     -\n     - Mittelmann\n     -\n     - SDP\n     -")
print("   * -\n     -\n     - median\n     - 90th\n     - median\n     - 90th\n     - median\n     - 90th\n     - median\n     - 90th")
for base, tag in SHOWN:
    cells = [LABELS[base], tag]
    any_ = False
    for fam, _, _, _ in FAMS:
        s = stats.get((f"{base}_{tag}", fam))
        cells += [fmt(s[0]) if s else "--", fmt(s[1]) if s else "--"]; any_ |= bool(s)
    if any_: print("   * - " + "\n     - ".join(cells))
