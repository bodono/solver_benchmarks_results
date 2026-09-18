"""RST table: verified solves and shifted geomean at 1e-4 vs 1e-5 for the three landing rows."""
import pandas as pd
SP = "/Users/bodonoghue/scs33_tools"
a = pd.read_csv(f"{SP}/fig/geomean_summary_1e-4.csv"); b = pd.read_csv(f"{SP}/fig/geomean_summary_1e-5.csv")
rows = (("qp", "largest", "Maros-Meszaros and QPLIB QPs, largest quartile"), ("lp", "largest", "Kennington and MIPLIB-relaxation LPs, largest quartile"), ("lpbig", "all", "Mittelmann LP set"))
print(".. list-table:: Verified solves and shifted geometric mean time (s) at the 1e-4 and 1e-5 settings; interior-point solvers unchanged (shown from their tightest run in both)")
print("   :header-rows: 1\n   :widths: 30 24 12 12 12 12\n")
print("   * - Problem set\n     - Solver\n     - solved 1e-4\n     - time 1e-4\n     - solved 1e-5\n     - time 1e-5")
for fam, sub, name in rows:
    x = a[(a.family == fam) & (a.subset == sub)][["label", "success_count", "run_time_seconds"]]
    y = b[(b.family == fam) & (b.subset == sub)][["label", "success_count", "run_time_seconds"]]
    n = int((a[(a.family == fam) & (a.subset == sub)].success_count + a[(a.family == fam) & (a.subset == sub)].failure_count).max())
    t = x.merge(y, on="label", how="outer", suffixes=("_4", "_5")).sort_values("run_time_seconds_5")
    first = True
    for _, r in t.iterrows():
        cells = [f"{name} ({n})" if first else "", r.label,
                 f"{int(r.success_count_4)}" if pd.notna(r.success_count_4) else "--", f"{r.run_time_seconds_4:.0f}" if pd.notna(r.run_time_seconds_4) else "--",
                 f"{int(r.success_count_5)}" if pd.notna(r.success_count_5) else "--", f"{r.run_time_seconds_5:.0f}" if pd.notna(r.run_time_seconds_5) else "--"]
        first = False
        print("   * - " + "\n     - ".join(cells))
