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
     - 38
     - 10
     - 37
     - 11
   * - 
     - SCS (GPU, cuDSS)
     - 40
     - 8
     - 38
     - 12
   * - 
     - PIQP
     - 35
     - 17
     - 35
     - 17
   * - 
     - cuOpt (GPU)
     - 32
     - 20
     - 32
     - 20
   * - 
     - SCS (CPU, MKL Pardiso)
     - 37
     - 16
     - 34
     - 23
   * - 
     - OSQP
     - 32
     - 30
     - 31
     - 37
   * - 
     - HiGHS
     - 17
     - 259
     - 13
     - 302
   * - 
     - ProxQP
     - 12
     - 342
     - 12
     - 353
   * - Kennington and MIPLIB-relaxation LPs, largest quartile (88)
     - SCS (GPU, cuDSS)
     - 82
     - 20
     - 78
     - 28
   * - 
     - HiGHS
     - 73
     - 33
     - 73
     - 33
   * - 
     - SCS (CPU, MKL Pardiso)
     - 79
     - 38
     - 74
     - 51
   * - 
     - PIQP
     - 63
     - 52
     - 63
     - 52
   * - 
     - Clarabel
     - 74
     - 58
     - 70
     - 70
   * - 
     - PDLP (OR-Tools)
     - 52
     - 137
     - 49
     - 165
   * - 
     - cuOpt (GPU)
     - 27
     - 231
     - 20
     - 324
   * - 
     - OSQP
     - 46
     - 218
     - 32
     - 349
   * - Mittelmann LP set (37)
     - SCS (GPU, cuDSS)
     - 29
     - 152
     - 25
     - 276
   * - 
     - SCS (CPU, MKL Pardiso)
     - 24
     - 361
     - 21
     - 580
   * - 
     - Clarabel
     - 21
     - 693
     - 21
     - 693
   * - 
     - PDLP (OR-Tools)
     - 19
     - 738
     - 14
     - 1232
   * - 
     - PIQP
     - 12
     - 1332
     - 12
     - 1332
   * - 
     - cuOpt (GPU)
     - 8
     - 1748
     - 5
     - 2572
   * - 
     - HiGHS
     - 9
     - 2947
     - 9
     - 2947
