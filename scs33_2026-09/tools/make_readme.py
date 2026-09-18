"""Generate scs33_2026-09/README.md: plots plus headline tables for every solver and family.

Run from the campaign directory:  python tools/make_readme.py
Inputs: tables/records_geomean_summary_{1e-4,1e-6}.csv (QP, LP, Mittelmann, all solvers incl. QTQP),
tables/geomean_summary_{1e-4,1e-6}.csv (SDP), merged/infeas/results.jsonl (infeasibility detection).
"""
from __future__ import annotations

import collections
import json
import math
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent
FAMILIES = [
    ("qp", "Quadratic programs", "Maros-Meszaros (138) and QPLIB (19): 157 problems, 300 s limit", "records"),
    ("lp", "Linear programs", "Netlib (93), Kennington (16) and the 240 MIPLIB 2017 relaxations: 349 problems, 300 s limit", "records"),
    ("lpbig", "Large linear programs: the Mittelmann set", "37 problems, 1800 s limit, 64 GB containers", "records"),
    ("sdp", "Semidefinite programs", "SDPLIB (88 feasible) and the Mittelmann SDPs (6): 94 problems, 900 s limit", "site"),
]
FIG = {"qp": ("figures/records/qp_1e-4_pair.png", "figures/records/qp_1e-6_pair_largest.png"),
       "lp": ("figures/records/lp_1e-4_pair.png", "figures/records/lp_1e-6_pair_largest.png"),
       "lpbig": ("figures/records/lpbig_1e-4_pair.png", None),
       "sdp": ("figures/site/sdp_1e-4_pair.png", None)}
SCS = ("SCS (CPU, MKL Pardiso)", "SCS (GPU, cuDSS)")


def load(kind: str, tol: str) -> pd.DataFrame:
    name = f"tables/{'records_' if kind == 'records' else ''}geomean_summary_{tol}.csv"
    p = HERE / name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def cell(df: pd.DataFrame, family: str, subset: str, label: str) -> str:
    r = df[(df.family == family) & (df.subset == subset) & (df.label == label)]
    if r.empty:
        return "–"
    r = r.iloc[0]
    n = int(r.success_count + r.failure_count)
    return f"{int(r.success_count)}/{n} · {r.run_time_seconds:.1f} s"


def family_table(family: str, kind: str) -> str:
    d4, d6 = load(kind, "1e-4"), load(kind, "1e-6")
    labels = list(d4[(d4.family == family) & (d4.subset == "all")].sort_values("run_time_seconds").label)
    has6 = not d6.empty and (d6.family == family).any()
    head = ["Solver", "1e-4, all", "1e-4, largest quartile"] + (["1e-6, all", "1e-6, largest quartile"] if has6 else [])
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for lab in labels:
        name = f"**{lab}**" if lab in SCS else lab
        row = [name, cell(d4, family, "all", lab), cell(d4, family, "largest", lab)]
        if has6:
            row += [cell(d6, family, "all", lab), cell(d6, family, "largest", lab)]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


# ---- infeasibility detection (same classification as the site's table, QTQP included) ----
TOL = 1e-3
LABELS = {"scs_cpu": "SCS (CPU, MKL Pardiso)", "scs_cudss": "SCS (GPU, cuDSS)", "cuopt": "cuOpt (GPU)", "osqp": "OSQP",
          "clarabel": "Clarabel", "piqp": "PIQP", "highs": "HiGHS", "pdlp": "PDLP (OR-Tools)",
          "pdlp_cert4": "PDLP (OR-Tools), certificate tolerance 1e-4", "cvxopt": "CVXOPT", "sdpa": "SDPA",
          "qtqp_mkl": "QTQP (CPU, MKL Pardiso)", "qtqp_cudss": "QTQP (GPU, cuDSS)"}
ORDER = ["scs_cpu", "scs_cudss", "clarabel", "qtqp_mkl", "qtqp_cudss", "piqp", "highs", "osqp", "pdlp", "pdlp_cert4", "cuopt", "cvxopt", "sdpa"]
SHOW = {"scs_cpu_1e-4", "scs_cpu_1e-8", "scs_cudss_1e-8", "clarabel_1e-8", "osqp_1e-8", "pdlp_1e-5", "cuopt_1e-4",
        "highs_1e-6", "piqp_1e-6", "qtqp_mkl_1e-8", "qtqp_cudss_1e-8"}
NOTE = {"scs_cpu_1e-8", "scs_cudss_1e-8", "clarabel_1e-8"}


def expected(r):
    if r["dataset"] == "netlib_infeasible":
        return "primal_infeasible"
    return "dual_infeasible" if r["problem"].startswith("infd") else "primal_infeasible"


def cert_ok(k):
    return bool(k.get("valid")) and all((v is not None and math.isfinite(v) and v <= TOL)
                                        for f, v in k.items() if f.endswith("_rel") or f.endswith("cone_res"))


def classify(r, rows):
    st, k = r["status"], (r.get("kkt") or {})
    if st.startswith(("primal_infeasible", "dual_infeasible", "primal_or_dual")):
        if "valid" not in k:
            return "status"
        if cert_ok(k):
            return "certified"
        direction = "primal_infeasible" if st.startswith("primal") else "dual_infeasible"
        proven = {expected(r)} | {("primal_infeasible" if x["status"].startswith("primal") else "dual_infeasible")
                                  for x in rows if x["problem"] == r["problem"] and x["dataset"] == r["dataset"]
                                  and "valid" in (x.get("kkt") or {}) and cert_ok(x["kkt"])
                                  and x["status"].startswith(("primal_infeasible", "dual_infeasible"))}
        return "unverified" if direction in proven else "wrong"
    if st.startswith("optimal"):
        core = [k.get(f) for f in ("primal_res_rel", "dual_res_rel", "duality_gap_rel")]
        if all(v is not None and v <= TOL for v in core):
            return "near_feasible"
        return "none" if st == "optimal_inaccurate" else "wrong"
    return "none"


def infeas_table(dataset: str) -> str:
    rows = [json.loads(line) for line in open(HERE / "merged/infeas/results.jsonl")]
    sub = [r for r in rows if r["dataset"] == dataset and (dataset != "netlib_infeasible" or r["solver_id"] in SHOW)]
    n = len({r["problem"] for r in sub})
    per: dict = collections.defaultdict(collections.Counter)
    times: dict = collections.defaultdict(list)
    for r in sub:
        c = classify(r, rows)
        per[r["solver_id"]][c] += 1
        if c in ("certified", "status"):
            times[r["solver_id"]].append(r.get("run_time_seconds") or 0.0)

    def label(sid):
        base, tol = sid.rsplit("_", 1)
        note = " (infeasibility tolerance 1e-4)" if sid in NOTE else ""
        return LABELS.get(base, base) + (f", {tol}" if dataset == "netlib_infeasible" else "") + note

    head = ["Solver", "certified", "status only", "unverified", "near-feasible", "wrong", "no answer", "geomean time"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for sid in sorted(per, key=lambda s: (ORDER.index(s.rsplit("_", 1)[0]) if s.rsplit("_", 1)[0] in ORDER else 99, s)):
        c = per[sid]
        c["none"] += n - sum(c.values())
        t = times[sid]
        gm = (math.exp(sum(math.log(x + 10.0) for x in t) / len(t)) - 10.0) if t else float("nan")
        name = f"**{label(sid)}**" if sid.startswith("scs_") else label(sid)
        lines.append("| " + " | ".join([name, str(c["certified"]), str(c["status"]), str(c["unverified"]),
                                          str(c["near_feasible"]), str(c["wrong"]), str(c["none"]),
                                          "–" if not t else f"{gm:.2f} s"]) + " |")
    return f"{n} problems.\n\n" + "\n".join(lines)


def main() -> None:
    out = ["# SCS 3.3 benchmark campaign, September 2026", "",
           "SCS 3.3.1 against Clarabel, PIQP, OSQP, ProxQP, HiGHS, PDLP (OR-Tools), NVIDIA cuOpt, CVXOPT, SDPA and QTQP on "
           "standard QP, LP, SDP and infeasible test sets, run on Modal in identical containers (A100-80GB for the GPU "
           "backends). Every solve is re-verified from the problem data at ten times the plot's target tolerance, so a "
           "\"solve\" below means a verified solution, whatever the solver reported; failures are charged three times the "
           "time limit in the shifted geometric means (shift 10 s). Interior-point solvers are shown from their 1e-6 runs "
           "(Clarabel 1e-8 on SDP, QTQP 1e-8 everywhere) and PDLP and ProxQP from their 1e-5 runs, matched by achieved "
           "accuracy; see [MANIFEST.md](MANIFEST.md) for versions, hardware and the exact rules, and "
           "[the SCS benchmarks page](https://www.cvxgrp.org/scs/benchmarks/) for the published subset (without QTQP).", "",
           "Table cells read *verified solves / problems · shifted geometric mean time*. Raw rows for every solver, "
           "tolerance and problem are in [`merged/`](merged/).", "",
           "## Headline", "",
           "Largest quarter of the QP and LP sets and the Mittelmann LP set, at 1e-4:", "",
           "![headline](figures/records/grid_with_qtqp.png)", ""]
    for fam, title, desc, kind in FAMILIES:
        out += [f"## {title}", "", desc + ".", ""]
        f4, f6 = FIG[fam]
        out += [f"![{fam} 1e-4]({f4})", ""]
        out += [family_table(fam, kind), ""]
        if f6:
            out += [f"Largest quartile at 1e-6:", "", f"![{fam} 1e-6 largest]({f6})", ""]
    out += ["## Infeasible and unbounded problems", "",
            "Netlib's 29 infeasible LPs (two of them also dual infeasible) and SDPLIB's four infeasible SDPs (two primal "
            "infeasible, two unbounded). SCS, Clarabel, OSQP, PDLP, CVXOPT and QTQP return a certificate (a Farkas ray), "
            "checked from the problem data at the 1e-3 threshold; HiGHS, PIQP, cuOpt and SDPA report a status only. A "
            "verified certificate of either kind counts as correct; \"near-feasible\" is an optimal claim whose residuals "
            "pass the check (the instance is infeasible by less than the tolerance). Each solver is shown from the run in "
            "which it certified the most; the plot uses the same rule.", "",
            "![infeasibility](figures/records/infeas_1e-8_pair_with_qtqp.png)", "",
            "### Netlib infeasible LPs", "", infeas_table("netlib_infeasible"), "",
            "### SDPLIB infeasible SDPs", "", infeas_table("sdplib_infeasible"), "",
            "## Sensitivity", "",
            "The same headline rows with every first-order solver re-run at a 1e-5 target (interior-point rows unchanged):", "",
            "![1e-5](figures/site/landing_grid_1e-5.png)", ""]
    (HERE / "README.md").write_text("\n".join(out))
    print("wrote", HERE / "README.md")


if __name__ == "__main__":
    main()
