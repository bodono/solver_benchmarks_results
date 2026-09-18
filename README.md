# solver_benchmarks_results

Raw results of benchmark campaigns run with [bodono/solver_benchmarks](https://github.com/bodono/solver_benchmarks).
One directory per campaign. Each `merged/<family>/` is a run directory the harness reads directly
(`results.jsonl` with one row per (dataset, problem, solver) solve, and its `manifest.json`), so

```bash
bench kkt-verify scs33_2026-09/merged/qp --tol 1e-3 --promote --output-dir /tmp/qp_verified
bench report /tmp/qp_verified
```

reproduce the verified counts and tables from the raw rows. Every row carries the harness's independent
KKT residuals (or certificate residuals for infeasible / unbounded claims) computed from the problem
data, independent of what the solver reported.

| Campaign | What | Site |
|---|---|---|
| [`scs33_2026-09`](scs33_2026-09/) | SCS 3.3.1 vs Clarabel, PIQP, OSQP, ProxQP, HiGHS, PDLP, cuOpt, CVXOPT, SDPA (and QTQP, for the record) on QP, LP, Mittelmann LP, SDP and infeasible problems | [SCS benchmarks page](https://www.cvxgrp.org/scs/benchmarks/) |

The complete archive of each campaign (raw per-shard results, verified runs at every threshold,
Modal logs) is attached to the campaign's GitHub release.
