.. list-table:: Infeasibility detection, Netlib infeasible LPs (29 problems): verified certificate / correct status without certificate / certificate failing the check / reported optimal with residuals within tolerance / wrong / no answer, and shifted geometric mean time (s) over certified and status answers
   :header-rows: 1
   :widths: 24 11 11 11 11 11 11 12

   * - Solver
     - certified
     - status only
     - unverified
     - near-feasible
     - wrong
     - no answer
     - gm time
   * - SCS (CPU, MKL Pardiso), 1e-4
     - 24
     - 0
     - 0
     - 2
     - 3
     - 0
     - 0.20
   * - SCS (CPU, MKL Pardiso), 1e-8 (infeasibility tolerance 1e-4)
     - 26
     - 0
     - 0
     - 1
     - 1
     - 1
     - 0.44
   * - SCS (GPU, cuDSS), 1e-8 (infeasibility tolerance 1e-4)
     - 25
     - 0
     - 0
     - 1
     - 1
     - 2
     - 0.93
   * - Clarabel, 1e-8 (infeasibility tolerance 1e-4)
     - 27
     - 0
     - 1
     - 1
     - 0
     - 0
     - 0.35
   * - PIQP, 1e-6
     - 0
     - 17
     - 0
     - 0
     - 0
     - 12
     - 0.29
   * - HiGHS, 1e-6
     - 0
     - 26
     - 0
     - 0
     - 0
     - 3
     - 0.02
   * - OSQP, 1e-8
     - 19
     - 0
     - 0
     - 0
     - 0
     - 10
     - 1.68
   * - PDLP (OR-Tools), 1e-5
     - 22
     - 0
     - 2
     - 0
     - 0
     - 5
     - 10.91
   * - cuOpt (GPU), 1e-4
     - 0
     - 27
     - 0
     - 0
     - 1
     - 1
     - 0.40

.. list-table:: Infeasibility detection, SDPLIB infeasible SDPs (4 problems): verified certificate / correct status without certificate / certificate failing the check / reported optimal with residuals within tolerance / wrong / no answer, and shifted geometric mean time (s) over certified and status answers
   :header-rows: 1
   :widths: 24 11 11 11 11 11 11 12

   * - Solver
     - certified
     - status only
     - unverified
     - near-feasible
     - wrong
     - no answer
     - gm time
   * - SCS (CPU, MKL Pardiso)
     - 4
     - 0
     - 0
     - 0
     - 0
     - 0
     - 0.04
   * - SCS (GPU, cuDSS)
     - 4
     - 0
     - 0
     - 0
     - 0
     - 0
     - 0.70
   * - Clarabel
     - 4
     - 0
     - 0
     - 0
     - 0
     - 0
     - 0.20
   * - CVXOPT
     - 0
     - 0
     - 2
     - 0
     - 2
     - 0
     - --
   * - SDPA
     - 0
     - 4
     - 0
     - 0
     - 0
     - 0
     - 0.03

