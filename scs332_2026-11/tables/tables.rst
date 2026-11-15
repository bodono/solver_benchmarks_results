.. list-table:: QP: verified solves and shifted geometric mean time (s); all 157 problems / largest quartile (40)
   :header-rows: 1
   :widths: 26 12 12 12 12 12 12 12 12

   * - Solver
     - solved 1e-4
     - gm 1e-4
     - solved 1e-4 (largest)
     - gm 1e-4 (largest)
     - solved 1e-6
     - gm 1e-6
     - solved 1e-6 (largest)
     - gm 1e-6 (largest)
   * - Clarabel
     - 153
     - 2.7
     - 38
     - 10.2
     - 148
     - 4.1
     - 34
     - 17.2
   * - PIQP
     - 151
     - 3.5
     - 35
     - 16.7
     - 151
     - 3.5
     - 35
     - 16.7
   * - SCS (GPU, cuDSS)
     - 148
     - 6.3
     - 40
     - 7.8
     - 141
     - 10.5
     - 34
     - 21.2
   * - SCS (CPU, MKL Pardiso)
     - 144
     - 7.7
     - 37
     - 15.9
     - 141
     - 9.5
     - 33
     - 23.5
   * - OSQP
     - 138
     - 10.9
     - 32
     - 29.6
     - 121
     - 27.8
     - 30
     - 42.6
   * - cuOpt (GPU)
     - 109
     - 32.8
     - 32
     - 19.9
     - 104
     - 38.0
     - 28
     - 32.2
   * - HiGHS
     - 107
     - 47.0
     - 17
     - 258.9
     - 84
     - 81.5
     - 10
     - 355.9
   * - ProxQP
     - 94
     - 73.5
     - 12
     - 342.2
     - 83
     - 92.0
     - 12
     - 352.9

.. list-table:: LP: verified solves and shifted geometric mean time (s); all 349 problems / largest quartile (88)
   :header-rows: 1
   :widths: 26 12 12 12 12 12 12 12 12

   * - Solver
     - solved 1e-4
     - gm 1e-4
     - solved 1e-4 (largest)
     - gm 1e-4 (largest)
     - solved 1e-6
     - gm 1e-6
     - solved 1e-6 (largest)
     - gm 1e-6 (largest)
   * - HiGHS
     - 333
     - 5.6
     - 73
     - 32.6
     - 333
     - 5.6
     - 73
     - 32.6
   * - SCS (GPU, cuDSS)
     - 334
     - 6.3
     - 82
     - 19.6
     - 318
     - 12.3
     - 76
     - 36.5
   * - SCS (CPU, MKL Pardiso)
     - 330
     - 8.4
     - 79
     - 37.7
     - 313
     - 14.4
     - 68
     - 65.7
   * - Clarabel
     - 330
     - 8.9
     - 74
     - 58.4
     - 316
     - 12.0
     - 68
     - 73.2
   * - PIQP
     - 317
     - 9.4
     - 63
     - 51.8
     - 311
     - 10.7
     - 63
     - 51.8
   * - PDLP (OR-Tools)
     - 291
     - 24.6
     - 52
     - 136.6
     - 262
     - 38.9
     - 40
     - 222.4
   * - cuOpt (GPU)
     - 230
     - 38.7
     - 27
     - 230.7
     - 207
     - 54.7
     - 18
     - 358.6
   * - OSQP
     - 258
     - 42.5
     - 46
     - 218.1
     - 173
     - 132.0
     - 20
     - 469.0

.. list-table:: SDP: verified solves and shifted geometric mean time (s); all 94 problems / largest quartile (24)
   :header-rows: 1
   :widths: 26 12 12 12 12

   * - Solver
     - solved 1e-4
     - gm 1e-4
     - solved 1e-4 (largest)
     - gm 1e-4 (largest)
   * - SDPA
     - 75
     - 34.7
     - 20
     - 45.5
   * - CVXOPT
     - 76
     - 46.6
     - 19
     - 86.9
   * - Clarabel
     - 71
     - 63.2
     - 12
     - 283.7
   * - SCS (CPU, MKL Pardiso)
     - 83
     - 63.8
     - 19
     - 404.5
   * - SCS (GPU, cuDSS)
     - 83
     - 83.5
     - 18
     - 624.8

