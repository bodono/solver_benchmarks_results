.. list-table:: Achieved accuracy of the runs shown in the headline plots: median and 90th percentile of the largest relative KKT residual over each solver's verified solves (returns that fail the check are excluded for every solver)
   :header-rows: 2
   :widths: 20 10 11 11 11 11 11 11 11 11

   * - Solver
     - run
     - QP
     -
     - LP
     -
     - Mittelmann
     -
     - SDP
     -
   * -
     -
     - median
     - 90th
     - median
     - 90th
     - median
     - 90th
     - median
     - 90th
   * - SCS (CPU)
     - 1e-4
     - 7e-6
     - 1e-4
     - 3e-5
     - 9e-5
     - 7e-5
     - 9e-5
     - 9e-5
     - 1e-4
   * - SCS (GPU, cuDSS)
     - 1e-4
     - 1e-5
     - 9e-5
     - 3e-5
     - 9e-5
     - 5e-5
     - 1e-4
     - 9e-5
     - 3e-4
   * - OSQP
     - 1e-4
     - 5e-5
     - 1e-4
     - 6e-5
     - 1e-4
     - --
     - --
     - --
     - --
   * - PDLP (OR-Tools)
     - 1e-5
     - --
     - --
     - 9e-6
     - 1e-4
     - 2e-5
     - 2e-4
     - --
     - --
   * - cuOpt (GPU)
     - 1e-4
     - 4e-8
     - 3e-6
     - 6e-11
     - 7e-5
     - 6e-5
     - 5e-4
     - --
     - --
   * - ProxQP
     - 1e-5
     - 5e-6
     - 9e-5
     - --
     - --
     - --
     - --
     - --
     - --
   * - Clarabel
     - 1e-6 (1e-8 SDP)
     - 2e-7
     - 1e-6
     - 1e-7
     - 2e-6
     - 3e-7
     - 2e-6
     - 8e-8
     - 2e-6
   * - PIQP
     - 1e-6 (1e-4 Mittelmann)
     - 8e-10
     - 9e-8
     - 2e-10
     - 5e-8
     - 3e-10
     - 5e-6
     - --
     - --
   * - HiGHS
     - 1e-6 (1e-4 Mittelmann)
     - 5e-8
     - 9e-5
     - 7e-16
     - 1e-12
     - 1e-7
     - 3e-5
     - --
     - --
   * - SDPA
     - 1e-6
     - --
     - --
     - --
     - --
     - --
     - --
     - 2e-7
     - 5e-6
   * - CVXOPT
     - 1e-6
     - --
     - --
     - --
     - --
     - --
     - --
     - 3e-7
     - 2e-5
