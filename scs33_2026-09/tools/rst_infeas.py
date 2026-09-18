"""RST tables for the infeasibility-detection family (Netlib infeasible LPs, SDPLIB infeasible SDPs)."""
import json, math, sys, collections
LABELS = {"scs_cpu": "SCS (CPU, MKL Pardiso)", "scs_cudss": "SCS (GPU, cuDSS)", "cuopt": "cuOpt (GPU)", "osqp": "OSQP",
          "clarabel": "Clarabel", "piqp": "PIQP", "highs": "HiGHS", "pdlp": "PDLP (OR-Tools)", "pdlp_cert4": "PDLP (OR-Tools), certificate tolerance 1e-4", "cvxopt": "CVXOPT", "sdpa": "SDPA"}
ORDER = ["scs_cpu", "scs_cudss", "clarabel", "piqp", "highs", "osqp", "pdlp", "pdlp_cert4", "cuopt", "cvxopt", "sdpa"]
TOL = 1e-3          # one threshold for everyone, the same as the 1e-4 plots (10x the target)

def tol_of(r):
    return TOL
SHIFT = 10.0
path = sys.argv[1] if len(sys.argv) > 1 else "results/scs33_infeas_merged/results.jsonl"
rows = [json.loads(l) for l in open(path)]

def expected(r):
    if r["dataset"] == "netlib_infeasible": return "primal_infeasible"
    return "dual_infeasible" if r["problem"].startswith("infd") else "primal_infeasible"

def cert_ok(k, TOL):
    return bool(k.get("valid")) and all((v is not None and math.isfinite(v) and v <= TOL)
                                        for f, v in k.items() if f.endswith("_rel") or f.endswith("cone_res"))

PROVEN: dict = {}   # problem -> directions proven by some verified certificate

def proven_directions(r):
    key = (r["dataset"], r["problem"])
    if key not in PROVEN:
        dirs = {expected(r)}
        for x in rows:
            if (x["dataset"], x["problem"]) != key: continue
            k = x.get("kkt") or {}
            if "valid" in k and cert_ok(k, TOL) and x["status"].startswith(("primal_infeasible", "dual_infeasible")):
                dirs.add("primal_infeasible" if x["status"].startswith("primal") else "dual_infeasible")
        PROVEN[key] = dirs
    return PROVEN[key]

def classify(r):
    """A verified certificate of either kind is a proof and counts as correct (two
    Netlib instances are both primal and dual infeasible). A certificate that fails
    the check is 'unverified' when its direction is proven (by the problem's known
    class or by another solver's verified certificate) and 'wrong' otherwise. A
    status-only solver is credited for any infeasibility status. An 'optimal' claim
    whose residuals pass the same check is a point within the tolerance of
    feasibility (near_feasible); an 'optimal' that fails is wrong, an
    'optimal_inaccurate' that fails is inconclusive (no answer)."""
    st, k, TOL = r["status"], (r.get("kkt") or {}), tol_of(r)
    if st.startswith(("primal_infeasible", "dual_infeasible", "primal_or_dual")):
        if "valid" not in k: return "status"
        if cert_ok(k, TOL): return "certified"
        direction = "primal_infeasible" if st.startswith("primal") else "dual_infeasible"
        return "unverified" if direction in proven_directions(r) else "wrong"
    if st.startswith("optimal"):
        core = [k.get(f) for f in ("primal_res_rel", "dual_res_rel", "duality_gap_rel")]
        if all(v is not None and v <= TOL for v in core): return "near_feasible"
        return "none" if st == "optimal_inaccurate" else "wrong"
    return "none"

# rows shown on the page: each solver at the plot's setting, plus SCS at the page setting
SHOW = {"netlib_infeasible": {"scs_cpu_1e-4", "scs_cpu_1e-8", "scs_cudss_1e-8", "clarabel_1e-8", "osqp_1e-8", "pdlp_1e-5",
                              "cuopt_1e-4", "highs_1e-6", "piqp_1e-6"}}
tables = collections.OrderedDict((("netlib_infeasible", "Netlib infeasible LPs"), ("sdplib_infeasible", "SDPLIB infeasible SDPs")))
for ds, title in tables.items():
    sub = [r for r in rows if r["dataset"] == ds and not r["solver_id"].startswith("qtqp") and (ds not in SHOW or r["solver_id"] in SHOW[ds])]
    if not sub: continue
    n = len({r["problem"] for r in sub})
    per = collections.defaultdict(lambda: collections.Counter())
    times = collections.defaultdict(list)
    for r in sub:
        base = r["solver_id"]; c = classify(r); per[base][c] += 1
        if c in ("certified", "status"): times[base].append(r.get("run_time_seconds") or 0.0)
    def label(sid):
        base, tol = sid.rsplit("_", 1)
        multi = ds == "netlib_infeasible" or len({x for x in per if x.rsplit("_", 1)[0] == base}) > 1
        note = " (infeasibility tolerance 1e-4)" if tol == "1e-8" and base.startswith(("scs_", "clarabel")) and ds == "netlib_infeasible" else ""
        return LABELS.get(base, base) + (f", {tol}" if multi else "") + note
    def order_key(sid):
        base, tol = sid.rsplit("_", 1)
        return (ORDER.index(base) if base in ORDER else 99, tol)
    print(f".. list-table:: Infeasibility detection, {title} ({n} problems): verified certificate / correct status without certificate / certificate failing the check / reported optimal with residuals within tolerance / wrong / no answer, and shifted geometric mean time (s) over certified and status answers")
    print("   :header-rows: 1\n   :widths: 24 11 11 11 11 11 11 12\n")
    print("   * - Solver\n     - certified\n     - status only\n     - unverified\n     - near-feasible\n     - wrong\n     - no answer\n     - gm time")
    for base in sorted(per, key=order_key):
        c = per[base]; missing = n - sum(c.values()); c["none"] += missing
        t = times[base]; gm = math.exp(sum(math.log(x + SHIFT) for x in t) / len(t)) - SHIFT if t else float("nan")
        cells = [label(base), str(c["certified"]), str(c["status"]), str(c["unverified"]), str(c["near_feasible"]), str(c["wrong"]), str(c["none"]), "--" if t == [] else f"{gm:.2f}"]
        print("   * - " + "\n     - ".join(cells))
    print()
