"""Assemble the SCS 3.3.2 benchmark refresh from the controlled-hardware campaigns.

Rule (RELEASE_CHECKLIST.md, 2026-11-14 ~14:20; Brendan 13:14: "make sure everything is running on
roughly similar hardware, so no solver randomly gets a faster cpu"):

- Every row comes from one of three campaigns on the results volume, nothing from September:
    scs332m   CPU-runner shards: SCS on the CPU, the SDP family (every solver), the infeasible sets.
              Its *_limit* shards (re-solves of September limit rows) are not used: scs332c covers them.
    scs332g2  SCS on cuDSS with the cuDSS setting of the fix to cvxgrp/scs#513 (matching off, no
              pivoting, no refinement; Brendan 2026-11-14 ~22:30). It replaces scs332gs (#513's setting,
              SCS 0e7b36ae), which is not used.
    scs332c   every other solver on qp, lp, the Mittelmann LPs and the Netlib infeasible LPs, plus the
              fill shards in campaign/scs332c_fill (same campaign on the volume).
  QTQP and qpo3 (record-only) are not part of the refresh.
- Clarabel out of memory (Brendan 2026-11-14 ~23:00: "If clarabel is OOMing count those problems as
  failures"): in two Mittelmann shards Clarabel's container exceeded its 64 GB on the first problem
  every time (host.txt: one block per container, all rows_before=0, no results file) until Modal
  dropped the input (OOM_LOST). That problem gets a worker_error row ("out of memory"), as the harness
  writes when a worker dies; the shard's other problem ran alone in a fill shard.
- Every container that touched a used shard ran on the target host: CPU kinds on AMD Zen 3 Milan
  (cpu family 25, model 1); GPU kinds on an NVIDIA A100-SXM4-80GB with a Milan host. host.txt has
  one block per container (harness 3bb8c9a and later); each block must show the target host, the
  SCS build (scs-python 91df3fcd, scs_source 0e7b36ae; BUILD_G2 for scs332g2 and the fill shards,
  which ran in the same orchestrator run and image) and the pinned solver versions.
- A used shard must hold exactly the problems its config lists (no missing, no extra). Anything
  else stops the assembly; --allow-partial turns ONLY the completeness check into a report (for a
  test assembly while the run is going). Host, build, version and bad-line problems always stop it.
- Each family is merged with the harness (bench merge; duplicate keys or mixed forms stop it), then
  bench kkt-verify --promote at 10x each tolerance.

Usage: python assemble2.py WORK_DIR [--no-fetch] [--allow-partial]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HARNESS = Path("/Users/bodonoghue/git/sb-refresh")
PY = "/Users/bodonoghue/git/solver_benchmarks/.venv-bench/bin/python"
MODAL = "/Users/bodonoghue/git/solver_benchmarks/.venv-bench/bin/modal"
GPU_CAMPAIGN = "scs332g2"
# (campaign on the volume, spec): the shards whose rows are used
SPECS = [("scs332m", "campaign/scs332m/campaign.json"), (GPU_CAMPAIGN, f"campaign/{GPU_CAMPAIGN}/campaign.json"),
         ("scs332c", "campaign/scs332c/campaign.json"), ("scs332c", "campaign/scs332c_fill/campaign.json")]
CAMPAIGNS = sorted({c for c, _ in SPECS})
GPU_KINDS = {"gpu", "cuopt"}
CPU_HOST = "25/1"
GPU_NAME = "NVIDIA A100-SXM4-80GB"
SCS_PYTHON_SHA = "91df3fcd59757ba65e416cdf820880b4026415d7"
SCS_SOURCE_SHA = "0e7b36ae30f0b427698f121c494029150274439a"
# scs-python commit and scs_source of the scs332g2 run (the cuDSS fix): bodono/scs-python#263 at 13a25e84,
# scs_source = SCS master 7584eece + cvxgrp/scs#525 (4c81d87e). In double precision the only behaviour change
# from 0e7b36ae is the cuDSS setting (#520-#523 touch single precision, comments and messages only).
BUILD_G2: tuple = ("13a25e84830de2549792df16161532624f576920", "4c81d87e92e45aadf15af7236893463073b4b57a")
# lost shard -> (problem whose container ran out of memory, fill shard that ran the other problem and
# holds the failure row, shard of the other tolerance whose row of that problem gives the metadata)
OOM_LOST = {
    "lpbig_mittelmann2_clarabel_1e-6_p1": ("L1_sixm250obs", "lpbig_mittelmann2_clarabel_1e-6_p1_fill",
                                           "lpbig_mittelmann2_clarabel_1e-4_p1"),
    "lpbig_mittelmann2_clarabel_1e-4_p2": ("L1_sixm1000obs", "lpbig_mittelmann2_clarabel_1e-4_p2_fill",
                                           "lpbig_mittelmann2_clarabel_1e-6_p2"),
}
OOM_TARGET = {fill: (lost, prob, tmpl) for lost, (prob, fill, tmpl) in OOM_LOST.items()}
# September's pins (bench_modal SOLVER_PKGS; cuOpt 26.8.0; the PDLP image pins highspy 1.11.0)
PINS = {"scs": "3.3.2", "osqp": "1.1.3", "clarabel": "0.11.1", "piqp": "0.6.4", "proxsuite": "0.7.3",
        "ortools": "9.15.6755", "cvxopt": "1.3.3", "sdpa-python": "0.2.3", "cuopt-cu12": "26.8.0"}
HIGHSPY = {"pdlp": "1.11.0"}  # by runner kind; 1.15.1 elsewhere
FAMILIES = ("qp", "lp", "lpbig", "sdp", "infeas")


def family_of(name: str) -> str:
    for fam in ("lpbig", "infeas", "qp", "lp", "sdp"):
        if name.startswith(fam + "_"):
            return fam
    raise ValueError(name)


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def expected_build(camp: str, name: str) -> tuple:
    return BUILD_G2 if camp == GPU_CAMPAIGN or name.endswith("_fill") else (SCS_PYTHON_SHA, SCS_SOURCE_SHA)


def used_shards(work: Path) -> list[tuple[dict, Path, str]]:
    out = []
    for camp, spec in SPECS:
        for s in json.loads((HARNESS / spec).read_text()):
            if (camp == "scs332m" and "_limit" in s["name"]) or s["name"] in OOM_LOST:
                continue
            out.append((s, work / camp / s["name"], camp))
    names = [(c, s["name"]) for s, _, c in out]
    assert len(set(names)) == len(names)
    return out


def planned_problems(s: dict) -> set[tuple[str, str]]:
    cfg = yaml.safe_load((HARNESS / s["config"]).read_text())
    (ds,) = cfg["run"]["datasets"]
    inc = set(ds.get("include") or [])
    inc -= set(ds.get("exclude") or [])
    if s["name"] in OOM_TARGET:
        inc.add(OOM_TARGET[s["name"]][1])
    return {(ds["id"], p) for p in inc}


def _get(remote: str, local: Path) -> str:
    import time
    err = ""
    for attempt in range(5):
        r = subprocess.run([MODAL, "volume", "get", "scs-bench-results", remote, str(local), "--force"],
                           capture_output=True, text=True)
        if r.returncode == 0 and local.exists():
            return ""
        if "No such file or directory" in r.stderr + r.stdout:
            return "absent"
        err = " ".join(x.strip("│╭╮╰╯─ ") for x in (r.stderr or r.stdout).splitlines()).strip() or "no output"
        time.sleep(2 + 3 * attempt)
    return err


def fetch(work: Path, report: dict) -> None:
    from concurrent.futures import ThreadPoolExecutor
    for camp in [*CAMPAIGNS, "lost"]:
        if (work / camp).exists():
            shutil.rmtree(work / camp)
    jobs = []
    for s, d, camp in used_shards(work):
        d.mkdir(parents=True, exist_ok=True)
        for fn in ("results.jsonl", "manifest.json", "host.txt"):
            jobs.append((f"{camp}/{s['name']}/{fn}", d / fn))
    for lost in OOM_LOST:  # evidence only: host records, and no results file expected
        (work / "lost" / lost).mkdir(parents=True, exist_ok=True)
        for fn in ("results.jsonl", "host.txt"):
            jobs.append((f"scs332c/{lost}/{fn}", work / "lost" / lost / fn))
    with ThreadPoolExecutor(6) as ex:
        errs = list(ex.map(lambda j: _get(*j), jobs))
    failed = [(j[0], e) for j, e in zip(jobs, errs) if e and e != "absent"]
    report["fetch"] = {"files": len(jobs), "absent": sum(e == "absent" for e in errs), "failed": failed[:20]}
    if failed:
        raise SystemExit(f"{len(failed)} files could not be fetched, e.g. {failed[:3]}")


def host_blocks(text: str) -> list[dict]:
    """One record per container: start line, then cpu, GPU, package and build lines."""
    blocks = []
    head = re.compile(r"^=== container start (\S+) task=(\S*) rows_before=(\d+) host=(\S+)$")
    cur = None
    legacy = []
    for line in text.splitlines():
        m = head.match(line)
        if m:
            cur = {"time": m.group(1), "task": m.group(2), "rows_before": int(m.group(3)), "cpu": m.group(4),
                   "gpu": None, "pkgs": {}, "build": None}
            blocks.append(cur)
            continue
        if cur is None:
            legacy.append(line)
            continue
        if line.startswith("NVIDIA ") and cur["gpu"] is None:
            cur["gpu"] = line.split(",")[0].strip()
        elif line.startswith("pkg "):
            _, name, ver = line.split(None, 2)
            cur["pkgs"][name] = ver.strip()
        elif line.startswith("scs-python "):
            parts = line.split()
            cur["build"] = (parts[1], parts[3]) if len(parts) >= 4 else None
    if any(l.strip() for l in legacy):
        blocks.insert(0, {"legacy": True})
    return blocks


def check(work: Path, report: dict, allow_partial: bool) -> None:
    incomplete, fatal, bad_lines = [], [], []
    statuses, hosts = collections.Counter(), collections.Counter()
    for s, d, camp in used_shards(work):
        n, kind = s["name"], s["runner"]
        f = d / "results.jsonl"
        if not f.exists():
            incomplete.append(f"{camp}/{n}: no results")
            continue
        keys = set()
        for i, line in enumerate(f.read_text().splitlines()):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                bad_lines.append(f"{camp}/{n}:{i + 1}")
                continue
            if r["solver_id"] != s["solver_id"]:
                fatal.append(f"{camp}/{n}: row of {r['solver_id']}, shard is {s['solver_id']}")
            keys.add((r["dataset"], r["problem"]))
            statuses[r["status"]] += 1
            want_hs = HIGHSPY.get(kind, "1.15.1")
            for pkg, ver in (((r.get("metadata") or {}).get("runtime") or {}).get("solver_package_versions") or {}).items():
                exp = want_hs if pkg == "highspy" else PINS.get(pkg)
                if exp and ver != exp:
                    fatal.append(f"{camp}/{n}: row {r['problem']} ran {pkg} {ver} (want {exp})")
        plan = planned_problems(s)
        if plan and keys != plan:
            missing, extra = plan - keys, keys - plan
            if extra:
                fatal.append(f"{camp}/{n}: rows for unplanned problems {sorted(extra)[:3]}")
            if missing:
                incomplete.append(f"{camp}/{n}: {len(keys & plan)}/{len(plan)}, missing {sorted(p for _, p in missing)[:4]}")
        elif not plan and len(keys) < (s.get("problems") or 0):
            incomplete.append(f"{camp}/{n}: {len(keys)}/{s['problems']}")
        blocks = host_blocks((d / "host.txt").read_text() if (d / "host.txt").exists() else "")
        if not blocks:
            fatal.append(f"{camp}/{n}: no host record")
        for b in blocks:
            if b.get("legacy"):
                fatal.append(f"{camp}/{n}: host record from before per-container blocks")
                continue
            gpu_kind = kind in GPU_KINDS
            hosts[(kind, b["gpu"] if gpu_kind else None, b["cpu"])] += 1
            if b["cpu"] != CPU_HOST or (gpu_kind and b["gpu"] != GPU_NAME):
                fatal.append(f"{camp}/{n}: container {b['task']} on {b['gpu']}|{b['cpu']}")
            if b["build"] != expected_build(camp, n) and kind != "cuopt" and kind != "pdlp":
                fatal.append(f"{camp}/{n}: container {b['task']} build {b['build']}")
            want = dict(PINS)
            want["highspy"] = HIGHSPY.get(kind, "1.15.1")
            relevant = {"cuopt": ("cuopt-cu12",), "pdlp": ("ortools", "highspy"), "gpu": ("scs",)}.get(
                kind, ("scs", "osqp", "clarabel", "piqp", "proxsuite", "highspy", "cvxopt", "sdpa-python"))
            # blocks written before harness abcccde carry no package lines; their rows' recorded
            # versions are checked below instead
            if b["pkgs"]:
                for pkg in relevant:
                    if b["pkgs"].get(pkg) != want[pkg]:
                        fatal.append(f"{camp}/{n}: container {b['task']} {pkg} {b['pkgs'].get(pkg)} (want {want[pkg]})")
            elif kind == "cuopt":
                fatal.append(f"{camp}/{n}: container {b['task']} has no package lines (cuOpt rows do not record a version)")
    report["check"] = {"shards": len(used_shards(work)), "incomplete": incomplete[:60], "n_incomplete": len(incomplete),
                       "fatal": fatal[:60], "n_fatal": len(fatal), "bad_lines": bad_lines[:20],
                       "container_hosts": {"|".join(str(x) for x in k): v for k, v in hosts.items()},
                       "statuses": dict(statuses)}
    (work / "assembly_report.json").write_text(json.dumps(report, indent=1))
    if fatal or bad_lines:
        raise SystemExit(f"assembly stopped: {len(fatal)} host/build/version/row problems, {len(bad_lines)} bad lines "
                         f"(see {work / 'assembly_report.json'})")
    if incomplete and not allow_partial:
        raise SystemExit(f"assembly stopped: {len(incomplete)} incomplete shards (see {work / 'assembly_report.json'}; "
                         f"--allow-partial for a test assembly)")


def add_oom_rows(work: Path, report: dict) -> None:
    """Failure rows for the problems whose Clarabel container ran out of memory (OOM_LOST)."""
    report["oom_failures"] = []
    for lost, (prob, fill, tmpl_name) in OOM_LOST.items():
        d = work / "lost" / lost
        if (d / "results.jsonl").exists():
            raise SystemExit(f"{lost}: has a results file after all; use its rows instead of OOM_LOST")
        blocks = host_blocks((d / "host.txt").read_text() if (d / "host.txt").exists() else "")
        if not blocks or any(b.get("legacy") or b["cpu"] != CPU_HOST or b["rows_before"] != 0 for b in blocks):
            raise SystemExit(f"{lost}: host record does not show only fresh {CPU_HOST} containers: {blocks}")
        spec = {s["name"]: (s, dd) for s, dd, _ in used_shards(work)}
        (fs, fdir), (ts, tdir) = spec[fill], spec[tmpl_name]
        tmpl = [r for r in read_rows(tdir / "results.jsonl") if r["problem"] == prob]
        if len(tmpl) != 1:
            raise SystemExit(f"{tmpl_name}: no single row for {prob} to take the metadata from")
        rows = read_rows(fdir / "results.jsonl") if (fdir / "results.jsonl").exists() else []
        if any(r["problem"] == prob for r in rows):
            continue  # added by an earlier --no-fetch run
        meta = {k: v for k, v in (tmpl[0].get("metadata") or {}).items() if k != "resume_signature"}
        note = (f"out of memory: in shard {lost} Clarabel's container exceeded its 64 GB on this problem "
                f"{len(blocks)} times (every container started with no rows) and Modal dropped the input; "
                f"counted as a failure (Brendan, 2026-11-14)")
        row = {**tmpl[0], "solver_id": fs["solver_id"], "run_id": fill, "status": "worker_error", "error": note,
               "run_time_seconds": None, "setup_time_seconds": None, "solve_time_seconds": None,
               "iterations": None, "objective_value": None, "kkt": None, "info": {}, "artifact_dir": None,
               "metadata": {**meta, "oom_lost_shard": lost}}
        with open(fdir / "results.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")
        report["oom_failures"].append({"problem": prob, "solver_id": fs["solver_id"], "lost_shard": lost,
                                       "containers": len(blocks), "row_in": fill})


def merge_and_verify(work: Path, report: dict) -> None:
    env = {"PYTHONPATH": str(HARNESS), "PATH": "/usr/bin:/bin"}
    report["merged"] = {}
    for fam in FAMILIES:
        srcs = sorted(str(d) for s, d, _ in used_shards(work) if family_of(s["name"]) == fam and (d / "results.jsonl").exists())
        out = work / "merged" / fam
        r = subprocess.run([PY, "-m", "solver_benchmarks.cli", "merge", str(out), *srcs, "--overwrite"],
                           cwd=HARNESS, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"merge {fam} failed:\n{r.stderr[-2000:]}")
        derived = json.loads((out / "manifest.json").read_text()).get("derived") or {}
        rows = read_rows(out / "results.jsonl")
        report["merged"][fam] = {"sources": len(srcs), "rows": len(rows), "duplicate_keys": derived.get("duplicate_keys"),
                                 "mixed_forms": derived.get("mixed_forms"),
                                 "solvers": dict(collections.Counter(x["solver_id"] for x in rows))}
        if derived.get("duplicate_keys") or derived.get("mixed_forms"):
            raise SystemExit(f"{fam}: duplicate keys or mixed forms: {derived.get('duplicate_keys')} {derived.get('mixed_forms')}")
        if fam == "infeas":
            continue  # the infeasibility tables and plot classify certificates themselves (rst_infeas)
        pairs = [("1e-4", "1e-3"), ("1e-5", "1e-4")] + ([] if fam == "lpbig" else [("1e-6", "1e-5")])
        for tag, thr in pairs:
            r = subprocess.run([PY, "-m", "solver_benchmarks.cli", "kkt-verify", str(out), "--tol", thr, "--promote",
                                "--output-dir", str(work / "verified" / f"{fam}_{tag}"), "--overwrite"],
                               cwd=HARNESS, env=env, capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f"kkt-verify {fam} {tag} failed:\n{r.stderr[-2000:]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("work", type=Path)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--allow-partial", action="store_true", help="report incomplete shards instead of stopping (test only)")
    args = ap.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    (work / "assembly_report.json").unlink(missing_ok=True)
    for sub in ("merged", "verified"):
        if (work / sub).exists():
            shutil.rmtree(work / sub)
    if None in BUILD_G2:
        raise SystemExit("set BUILD_G2 to the scs332g2 run's scs-python and scs_source commits first")
    report: dict = {"rule": f"controlled campaigns scs332m (no _limit), {GPU_CAMPAIGN}, scs332c (+ fill); "
                            "Clarabel out-of-memory problems as worker_error rows; no September rows"}
    if not args.no_fetch:
        fetch(work, report)
    add_oom_rows(work, report)
    check(work, report, args.allow_partial)
    merge_and_verify(work, report)
    (work / "assembly_report.json").write_text(json.dumps(report, indent=1))
    json.dump({k: v for k, v in report.items() if k != "check"} | {"check_summary": {
        k: report["check"][k] for k in ("shards", "n_incomplete", "n_fatal", "container_hosts")}}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
