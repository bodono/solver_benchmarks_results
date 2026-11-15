"""RST list-table for the Mittelmann (lpbig) family, 1e-4 only, from a geomean_summary.csv."""
import sys, pandas as pd
LABELS = {"scs_cpu": "SCS (CPU, MKL Pardiso)", "scs_cudss": "SCS (GPU, cuDSS)", "cuopt": "cuOpt (GPU)",
          "clarabel": "Clarabel", "piqp": "PIQP", "highs": "HiGHS", "pdlp": "PDLP (OR-Tools)"}
t = pd.read_csv(sys.argv[1]); t = t[(t.family == "lpbig") & (t.subset == "all")].sort_values("run_time_seconds")
n = int((t.success_count + t.failure_count).max())
print(f".. list-table:: Mittelmann LP set: verified solves out of {n} and shifted geometric mean time (s), tolerance 1e-4, 1800 s limit")
print("   :header-rows: 1\n   :widths: 40 20 20\n")
print("   * - Solver\n     - verified solves\n     - geometric mean (s)")
for _, r in t.iterrows():
    name = r.label if "label" in t.columns else LABELS.get(r.solver_id.rsplit('_',1)[0], r.solver_id)
    print(f"   * - {name}\n     - {int(r.success_count)}\n     - {r.run_time_seconds:.0f}")
