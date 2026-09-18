.. list-table:: Verified solves and shifted geometric mean time (s) at the 1e-4 and 1e-5 settings; interior-point solvers unchanged (shown from their tightest run in both)
   :header-rows: 1
   :widths: 30 24 12 12 12 12

   * - Problem set
     - Solver
     - solved 1e-4
     - time 1e-4
     - solved 1e-5
     - time 1e-5
   * - Maros-Meszaros and QPLIB QPs, largest quartile (40)
     - Clarabel
     - 37
     - 13
     - 37
     - 13
   * - 
     - PIQP
     - 34
     - 18
     - 34
     - 18
   * - 
     - SCS (GPU, cuDSS)
     - 38
     - 9
     - 33
     - 20
   * - 
     - SCS (CPU, MKL Pardiso)
     - 38
     - 13
     - 35
     - 21
   * - 
     - cuOpt (GPU)
     - 32
     - 22
     - 31
     - 24
   * - 
     - OSQP
     - 32
     - 29
     - 31
     - 38
   * - 
     - HiGHS
     - 13
     - 268
     - 12
     - 290
   * - 
     - ProxQP
     - 12
     - 346
     - 12
     - 348
   * - Kennington and MIPLIB-relaxation LPs, largest quartile (88)
     - HiGHS
     - 76
     - 28
     - 76
     - 28
   * - 
     - SCS (GPU, cuDSS)
     - 77
     - 36
     - 75
     - 37
   * - 
     - PIQP
     - 63
     - 51
     - 63
     - 51
   * - 
     - SCS (CPU, MKL Pardiso)
     - 71
     - 57
     - 70
     - 63
   * - 
     - Clarabel
     - 68
     - 74
     - 64
     - 86
   * - 
     - PDLP (OR-Tools)
     - 52
     - 139
     - 49
     - 164
   * - 
     - cuOpt (GPU)
     - 25
     - 256
     - 24
     - 265
   * - 
     - OSQP
     - 43
     - 220
     - 32
     - 363
   * - Mittelmann LP set (37)
     - SCS (GPU, cuDSS)
     - 28
     - 208
     - 23
     - 390
   * - 
     - SCS (CPU, MKL Pardiso)
     - 24
     - 431
     - 20
     - 696
   * - 
     - Clarabel
     - 20
     - 817
     - 20
     - 817
   * - 
     - PDLP (OR-Tools)
     - 19
     - 733
     - 14
     - 1226
   * - 
     - PIQP
     - 12
     - 1352
     - 12
     - 1352
   * - 
     - HiGHS
     - 9
     - 2889
     - 9
     - 2889
   * - 
     - cuOpt (GPU)
     - 7
     - 2086
     - 4
     - 3050
