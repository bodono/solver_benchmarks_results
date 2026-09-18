.. list-table:: Mittelmann LP set: verified solves out of 37 and shifted geometric mean time (s), tolerance 1e-4, 1800 s limit
   :header-rows: 1
   :widths: 40 20 20

   * - Solver
     - verified solves
     - geometric mean (s)
   * - SCS (GPU, cuDSS)
     - 28
     - 208
   * - SCS (CPU, MKL Pardiso)
     - 24
     - 431
   * - PDLP (OR-Tools)
     - 19
     - 733
   * - Clarabel
     - 20
     - 817
   * - PIQP
     - 12
     - 1352
   * - cuOpt (GPU)
     - 7
     - 2086
   * - HiGHS
     - 9
     - 2889
