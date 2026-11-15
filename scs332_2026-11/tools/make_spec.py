"""Spec for the SCS 3.3.2 benchmark refresh (November 2026).

What is run, in the order the runner starts it (the budget guard drops what
comes last):

 1. SCS on the CPU: qp, lp, Mittelmann LPs.
 2. SCS on cuDSS: qp, lp, Mittelmann LPs.
 3. Every solver of the SDP family on the CPU (SCS, Clarabel, CVXOPT, SDPA),
    with Clarabel's large-PSD instances one per container as in September.
 4. Re-solves of the September rows where Clarabel, PIQP or HiGHS stopped at a
    limit with a point: the September harness recorded no residuals for
    those, so they could not be promoted the way SCS's limit rows are.
 5. The infeasible sets: SCS on the Netlib infeasible LPs, every solver on the
    four infeasible SDPLIB problems.
 6. SCS on cuDSS for the SDP family (the most expensive item, so last).

Every shard lists its problems by name, taken from the September rows, so the
new rows cover exactly the problems the kept rows cover.

Usage: python make_spec.py <harness worktree> <september results dir> [campaign dir name]
"""

from __future__ import annotations

import collections
import importlib.util
import json
import sys
from pathlib import Path

import yaml

HARNESS = Path(sys.argv[1]).resolve()
SEPT = Path(sys.argv[2]).resolve()
CAMPAIGN_DIR = sys.argv[3] if len(sys.argv) > 3 else "campaign/scs332"

spec = importlib.util.spec_from_file_location("make_campaign", HARNESS / "tools" / "make_campaign.py")
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)

SDPLIB_INFEASIBLE = ["infd1", "infd2", "infp1", "infp2"]
# MIPLIB relaxations over 20 MB (September: campaign scs33big6, 64 GB containers)
# and the four that completed the benchmark set (scs33miss4).
MIPLIB_BIG6 = ["square47", "square41", "neos-3402454-bohle", "neos-2075418-temuka", "supportcase19",
               "neos-5114902-kasavu"]
MIPLIB_MISS4 = ["mad", "neos-2987310-joes", "piperout-27", "rococoC10-001000"]


def rows(family: str):
    with (SEPT / "merged" / family / "results.jsonl").open() as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def september_problems(family: str, solver_id: str = "scs_cpu_1e-4") -> dict[str, list[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for r in rows(family):
        if r["solver_id"] == solver_id:
            out[r["dataset"]].add(r["problem"])
    return {k: sorted(v) for k, v in out.items()}


def variant(family: str, tol: float, solver_id_prefix: str) -> dict:
    timeout = {"sdp": mc.SDP_TIMEOUT, "lpbig": mc.LPBIG_TIMEOUT}.get(family, mc.QP_LP_TIMEOUT)
    for v in mc.solver_variants(family, tol, timeout):
        if v["id"].startswith(solver_id_prefix + "_"):
            return v
    raise KeyError((family, tol, solver_id_prefix))


shards: list[dict] = []
out_dir = HARNESS / CAMPAIGN_DIR
out_dir.mkdir(parents=True, exist_ok=True)


def add(family: str, dataset: dict, var: dict, timeout: float, runner: str, suffix: str = "") -> None:
    cfg = mc.shard_config(family, dataset, var, timeout)
    name = cfg["run"]["name"] + suffix
    cfg["run"]["name"] = name
    assert not any(s["name"] == name for s in shards), name
    path = out_dir / f"{name}.yaml"
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    shards.append({"name": name, "family": family, "dataset": dataset["id"], "solver_id": var["id"],
                   "tol": float(var["id"].rsplit("_", 1)[1]), "gpu": runner == "gpu", "runner": runner,
                   "config": f"{CAMPAIGN_DIR}/{name}.yaml",
                   "problems": len(set(cfg["run"]["datasets"][0].get("include", []))
                                   - set(cfg["run"]["datasets"][0].get("exclude", [])))})


def tol_of(tag: str) -> float:
    return float(tag)


qp = september_problems("qp")
lp = september_problems("lp")
big = september_problems("mittelmann")
sdp = september_problems("sdp")
assert len(qp["maros_meszaros"]) == 138 and len(qp["qplib"]) == 19, {k: len(v) for k, v in qp.items()}
assert len(lp["netlib"]) == 93 and len(lp["kennington"]) == 16 and len(lp["miplib_relax"]) == 245
assert [len(big[f"mittelmann{k}"]) for k in range(3)] == [13, 12, 12]
assert len(sdp["sdplib"]) == 92 and len(sdp["mittelmann_sdp"]) == 6
for k in range(3):  # the chunks are the ones make_campaign defines
    assert big[f"mittelmann{k}"] == sorted(mc.MITTELMANN_CHUNKS[k]), k
assert set(MIPLIB_BIG6 + MIPLIB_MISS4) <= set(lp["miplib_relax"])
miplib_main = [p for p in lp["miplib_relax"] if p not in MIPLIB_BIG6 + MIPLIB_MISS4]
sdplib_feasible = [p for p in sdp["sdplib"] if p not in SDPLIB_INFEASIBLE]
assert len(sdplib_feasible) == 88

def sdplib_chunks(solver_id: str, k: int = 3) -> list[list[str]]:
    """The 88 feasible SDPLIB problems in k chunks of about equal September time
    for this solver id, so that no SCS SDP shard nears the 20 h container limit."""
    secs = collections.defaultdict(float)
    for r in rows("sdp"):
        if r["solver_id"] == solver_id and r["dataset"] == "sdplib":
            secs[r["problem"]] = float(r.get("run_time_seconds") or 0)
    order = sorted(sdplib_feasible, key=lambda p: -secs.get(p, mc.SDP_TIMEOUT))
    load = [0.0] * k
    out = [[] for _ in range(k)]
    for p in order:
        i = load.index(min(load))
        out[i].append(p)
        load[i] += secs.get(p, mc.SDP_TIMEOUT)
    return [sorted(c) for c in out]


QP_SETS = [
    ({"name": "maros_meszaros", "id": "maros_meszaros", "include": qp["maros_meszaros"]}, "cpu"),
    ({"name": "qplib", "id": "qplib", "dataset_options": {"subset": "all"}, "include": qp["qplib"]}, "cpu"),
]
LP_SETS = [
    ({"name": "netlib", "id": "netlib", "dataset_options": {"subset": "feasible"}, "include": lp["netlib"]}, "cpu", ""),
    ({"name": "kennington", "id": "kennington", "include": lp["kennington"]}, "cpu", ""),
    ({"name": "miplib", "id": "miplib_relax", "include": miplib_main}, "cpu", ""),
    ({"name": "miplib", "id": "miplib_relax", "include": MIPLIB_BIG6}, "cpu_big", "_big6"),
    ({"name": "miplib", "id": "miplib_relax", "include": MIPLIB_MISS4}, "cpu_big", "_miss4"),
]
BIG_SETS = [({"name": "mittelmann", "id": f"mittelmann{k}", "include": big[f"mittelmann{k}"]}, "cpu_big")
            for k in range(3)]
SDP_SETS = [
    ({"name": "sdplib", "id": "sdplib", "include": sdplib_feasible}, "cpu_big"),
    ({"name": "mittelmann_sdp", "id": "mittelmann_sdp", "dataset_options": {"subset": "all"},
      "include": sdp["mittelmann_sdp"]}, "cpu_big"),
]

# 1 and 2: SCS on qp, lp and the Mittelmann LPs, CPU first.
for solver, gpu in (("scs_cpu", False), ("scs_cudss", True)):
    for tol in (1e-4, 1e-5, 1e-6):
        for ds, runner in QP_SETS:
            add("qp", ds, variant("qp", tol, solver), mc.QP_LP_TIMEOUT, "gpu" if gpu else runner)
        for ds, runner, suffix in LP_SETS:
            add("lp", ds, variant("lp", tol, solver), mc.QP_LP_TIMEOUT, "gpu" if gpu else runner, suffix)
    for tol in (1e-4, 1e-5):
        for ds, runner in BIG_SETS:
            add("lpbig", ds, variant("lpbig", tol, solver), mc.LPBIG_TIMEOUT, "gpu" if gpu else runner)

# 3: the SDP family on the CPU, every solver. SCS's SDPLIB shards in chunks.
for tol in (1e-4, 1e-6):
    for solver in ("scs_cpu", "clarabel", "cvxopt", "sdpa"):
        for ds, runner in SDP_SETS:
            if solver == "scs_cpu" and ds["id"] == "sdplib":
                tag = f"{tol:.0e}".replace("e-0", "e-")
                for i, chunk in enumerate(sdplib_chunks(f"scs_cpu_{tag}")):
                    add("sdp", {**ds, "include": chunk}, variant("sdp", tol, solver), mc.SDP_TIMEOUT, runner, f"_c{i}")
                continue
            add("sdp", ds, variant("sdp", tol, solver), mc.SDP_TIMEOUT, runner)
for ds, runner in SDP_SETS:
    add("sdp", ds, variant("sdp", 1e-8, "clarabel"), mc.SDP_TIMEOUT, runner)
# Clarabel on the instances with a large PSD block, one per container (it can
# take the container down); make_campaign excludes them from the shards above.
clarabel8 = variant("sdp", 1e-8, "clarabel")
# equalG11, equalG51 and maxG55 are single PSD blocks that ran out of 64 GB in
# September (as did G40mc); same Clarabel, same memory, so not tried again (a
# missing row counts as a failure either way). maxG60 had no real attempt then.
OOM_SEPTEMBER = {"equalG11", "equalG51", "maxG55"}
for prob in mc.LARGE_PSD_BLOCKS:
    assert prob in sdplib_feasible, prob
    if prob in OOM_SEPTEMBER:
        continue
    cfg_ds = {"name": "sdplib", "id": "sdplib", "include": [prob]}
    # shard_config would put the exclusion list back; write this one directly
    name = f"sdp_sdplib_clarabel_1e-8_try_{prob}"
    cfg = {"run": {"name": name, "output_dir": "results", "parallelism": 1, "resume": True,
                   "timeout_seconds": mc.SDP_TIMEOUT + 60.0, "datasets": [cfg_ds]},
           "solvers": [{k: v for k, v in clarabel8.items() if k not in ("gpu", "runner")}]}
    (out_dir / f"{name}.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    shards.append({"name": name, "family": "sdp", "dataset": "sdplib", "solver_id": "clarabel_1e-8", "tol": 1e-8,
                   "gpu": False, "runner": "cpu_big", "config": f"{CAMPAIGN_DIR}/{name}.yaml", "problems": 1})
# G40mc (Mittelmann SDP, one block of order 2000) also ran out of 64 GB in
# September, so it has no try either.

# 4: limit rows of Clarabel, PIQP and HiGHS that returned a point but have no
# residuals in September. HiGHS only on qp: on lp and the Mittelmann LPs it
# returned no point at the time limit (solution status none).
limit: dict[tuple, set[str]] = collections.defaultdict(set)
for family in ("qp", "lp", "mittelmann"):
    for r in rows(family):
        base = r["solver_id"].rsplit("_", 1)[0]
        if base not in ("clarabel", "piqp", "highs") or (base == "highs" and family != "qp"):
            continue
        carried = bool((r.get("info") or {}).get("carried_from") or (r.get("metadata") or {}).get("carried_from"))
        at_limit = r["status"] in ("time_limit", "max_iter_reached")
        # a point but no residuals; harness kills (error set) returned no point
        if (at_limit or carried) and not r.get("kkt") and not r.get("error"):
            if r["dataset"] in ("mpc", "mittelmann") and family != "mittelmann":
                continue  # not part of the published families
            limit[(family, r["dataset"], r["solver_id"])].add(r["problem"])
n_limit = 0
for (family, dataset_id, solver_id), probs in sorted(limit.items()):
    fam = "lpbig" if family == "mittelmann" else family
    base, tag = solver_id.rsplit("_", 1)
    timeout = mc.LPBIG_TIMEOUT if fam == "lpbig" else mc.QP_LP_TIMEOUT
    name_of = {"maros_meszaros": "maros_meszaros", "qplib": "qplib", "netlib": "netlib", "kennington": "kennington",
               "miplib_relax": "miplib"}.get(dataset_id, "mittelmann")
    ds = {"name": name_of, "id": dataset_id}
    if dataset_id == "qplib":
        ds["dataset_options"] = {"subset": "all"}
    if dataset_id == "netlib":
        ds["dataset_options"] = {"subset": "feasible"}
    for part, runner, suffix in (
        (sorted(p for p in probs if p not in MIPLIB_BIG6), "cpu_big" if fam == "lpbig" else "cpu", "_limit"),
        (sorted(p for p in probs if p in MIPLIB_BIG6), "cpu_big", "_limit_big6"),
    ):
        if part:
            add(fam, {**ds, "include": part}, variant(fam, float(tag), base), timeout, runner, suffix)
            n_limit += len(part)

# 5: infeasible sets. The September configs are reused as they are; the SDPLIB
# ones need the subset, which did not exist then (the default is now feasible).
n_inf = 0
# (The folders also hold the plain SCS configs that the _inf variants replaced
# in September; only the names in each campaign.json produced published rows.)
listed = sorted({(d.name, s["name"]) for d in (SEPT / "configs").glob("scs33infeas*")
                 for s in json.loads((d / "campaign.json").read_text())})
for folder, shard_name in listed:
    cfg_path = SEPT / "configs" / folder / f"{shard_name}.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    solver = cfg["solvers"][0]
    (ds,) = cfg["run"]["datasets"]
    if not (solver["id"].startswith("scs_") or ds["id"] == "sdplib_infeasible"):
        continue
    if ds["id"] == "sdplib_infeasible":
        ds["dataset_options"] = {"subset": "infeasible"}
        assert sorted(ds["include"]) == SDPLIB_INFEASIBLE, ds
    name = cfg["run"]["name"]
    assert not any(s["name"] == name for s in shards), name
    gpu = solver.get("settings", {}).get("linear_solver") == "cudss"
    (out_dir / f"{name}.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    shards.append({"name": name, "family": "infeas", "dataset": ds["id"], "solver_id": solver["id"],
                   "tol": float(solver["id"].rsplit("_", 1)[1]), "gpu": gpu, "runner": "gpu" if gpu else "cpu",
                   "config": f"{CAMPAIGN_DIR}/{name}.yaml", "problems": len(ds.get("include", [])) or 29})
    n_inf += 1

# 6: SCS on cuDSS for the SDP family, 1e-4 first; SDPLIB in chunks (the 1e-6
# September run reached only 28 problems, so its chunks use the 1e-4 times).
for tol in (1e-4, 1e-6):
    for ds, _ in SDP_SETS:
        if ds["id"] == "sdplib":
            for i, chunk in enumerate(sdplib_chunks("scs_cudss_1e-4")):
                add("sdp", {**ds, "include": chunk}, variant("sdp", tol, "scs_cudss"), mc.SDP_TIMEOUT, "gpu", f"_c{i}")
            continue
        add("sdp", ds, variant("sdp", tol, "scs_cudss"), mc.SDP_TIMEOUT, "gpu")

# Split every shard into chunks of about CHUNK_HOURS of September solve time,
# balanced by each problem's time (charged the limit where September has none),
# so that many containers can run at once and none runs for hours. The order of
# the chunks keeps the order of the shards, so the priority is unchanged.
CHUNK_HOURS = 1.0
sept_time: dict[tuple, float] = {}
for family in ("qp", "lp", "mittelmann", "sdp", "infeas"):
    for r in rows(family):
        k = (r["solver_id"], r["dataset"], r["problem"])
        sept_time[k] = max(sept_time.get(k, 0.0), float(r.get("run_time_seconds") or 0.0))
split: list[dict] = []
for sh in shards:
    path = HARNESS / sh["config"]
    cfg = yaml.safe_load(path.read_text())
    (ds,) = cfg["run"]["datasets"]
    sid = cfg["solvers"][0]["id"]
    limit = cfg["run"]["timeout_seconds"] - 60.0
    probs = [p for p in ds.get("include", []) if p not in set(ds.get("exclude", []))]
    secs = {p: min(sept_time.get((sid, ds["id"], p), limit), limit + 60.0) + 5.0 for p in probs}
    total_h = sum(secs.values()) / 3600.0
    k = int(-(-total_h // CHUNK_HOURS)) if probs else 1
    k = min(k, len(probs)) if probs else 1
    if k <= 1:
        sh["est_hours"] = round(total_h, 2)
        split.append(sh)
        continue
    load = [0.0] * k
    parts: list[list[str]] = [[] for _ in range(k)]
    for p in sorted(probs, key=lambda q: -secs[q]):
        i = load.index(min(load))
        parts[i].append(p)
        load[i] += secs[p]
    path.unlink()
    for i, part in enumerate(parts):
        c2 = yaml.safe_load(yaml.safe_dump(cfg))
        c2["run"]["datasets"][0]["include"] = sorted(part)
        c2["run"]["datasets"][0].pop("exclude", None)
        name = f"{sh['name']}_p{i}"
        c2["run"]["name"] = name
        (out_dir / f"{name}.yaml").write_text(yaml.safe_dump(c2, sort_keys=False))
        split.append({**sh, "name": name, "config": f"{CAMPAIGN_DIR}/{name}.yaml", "problems": len(part),
                      "est_hours": round(load[i] / 3600.0, 2)})
shards = split
assert len({s["name"] for s in shards}) == len(shards)

(out_dir / "campaign.json").write_text(json.dumps(shards, indent=2))
kinds = collections.Counter(s["runner"] for s in shards)
hours = collections.defaultdict(float)
for x in shards:
    hours[x["runner"]] += x.get("est_hours", 0.0)
print(f"{len(shards)} shards: {dict(kinds)}; limit re-solves {n_limit} rows; infeasible shards {n_inf}; "
      f"est. hours {dict((k, round(v, 1)) for k, v in hours.items())}; longest "
      f"{max(x.get('est_hours', 0) for x in shards):.2f} h")
