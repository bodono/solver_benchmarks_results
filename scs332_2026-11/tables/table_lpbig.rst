.. list-table:: Mittelmann LP set: verified solves out of 37 and shifted geometric mean time (s), tolerance 1e-4, 1800 s limit
   :header-rows: 1
   :widths: 40 20 20

   * - Solver
     - verified solves
     - geometric mean (s)
   * - SCS (GPU, cuDSS)
     - 29
     - 152
   * - SCS (CPU, MKL Pardiso)
     - 24
     - 361
   * - Clarabel
     - 21
     - 693
   * - PDLP (OR-Tools)
     - 19
     - 738
   * - PIQP
     - 12
     - 1332
   * - cuOpt (GPU)
     - 8
     - 1748
   * - HiGHS
     - 9
     - 2947
