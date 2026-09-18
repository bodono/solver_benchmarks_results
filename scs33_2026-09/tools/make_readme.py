"""Generate scs33_2026-09/README.md: solver-neutral plots and headline tables for every solver, family,
data set and tolerance.

Run from the campaign directory:  python tools/make_readme.py
Inputs: figures/all/ (rendered with `make_figures.py --neutral`), tables/all_geomean_summary_*.csv,
per_problem/*.csv (verified status and time per solver and problem), merged/infeas/results.jsonl.
"""
from __future__ import annotations

import collections
import csv
import json
import math
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent
SHIFT, FLOOR, PENALTY_FACTOR, GRACE = 10.0, 0.01, 3.0, 60.0
LIMIT = {"qp": 300.0, "lp": 300.0, "lpbig": 1800.0, "sdp": 900.0}
FAMILIES = [
    ("qp", "Quadratic programs", "Maros-Meszaros (138) and QPLIB continuous convex (19): 157 problems, 300 s limit.", "qp"),
    ("lp", "Linear programs", "Netlib (93), Kennington (16) and the 240 MIPLIB 2017 benchmark relaxations: 349 problems, 300 s limit.", "lp"),
    ("lpbig", "Large linear programs: the Mittelmann set", "Hans Mittelmann's LP benchmark set: 37 problems, 1800 s limit, 64 GB containers.", "mittelmann"),
    ("sdp", "Semidefinite programs", "SDPLIB (88 feasible instances) and the Mittelmann SDPs (6): 94 problems, 900 s limit. "
     "SCS cuDSS was run at 1e-4 only on this family.", "sdp"),
]
# the run each solver is shown from, per plot tolerance (matched by achieved accuracy, as on the SCS site;
# QTQP, an interior-point method, from its 1e-8 run everywhere)
RULE = {
    "1e-4": {"scs_cpu": "1e-4", "scs_cudss": "1e-4", "osqp": "1e-4", "cuopt": "1e-4", "pdlp": "1e-5", "proxqp": "1e-5",
             "clarabel": "1e-6", "piqp": "1e-6", "highs": "1e-6", "sdpa": "1e-6", "cvxopt": "1e-6",
             "qtqp_mkl": "1e-8", "qtqp_cudss": "1e-8"},
    "1e-6": {"scs_cpu": "1e-6", "scs_cudss": "1e-6", "osqp": "1e-6", "cuopt": "1e-6", "pdlp": "1e-6", "proxqp": "1e-6",
             "clarabel": "1e-6", "piqp": "1e-6", "highs": "1e-6", "sdpa": "1e-6", "cvxopt": "1e-6",
             "qtqp_mkl": "1e-8", "qtqp_cudss": "1e-8"},
}
RULE["1e-4"]["clarabel@sdp"] = "1e-8"
RULE["1e-6"]["clarabel@sdp"] = "1e-8"
LABELS = {"scs_cpu": "SCS (CPU, MKL Pardiso)", "scs_cudss": "SCS (GPU, cuDSS)", "cuopt": "cuOpt (GPU)", "osqp": "OSQP",
          "clarabel": "Clarabel", "piqp": "PIQP", "proxqp": "ProxQP", "highs": "HiGHS", "pdlp": "PDLP (OR-Tools)",
          "pdlp_cert4": "PDLP (OR-Tools), certificate tolerance 1e-4", "cvxopt": "CVXOPT", "sdpa": "SDPA",
          "qtqp_mkl": "QTQP (CPU, MKL Pardiso)", "qtqp_cudss": "QTQP (GPU, cuDSS)"}
DATASET_NAMES = {"maros_meszaros": "Maros-Meszaros", "qplib": "QPLIB", "netlib": "Netlib", "kennington": "Kennington",
                 "miplib_relax": "MIPLIB 2017 relaxations", "mittelmann0": "Mittelmann", "mittelmann1": "Mittelmann",
                 "mittelmann2": "Mittelmann", "sdplib": "SDPLIB", "mittelmann_sdp": "Mittelmann SDPs"}
DROP_DATASETS = {"qp": {"mpc"}, "lp": {"mittelmann"}}
DROP_PROBLEMS = {"lp": {("miplib_relax", n) for n in ("n9-3", "neos-3754224-navua", "neos-5075914-elvire", "rococoC11-011100", "toll-like")},
                 "sdp": {("sdplib", n) for n in ("infd1", "infd2", "infp1", "infp2")}}


def sgm(times: list[float], failures: int, limit: float) -> float:
    vals = [max(t, FLOOR) for t in times] + [PENALTY_FACTOR * limit] * failures
    return math.exp(sum(math.log(v + SHIFT) for v in vals) / len(vals)) - SHIFT if vals else float("nan")


# ---------- family tables from the figure script's summaries ----------
def summary(tol: str) -> pd.DataFrame:
    p = HERE / f"tables/all_geomean_summary_{tol}.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def cell(df: pd.DataFrame, family: str, subset: str, label: str) -> str:
    r = df[(df.family == family) & (df.subset == subset) & (df.label == label)]
    if r.empty:
        return "–"
    r = r.iloc[0]
    return f"{int(r.success_count)}/{int(r.success_count + r.failure_count)} · {r.run_time_seconds:.1f} s"


def family_table(family: str) -> str:
    frames = {t: summary(t) for t in ("1e-4", "1e-5", "1e-6")}
    if family == "sdp":
        frames["1e-6"] = summary("sdp_1e-6")
    frames = {t: d for t, d in frames.items() if not d.empty and (d.family == family).any()}
    d4 = frames["1e-4"]
    labels = list(d4[(d4.family == family) & (d4.subset == "all")].sort_values("run_time_seconds").label)
    head = ["Solver"] + [f"{t}, {sub}" for t in frames for sub in ("all", "largest quartile")]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for lab in labels:
        row = [lab] + [cell(frames[t], family, sub, lab) for t in frames for sub in ("all", "largest")]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


# ---------- per-data-set tables from the verified per-problem CSVs ----------
def per_dataset_table(family: str, csv_name: str, tol: str) -> str:
    fn = HERE / f"per_problem/{csv_name}{'' if tol == '1e-4' else '_' + tol}.csv"
    if not fn.exists():
        return ""
    rows = list(csv.DictReader(open(fn)))
    rows = [r for r in rows if r["dataset"] not in DROP_DATASETS.get(family, set())
            and (r["dataset"], r["problem"]) not in DROP_PROBLEMS.get(family, set())]
    solver_cols = sorted({c[:-len("_status")] for c in rows[0] if c.endswith("_status")})
    rule = RULE[tol]
    shown = []
    for sid in solver_cols:
        base, stol = sid.rsplit("_", 1)
        want = rule.get(f"{base}@{family}", rule.get(base))
        if want == stol:
            shown.append((base, sid))
    limit = LIMIT[family]
    datasets = []
    for r in rows:
        name = DATASET_NAMES.get(r["dataset"], r["dataset"])
        if name not in datasets:
            datasets.append(name)
    per: dict = {}
    for base, sid in shown:
        for r in rows:
            ds = DATASET_NAMES.get(r["dataset"], r["dataset"])
            st = r.get(f"{sid}_status", ""); t = r.get(sid, "")
            ok = st == "optimal" and t not in ("", "nan") and float(t) <= limit + GRACE
            slot = per.setdefault((base, ds), {"times": [], "fail": 0})
            if ok:
                slot["times"].append(float(t))
            else:
                slot["fail"] += 1
    head = ["Solver"] + datasets
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    order = sorted({b for b, _ in shown}, key=lambda b: sum(sgm(per[(b, d)]["times"], per[(b, d)]["fail"], limit) for d in datasets if (b, d) in per))
    for base in order:
        cells = []
        for ds in datasets:
            slot = per.get((base, ds))
            if not slot:
                cells.append("–"); continue
            n = len(slot["times"]) + slot["fail"]
            cells.append(f"{len(slot['times'])}/{n} · {sgm(slot['times'], slot['fail'], limit):.1f} s")
        lines.append("| " + " | ".join([LABELS.get(base, base)] + cells) + " |")
    return "\n".join(lines)


# ---------- infeasibility detection ----------
TOL = 1e-3
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
        gm = (math.exp(sum(math.log(x + SHIFT) for x in t) / len(t)) - SHIFT) if t else float("nan")
        lines.append("| " + " | ".join([label(sid), str(c["certified"]), str(c["status"]), str(c["unverified"]),
                                          str(c["near_feasible"]), str(c["wrong"]), str(c["none"]),
                                          "–" if not t else f"{gm:.2f} s"]) + " |")
    return f"{n} problems.\n\n" + "\n".join(lines)


def main() -> None:
    out = ["# Solver benchmark campaign, September 2026", "",
           "Clarabel, CVXOPT, cuOpt, HiGHS, OSQP, PDLP (OR-Tools), PIQP, ProxQP, QTQP, SCS 3.3.1 and SDPA on standard "
           "QP, LP, SDP and infeasible test sets, run on Modal in identical 4-core containers (A100-80GB for the GPU "
           "backends). Every solve is re-verified from the problem data at ten times the plot's target tolerance, so a "
           "\"solve\" below means a verified solution, whatever the solver reported. Failures are charged three times the "
           "time limit in the shifted geometric means (shift 10 s); a solve finishing after the limit plus 60 s counts as "
           "a failure. Because a requested tolerance means different things to different solvers, each plot shows every "
           "solver from the run whose achieved accuracy matches the plot's target: SCS, OSQP and cuOpt from the run at "
           "the nominal tolerance, PDLP and ProxQP from one decade tighter, the interior-point solvers Clarabel, PIQP, "
           "HiGHS, SDPA and CVXOPT from their 1e-6 runs (Clarabel 1e-8 on SDP) and QTQP from its 1e-8 run. "
           "See [MANIFEST.md](MANIFEST.md) for versions, hardware and the full rules.", "",
           "Table cells read *verified solves / problems · shifted geometric mean time*. \"Largest quartile\" is the "
           "quarter of the family with the most nonzeros. Raw rows for every solver, tolerance and problem are in "
           "[`merged/`](merged/) and per-problem status and times in [`per_problem/`](per_problem/).", "",
           "## Headline", "",
           "Largest quarter of the QP and LP sets and the Mittelmann LP set, at 1e-4 (top) and 1e-5 (bottom):", "",
           "![headline 1e-4](figures/all/grid_1e-4.png)", "", "![headline 1e-5](figures/all/grid_1e-5.png)", ""]
    for fam, title, desc, csv_name in FAMILIES:
        out += [f"## {title}", "", desc, ""]
        tols = ["1e-4", "1e-5", "1e-6"] if fam in ("qp", "lp") else (["1e-4", "1e-5"] if fam == "lpbig" else ["1e-4", "1e-6"])
        out += [family_table(fam), ""]
        for t in tols:
            for sub, suffix in (("all problems", ""), ("largest quartile", "_largest")):
                f = HERE / f"figures/all/{fam}_{t}_pair{suffix}.png"
                if f.exists():
                    out += [f"{t}, {sub}:", "", f"![{fam} {t} {sub}](figures/all/{fam}_{t}_pair{suffix}.png)", ""]
        for t in ("1e-4", "1e-6"):
            tab = per_dataset_table(fam, csv_name, t)
            if tab:
                out += [f"By data set at {t}:", "", tab, ""]
    out += ["## Infeasible and unbounded problems", "",
            "Netlib's 29 infeasible LPs (two of them also dual infeasible) and SDPLIB's four infeasible SDPs (two primal "
            "infeasible, two unbounded); small problems, a median of 460 variables. SCS, Clarabel, OSQP, PDLP, CVXOPT and "
            "QTQP return a certificate (a Farkas ray), checked from the problem data at the 1e-3 threshold; HiGHS, PIQP, "
            "cuOpt and SDPA report a status only. A verified certificate of either kind counts as correct; \"near-feasible\" "
            "is an optimal claim whose residuals pass the check (the instance is infeasible by less than the tolerance). "
            "The plot shows the certificate-producing solvers, each from the run in which it certified the most (SCS, "
            "Clarabel and OSQP at a solve tolerance of 1e-8 with certificate tolerance 1e-4, QTQP at 1e-8, PDLP at 1e-5 "
            "with its default certificate tolerance); a verified certificate counts as a solve.", "",
            "![infeasibility](figures/all/infeas_1e-8_pair.png)", "",
            "### Netlib infeasible LPs", "", infeas_table("netlib_infeasible"), "",
            "### SDPLIB infeasible SDPs", "", infeas_table("sdplib_infeasible"), ""]
    (HERE / "README.md").write_text("\n".join(out))
    print("wrote", HERE / "README.md")


if __name__ == "__main__":
    main()
