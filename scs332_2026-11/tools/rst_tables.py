"""Emit RST list-tables (verified solves, shifted geomean) from geomean_summary CSVs."""
import sys, pandas as pd
LABELS = {"scs_cpu": "SCS (CPU, MKL Pardiso)", "scs_cudss": "SCS (GPU, cuDSS)", "cuopt": "cuOpt (GPU)",
          "osqp": "OSQP", "clarabel": "Clarabel", "piqp": "PIQP", "proxqp": "ProxQP", "highs": "HiGHS",
          "pdlp": "PDLP (OR-Tools)", "cvxopt": "CVXOPT", "sdpa": "SDPA"}
fig = sys.argv[1]
for family, title in (("qp", "QP"), ("lp", "LP"), ("sdp", "SDP")):
    frames = {tol: pd.read_csv(f"{fig}/geomean_summary_{tol}.csv") for tol in ("1e-4", "1e-6")}
    rows = {}
    for tol, t in frames.items():
        t = t[t.family == family]
        for _, r in t.iterrows():
            base = r.solver_id.rsplit("_", 1)[0]
            rows.setdefault(base, {})[(tol, r.subset)] = (int(r.success_count), int(r.success_count + r.failure_count), r.run_time_seconds)
            if tol == "1e-4" and "label" in t.columns:
                LABELS[base] = r.label
    n_all = max(v[("1e-4", "all")][1] for v in rows.values() if ("1e-4", "all") in v)
    n_big = max(v[("1e-4", "largest")][1] for v in rows.values() if ("1e-4", "largest") in v)
    print(f".. list-table:: {title}: verified solves and shifted geometric mean time (s); all {n_all} problems / largest quartile ({n_big})")
    tols = ("1e-4",) if family == "sdp" else ("1e-4", "1e-6")   # the SDP page shows the 1e-4 plot only
    print("   :header-rows: 1\n   :widths: 26 12 12 12 12" + (" 12 12 12 12" if len(tols) == 2 else "") + "\n")
    print("   * - Solver\n     - solved 1e-4\n     - gm 1e-4\n     - solved 1e-4 (largest)\n     - gm 1e-4 (largest)" + ("\n     - solved 1e-6\n     - gm 1e-6\n     - solved 1e-6 (largest)\n     - gm 1e-6 (largest)" if len(tols) == 2 else ""))
    order = sorted(rows, key=lambda b: rows[b].get(("1e-4", "all"), (0, 0, 1e9))[2])
    for b in order:
        cells = [LABELS.get(b, b)]
        for tol in tols:
            for sub in ("all", "largest"):
                v = rows[b].get((tol, sub))
                if v is None:
                    cells += ["--", "--"]
                else:
                    cells += [f"{v[0]}", f"{v[2]:.1f}"]
        print("   * - " + "\n     - ".join(cells))
    print()
