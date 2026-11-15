# solver_benchmarks_results

Raw results of benchmark campaigns run with [bodono/solver_benchmarks](https://github.com/bodono/solver_benchmarks).
One directory per campaign. Each `merged/<family>/` is a run directory the harness reads directly
(`results.jsonl` with one row per (dataset, problem, solver) solve, and its `manifest.json`), so

```bash
bench kkt-verify scs332_2026-11/merged/qp --tol 1e-3 --promote --output-dir /tmp/qp_verified
bench report /tmp/qp_verified
```

reproduce the verified counts and tables from the raw rows. Every row carries the harness's independent
KKT residuals (or certificate residuals for infeasible / unbounded claims) computed from the problem
data, independent of what the solver reported.

| Campaign | What | Site |
|---|---|---|
| [`scs332_2026-11`](scs332_2026-11/) | Clarabel, CVXOPT, cuOpt, HiGHS, OSQP, PDLP, PIQP, ProxQP, SCS 3.3.2 and SDPA on QP, LP, Mittelmann LP, SDP and infeasible problems, every solver on the same hardware | run for the [SCS benchmarks page](https://www.cvxgrp.org/scs/benchmarks/) (SCS 3.3.2) |
| [`scs33_2026-09`](scs33_2026-09/) | Clarabel, CVXOPT, cuOpt, HiGHS, OSQP, PDLP, PIQP, ProxQP, qpo3, QTQP, SCS 3.3.1 and SDPA on QP, LP, Mittelmann LP, SDP and infeasible problems, on Modal hosts not controlled or recorded per container | run for the SCS 3.3 benchmarks page; replaced by `scs332_2026-11` |

The latest campaign (`scs332_2026-11`). Largest quarter of the QP and LP sets and the Mittelmann LP set, at 1e-4:

![November 2026 campaign headline](scs332_2026-11/figures/all/grid_1e-4.png)

SDPLIB and the Mittelmann SDPs at 1e-4:

![SDP](scs332_2026-11/figures/all/sdp_1e-4_pair.png)

Infeasibility detection on the Netlib infeasible LPs (a solve is a verified certificate):

![infeasibility](scs332_2026-11/figures/all/infeas_1e-8_pair.png)

Each campaign directory has a README with the plots and headline tables for every solver and test set
(for example [`scs332_2026-11/README.md`](scs332_2026-11/README.md)) and a MANIFEST with versions, hardware and
rules. The complete archive of each campaign (raw per-shard results, verified runs at every threshold,
Modal logs) is attached to the campaign's GitHub release.
