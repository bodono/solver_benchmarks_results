"""Specs for the controlled-hardware completion of the SCS 3.3.2 refresh.

Brendan, 2026-11-14: "We need to make sure everything is running on roughly similar hardware,
so no solver randomly gets a faster cpu". September's kept rows ran on mixed Modal hosts
(and the first November GPU shards on two GPU models and three host CPUs), so every row
the docs compare is produced again on one host type per runner kind:

  CPU kinds (cpu, cpu_big, pdlp): AMD Zen 3 Milan, --require-cpu 25/1
  GPU kinds (gpu, cuopt):         NVIDIA A100 80GB PCIe on Intel 6/106, --require-gpu GPU_HOST_332

Campaigns (fresh volume directories; nothing is resumed from a mixed-host run):
  scs332m  SCS on the CPU, the SDP family (every solver), limit re-solves, infeasible sets
           (already written by make_relaunch_spec.py; running since 13:15)
  scs332g  SCS on cuDSS: every GPU shard of the scs332 spec, same configs
  scs332c  every other solver row of the qp, lp, Mittelmann and Netlib-infeasible families:
           the solver ids and tolerances September ran, on the problems September's rows cover,
           with September's dataset options (QTQP and qpo3, record-only, are left out)

Writes campaign/scs332c/*.yaml + campaign.json, campaign/scs332g/campaign.json and
campaign/scs332_controlled/campaign.json (scs332g + scs332c, GPU first).
Usage: python make_spec_controlled.py
"""
from __future__ import annotations

import collections
import importlib.util
import json
from pathlib import Path

import yaml

H = Path("/Users/bodonoghue/git/sb-refresh")
SEPT = Path("/Users/bodonoghue/git/solver_benchmarks_results/scs33_2026-09")
RAW = Path("/Users/bodonoghue/scs33_tools/refresh_332/sept_archive/scs33_campaign_2026-09/raw_shards")
OUT = "campaign/scs332c"
RECORDS_ONLY = ("qtqp_", "qpo3")

s = importlib.util.spec_from_file_location("make_campaign", H / "tools" / "make_campaign.py")
mc = importlib.util.module_from_spec(s)
s.loader.exec_module(mc)


def rows(family):
    with (SEPT / "merged" / family / "results.jsonl").open() as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def problems(family, dataset_ids):
    out = collections.defaultdict(set)
    for r in rows(family):
        if r["dataset"] in dataset_ids:
            out[r["dataset"]].add(r["problem"])
    return {k: sorted(v) for k, v in out.items()}


# the solver ids September ran per family (SCS and records-only solvers excluded)
ran = collections.defaultdict(set)
for fam, pub in (("qp", "qp"), ("lp", "lp"), ("lpbig", "mittelmann")):
    for r in rows(pub):
        sid = r["solver_id"]
        if sid.startswith("scs_") or sid.startswith(RECORDS_ONLY):
            continue
        if fam == "qp" and r["dataset"] == "mpc" or fam == "lp" and r["dataset"] == "mittelmann":
            continue
        ran[fam].add(sid)

qp = problems("qp", {"maros_meszaros", "qplib"})
lp = problems("lp", {"netlib", "kennington", "miplib_relax"})
big = problems("mittelmann", {"mittelmann0", "mittelmann1", "mittelmann2"})
assert len(qp["maros_meszaros"]) == 138 and len(qp["qplib"]) == 19
assert len(lp["netlib"]) == 93 and len(lp["kennington"]) == 16 and len(lp["miplib_relax"]) == 245
MIPLIB_BIG6 = ["square47", "square41", "neos-3402454-bohle", "neos-2075418-temuka", "supportcase19", "neos-5114902-kasavu"]
MIPLIB_MISS4 = ["mad", "neos-2987310-joes", "piperout-27", "rococoC10-001000"]
miplib_main = [p for p in lp["miplib_relax"] if p not in MIPLIB_BIG6 + MIPLIB_MISS4]
SETS = {
    "qp": [({"name": "maros_meszaros", "id": "maros_meszaros", "include": qp["maros_meszaros"]}, "cpu", ""),
           ({"name": "qplib", "id": "qplib", "dataset_options": {"subset": "all"}, "include": qp["qplib"]}, "cpu", "")],
    "lp": [({"name": "netlib", "id": "netlib", "dataset_options": {"subset": "feasible"}, "include": lp["netlib"]}, "cpu", ""),
           ({"name": "kennington", "id": "kennington", "include": lp["kennington"]}, "cpu", ""),
           ({"name": "miplib", "id": "miplib_relax", "include": miplib_main}, "cpu", ""),
           ({"name": "miplib", "id": "miplib_relax", "include": MIPLIB_BIG6}, "cpu_big", "_big6"),
           ({"name": "miplib", "id": "miplib_relax", "include": MIPLIB_MISS4}, "cpu_big", "_miss4")],
    "lpbig": [({"name": "mittelmann", "id": f"mittelmann{k}", "include": big[f"mittelmann{k}"]}, "cpu_big", "")
              for k in range(3)],
}
TIMEOUT = {"qp": mc.QP_LP_TIMEOUT, "lp": mc.QP_LP_TIMEOUT, "lpbig": mc.LPBIG_TIMEOUT}

out_dir = H / OUT
out_dir.mkdir(parents=True, exist_ok=True)
shards = []


def add_cfg(name, cfg, family, dataset_id, sid, runner, n):
    assert not any(x["name"] == name for x in shards), name
    (out_dir / f"{name}.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    shards.append({"name": name, "family": family, "dataset": dataset_id, "solver_id": sid,
                   "tol": float(sid.rsplit("_", 1)[1]), "gpu": runner in ("gpu", "cuopt"), "runner": runner,
                   "config": f"{OUT}/{name}.yaml", "problems": n, "campaign": "scs332c"})


for fam in ("qp", "lp", "lpbig"):
    for sid in sorted(ran[fam]):
        base, tag = sid.rsplit("_", 1)
        var = next(v for v in mc.solver_variants(fam, float(tag), TIMEOUT[fam]) if v["id"] == sid)
        for ds, runner, suffix in SETS[fam]:
            r = var.get("runner") or runner
            if r == "cpu" and runner == "cpu_big":
                r = "cpu_big"
            cfg = mc.shard_config(fam, ds, var, TIMEOUT[fam])
            name = cfg["run"]["name"] + suffix
            cfg["run"]["name"] = name
            inc = cfg["run"]["datasets"][0].get("include", [])
            exc = set(cfg["run"]["datasets"][0].get("exclude", []))
            add_cfg(name, cfg, fam, ds["id"], sid, r, len(set(inc) - exc))

# Netlib infeasible LPs: September's own configs for every non-SCS, non-record shard
# whose rows the September archive holds (SDPLIB infeasible is in scs332m already)
conf = {}
for d in (SEPT / "configs").iterdir():
    for y in d.glob("*.yaml"):
        conf.setdefault(y.stem, y)
n_inf = 0
for d in sorted(RAW.iterdir()):
    if not d.name.startswith("infeas_netlib_infeasible_") or not (d / "results.jsonl").exists():
        continue
    r0 = json.loads((d / "results.jsonl").read_text().splitlines()[0])
    sid = r0["solver_id"]
    if sid.startswith("scs_") or sid.startswith(RECORDS_ONLY):
        continue
    if d.name in conf:
        cfg = yaml.safe_load(conf[d.name].read_text())
    else:
        # an extra September shard (pdlp_cert4) with no published YAML: rebuild it from the
        # config its manifest recorded
        m = json.loads((d / "manifest.json").read_text())["config"]
        cfg = {"run": {"name": d.name, "datasets": m["datasets"], "output_dir": "results",
                       "parallelism": m.get("parallelism", 1), "resume": True,
                       "timeout_seconds": m["timeout_seconds"]},
               "solvers": [{k: v for k, v in sv.items() if k in ("id", "solver", "settings")} for sv in m["solvers"]]}
    cfg["run"]["name"] = d.name
    solver = cfg["solvers"][0]
    runner = "cuopt" if solver["solver"] == "cuopt" else ("pdlp" if solver["solver"] == "pdlp" else "cpu")
    (ds,) = cfg["run"]["datasets"]
    n = len(ds.get("include", [])) or 29
    add_cfg(d.name, cfg, "infeas", ds["id"], sid, runner, n)
    n_inf += 1

# split into ~1 h chunks by September time, as make_spec.py does
sept_time = {}
for fam in ("qp", "lp", "mittelmann", "infeas"):
    for r in rows(fam):
        k = (r["solver_id"], r["dataset"], r["problem"])
        sept_time[k] = max(sept_time.get(k, 0.0), float(r.get("run_time_seconds") or 0.0))
split = []
for sh in shards:
    path = H / sh["config"]
    cfg = yaml.safe_load(path.read_text())
    (ds,) = cfg["run"]["datasets"]
    limit = cfg["run"]["timeout_seconds"] - 60.0
    probs = [p for p in ds.get("include", []) if p not in set(ds.get("exclude", []))]
    secs = {p: min(sept_time.get((sh["solver_id"], ds["id"], p), limit), limit + 60.0) + 5.0 for p in probs}
    total_h = sum(secs.values()) / 3600.0
    k = min(int(-(-total_h // 1.0)), len(probs)) if probs else 1
    if k <= 1:
        split.append({**sh, "est_hours": round(total_h, 2)})
        continue
    load, parts = [0.0] * k, [[] for _ in range(k)]
    for p in sorted(probs, key=lambda q: -secs[q]):
        i = load.index(min(load)); parts[i].append(p); load[i] += secs[p]
    path.unlink()
    for i, part in enumerate(parts):
        c2 = yaml.safe_load(yaml.safe_dump(cfg))
        c2["run"]["datasets"][0]["include"] = sorted(part)
        c2["run"]["datasets"][0].pop("exclude", None)
        name = f"{sh['name']}_p{i}"
        c2["run"]["name"] = name
        (out_dir / f"{name}.yaml").write_text(yaml.safe_dump(c2, sort_keys=False))
        split.append({**sh, "name": name, "config": f"{OUT}/{name}.yaml", "problems": len(part),
                      "est_hours": round(load[i] / 3600.0, 2)})
assert len({x["name"] for x in split}) == len(split)
(out_dir / "campaign.json").write_text(json.dumps(split, indent=1))

gpu = [dict(x, campaign="scs332g") for x in json.loads((H / "campaign/scs332/campaign.json").read_text())
       if x["runner"] == "gpu"]
(H / "campaign/scs332g").mkdir(exist_ok=True)
(H / "campaign/scs332g/campaign.json").write_text(json.dumps(gpu, indent=1))
(H / "campaign/scs332_controlled").mkdir(exist_ok=True)
gpu_c = [x for x in split if x["runner"] in ("gpu", "cuopt")]
cpu_c = [x for x in split if x["runner"] not in ("gpu", "cuopt")]
(H / "campaign/scs332_controlled/campaign.json").write_text(json.dumps(gpu + gpu_c + cpu_c, indent=1))

RATE = {"cpu": 0.92 * 1.2, "cpu_big": 2.08 * 1.2, "pdlp": 2.08 * 1.2, "gpu": 5.12 * 1.2, "cuopt": 5.12 * 1.2}
hours = collections.Counter()
for x in gpu + split:
    hours[x["runner"]] += x.get("est_hours", 0.0)
print("solvers per family:", {f: sorted(v) for f, v in ran.items()})
print(f"scs332c: {len(split)} shards ({n_inf} Netlib-infeasible), scs332g: {len(gpu)} shards")
for k, h in sorted(hours.items()):
    print(f"  {k:8s} {h:6.1f} est h  ~${h * RATE[k]:6.0f}")
print(f"  total ~${sum(h * RATE[k] for k, h in hours.items()):.0f} at the guard's rates (solve time + 5 s per problem)")
