# SCS 3.3.2 benchmark campaign, November 2026

Run 2026-11-14 (CPU solvers) and 2026-11-15 (GPU solvers) on [Modal](https://modal.com) with
[bodono/solver_benchmarks](https://github.com/bodono/solver_benchmarks) at master `7330423` (every loader and scoring
fix up to #122) plus runner-only commits on branch `scs332-campaign` (`tools/bench_modal.py`: version pins, SCS built
from source, hardware filters; the CPU shards ran at `3bb8c9a` to `2084139`, the GPU run at `0c2165f`). Results feed
the SCS documentation's benchmarks page (cvxgrp/scs, docs/src/benchmarks). It replaces the September 2026 campaign
([`../scs33_2026-09`](../scs33_2026-09), SCS 3.3.1) for the page: every row here was produced again in November;
nothing is carried over from September (Clarabel was not run again on four SDPs, see `sdp` below).

## Solvers

SCS 3.3.2 (bodono/scs-python `91df3fcd`, SCS core `0e7b36ae`, built from source with static MKL 2026.1.0 as the
PyPI wheel is; MKL Pardiso on the CPU, cuDSS 1.0.0 on the GPU; the GPU runs and the Clarabel fill shards use
scs-python `13a25e84`, whose SCS core `4c81d87e` is SCS master `7584eece` plus cvxgrp/scs#525's cuDSS setting,
and in double precision differs from `0e7b36ae` only in that setting), Clarabel 0.11.1, PIQP 0.6.4, OSQP 1.1.3, ProxQP 0.7.3
(proxsuite), HiGHS 1.15.1, PDLP from OR-Tools 9.15.6755, NVIDIA cuOpt 26.8.0, CVXOPT 1.3.3 and SDPA (sdpa-python
0.2.3): the versions of the September campaign for every solver other than SCS. QTQP, qpo3 and cpo3 are not part of
this campaign.

## Hardware

Modal places a container on whatever host type is free, and its pools are mixed: the 4-core CPU containers land on
AMD EPYC Zen 3 (cpu family 25 model 1), Zen 4 (25/17) and several Intel generations, and an "A100-80GB" request on
the PCIe or the SXM4 card with Intel or AMD hosts. September's campaign did not control for this. Here every
container checked its hardware on start, and one on another type handed its job back to be queued again:

- CPU solvers: 4 reserved cores (`cpu=4.0`; 16 GB, or 64 GB for the SDP, Mittelmann and large MIPLIB shards) on AMD
  EPYC Zen 3 Milan hosts only. Modal's reservation is not a cap, so OpenMP, MKL, OpenBLAS and Rayon are pinned to 4
  threads. Clarabel, PIQP, OSQP, HiGHS and PDLP run single-threaded at their defaults.
- GPU solvers (SCS with cuDSS, cuOpt): NVIDIA A100-SXM4-80GB with 8 cores of an AMD EPYC Zen 3 Milan host, 64 GB.

Each shard's `host.txt` (in the release archive) has one block per container that ran it: start time, Modal task
id, rows found, CPU family/model, GPU, solver package versions and the SCS build; the assembly refuses any shard
with a container on other hardware, another SCS build or another solver version (`tools/assemble2.py`).
In the 459 shards used, 603 containers ran: 488 CPU containers (204 standard, 217 large-memory and 67 PDLP), all
on Zen 3 Milan, and 115 GPU containers (87 SCS with cuDSS, 28 cuOpt), all on an A100-SXM4-80GB with a Milan host.

## Campaigns (Modal volume `scs-bench-results`)

| Campaign | What | Shards |
|---|---|---|
| `scs332m` | SCS on the CPU (qp, lp, Mittelmann, sdp, infeasible), every solver on the SDP family, SDPLIB infeasible | 118 |
| `scs332g2` | SCS with cuDSS (qp, lp, Mittelmann, sdp, infeasible), with the cuDSS setting of cvxgrp/scs#525 (matching off, no pivoting, no refinement) | 87 |
| `scs332c` | Clarabel, PIQP, OSQP, ProxQP, HiGHS, PDLP, cuOpt on qp, lp, Mittelmann and the Netlib infeasible LPs (with the fill shards of `configs/scs332c_fill`) | 252 + 2 fill |

Clarabel's container ran out of its 64 GB on the first problem of two Mittelmann shards every time it
started (L1_sixm250obs at 1e-6, L1_sixm1000obs at 1e-4; the same problems hit the 1800 s limit in the
other two runs) until Modal dropped the input. Those two problems are recorded as failures (`worker_error`,
"out of memory"); the shards' other problems (s82, set-cover-model) ran alone in fill shards.
`scs332gs` (SCS on cuDSS with cvxgrp/scs#513's setting: no pivoting, one refinement step per solve) ran too,
on the same GPU host type, and is not used.

The problem lists, solver ids and tolerances are September's (`tools/make_spec.py`, `tools/make_spec_controlled.py`).
Earlier November runs on unfiltered hardware (campaigns `scs332`, `scs332g`) are not used.

## Families (`merged/`)

| Directory | Problems | Settings | Time limit |
|---|---|---|---|
| `qp` | Maros-Meszaros (138) and QPLIB continuous convex (19) | every solver at its September tolerances (1e-4 to 1e-6) | 300 s |
| `lp` | Netlib feasible (93), Kennington (16), the 240 MIPLIB 2017 benchmark relaxations (plus 5 extras dropped on the site) | as above | 300 s |
| `mittelmann` | Hans Mittelmann's LP benchmark set (37) | 1e-4 and 1e-5 | 1800 s |
| `sdp` | SDPLIB (88 feasible) and the Mittelmann SDP set (6) | 1e-4 and 1e-6; Clarabel also 1e-8, its large-PSD instances one per container, except equalG11, equalG51, maxG55 and G40mc, which exceeded its 64 GB in September with the same version and were not run again (no rows; the site counts them as failures) | 900 s |
| `infeas` | Netlib infeasible LPs (29), SDPLIB infeasible SDPs (4) | page settings plus matched infeasibility tolerances | 300 s / 900 s |

The site's plots use the runs matched by achieved accuracy (interior-point solvers from their 1e-6 runs, Clarabel
1e-8 on SDP, PDLP and ProxQP from one decade tighter), verification at 10x the plot's target, failures charged three
times the time limit, and a limit + 60 s grace rule (`tools/figures_tables.sh`, harness `tools/make_figures.py`).

## Layout

- `merged/<family>/results.jsonl`, `manifest.json`: every solve, all solvers, all tolerances.
- `configs/<campaign>/`: the campaign specs and the YAML of every shard used.
- `figures/site/`: the figures on the SCS site; `figures/all/`: solver-neutral colours, every solver.
- `tables/`: the RST tables on the site, the geomean summaries and the assembly report; `per_problem/`: one CSV per
  family with verified status and time per solver.
- `tools/`: the scripts used (paths refer to the machine they ran on).

The full archive (raw per-shard results with their host records, verified runs, orchestrator logs) is the release
asset `scs332_benchmarks_2026-11.tar.gz` on the `scs332-2026-11` release.
