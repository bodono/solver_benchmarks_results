# SCS 3.3 benchmark campaign, September 2026

Run 2026-09-13 to 2026-09-18 on [Modal](https://modal.com) with
[bodono/solver_benchmarks](https://github.com/bodono/solver_benchmarks) at branch `scs33-campaign`
(commit `24ac4ca`; the harness fixes made during the campaign are merged into `master` at `f18e724`
and later). Results feed the SCS website ([cvxgrp/scs#476](https://github.com/cvxgrp/scs/pull/476),
[#482](https://github.com/cvxgrp/scs/pull/482)).

## Solvers

SCS 3.3.1 (MKL Pardiso on the CPU; cuDSS on the GPU), Clarabel 0.11.1, PIQP 0.6.4, OSQP 1.1.3,
ProxQP 0.7.3 (proxsuite), HiGHS 1.15.1, PDLP from OR-Tools 9.15.6755, NVIDIA cuOpt 26.8.0,
CVXOPT 1.3.3, SDPA (sdpa-python 0.2.3), QTQP 0.0.7 (MKL Pardiso and cuDSS backends) and qpo3 0.1.0
(Rust interior-point solver, Faer linear solver; run 2026-09-18 from a private checkout). QTQP and qpo3
are not shown on the SCS site.

## Hardware

CPU solvers ran in Modal containers reserving 4 physical cores (`cpu=4.0`) and 16 GB of memory
(64 GB for the SDP, Mittelmann, QTQP and qpo3 shards and the Clarabel large-PSD attempts; Modal
kills a container that exceeds its memory request, so these acted as limits). The hosts are AMD EPYC
Zen 3 ("Milan", CPU family 25 model 1; gVisor masks the exact model string; AVX2/FMA, no AVX-512,
one thread per core, observed 1.8-3.1 GHz). Modal's core request is a reservation rather than a cap:
a container sees 20 cores and may burst above 4, so the workers pin the threading runtimes to 4
(`OMP_NUM_THREADS=4` for MKL Pardiso, OpenBLAS and other OpenMP code; from 2026-09-20 also
`RAYON_NUM_THREADS=4`, `MKL_NUM_THREADS=4` and `OPENBLAS_NUM_THREADS=4`). Clarabel, PIQP, OSQP,
HiGHS and PDLP ran single-threaded at their defaults. qpo3's first runs (2026-09-18) predated the
Rayon pin and its Faer factorizations could use more than 4 cores; every qpo3 shard was re-run with
the pin on 2026-09-20 and only the pinned results are kept. Pinning made qpo3 faster, not slower (a
20-thread Rayon pool on a 4-core reservation was oversubscribed): the same 150 QPs and one more LP
verified, with the geometric mean over common solves dropping from 0.78 s to 0.53 s on QP and from
3.06 s to 2.53 s on LP. The GPU solvers (SCS cuDSS, QTQP cuDSS,
cuOpt) ran on an NVIDIA A100-80GB with 8 reserved host cores and 64 GB.

## Families (`merged/`)

| Directory | Problems | Solver settings | Time limit |
|---|---|---|---|
| `qp` | Maros-Meszaros (138) and QPLIB continuous convex (19) | every solver at nominal 1e-4, 1e-5 and 1e-6 (QTQP and qpo3: 1e-4, 1e-6, 1e-8) | 300 s |
| `lp` | Netlib feasible (93), Kennington (16), the 240 MIPLIB 2017 benchmark relaxations (plus a few extras dropped on the site, see `tools/`) | as above | 300 s |
| `mittelmann` | Hans Mittelmann's LP benchmark set (37) | 1e-4 and 1e-5 (QTQP and qpo3: 1e-4, 1e-6, 1e-8; qpo3 could not attempt the two `L1_sixm` instances within 64 GB, counted as failures) | 1800 s |
| `sdp` | SDPLIB (92, incl. the 4 infeasible) and the Mittelmann SDP set (6) | 1e-4 and 1e-6; Clarabel also 1e-8; Clarabel's large-PSD instances attempted one per container | 900 s |
| `infeas` | Netlib infeasible LPs (29), SDPLIB infeasible SDPs (4) | page settings plus SCS / OSQP / Clarabel / PDLP / qpo3 variants with matched infeasibility tolerances | 300 s / 900 s |

The site's plots use the runs matched by achieved accuracy (interior-point solvers from their 1e-6 runs,
Clarabel 1e-8 on SDP, PDLP and ProxQP from 1e-5, QTQP and qpo3 from 1e-8), verification at 10x the plot's target, failures charged
three times the time limit, a limit + 60 s grace rule, SDPLIB's four infeasible instances excluded from
the SDP plots; see `tools/finalize_all.sh` and `tools/make_figures.py` in the harness for the exact rules.

## Layout

- `merged/<family>/results.jsonl`, `manifest.json`: every solve, all solvers, all tolerances.
- `configs/`: the campaign specs and per-shard YAML configs (`scs33*`).
- `figures/site/`: the figures on the SCS site; `figures/records/`: the same with QTQP included;
  `figures/infeasible/`: the infeasibility-detection pair.
- `tables/`: the RST tables on the site and the scripts that generate them; `per_problem/`: one CSV per
  family with time and status per solver.
- `tools/`: the assembly scripts used (paths refer to the machine they ran on).

The full archive (raw per-shard results, verified runs at 1e-3 / 1e-4 / 1e-5, Modal logs, ~42 MB) is the
release asset `scs33_benchmarks_2026-09.tar.gz` on the `scs33-2026-09` release.
