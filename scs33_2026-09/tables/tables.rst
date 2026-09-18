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
     - 152
     - 3.1
     - 37
     - 12.6
     - 148
     - 4.4
     - 34
     - 19.5
   * - PIQP
     - 150
     - 3.7
     - 34
     - 18.3
     - 150
     - 3.7
     - 34
     - 18.3
   * - SCS (GPU, cuDSS)
     - 146
     - 6.3
     - 38
     - 9.4
     - 140
     - 12.2
     - 33
     - 26.1
   * - SCS (CPU, MKL Pardiso)
     - 144
     - 7.5
     - 38
     - 12.8
     - 138
     - 11.4
     - 33
     - 28.8
   * - OSQP
     - 138
     - 10.9
     - 32
     - 29.4
     - 121
     - 27.2
     - 30
     - 41.8
   * - cuOpt (GPU)
     - 109
     - 33.8
     - 32
     - 22.4
     - 103
     - 39.6
     - 27
     - 37.1
   * - HiGHS
     - 100
     - 48.0
     - 13
     - 268.1
     - 84
     - 79.1
     - 11
     - 323.6
   * - ProxQP
     - 98
     - 67.9
     - 12
     - 346.3
     - 84
     - 88.9
     - 12
     - 348.0

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
     - 336
     - 5.0
     - 76
     - 28.2
     - 336
     - 5.0
     - 76
     - 28.2
   * - PIQP
     - 316
     - 9.3
     - 63
     - 51.5
     - 310
     - 10.6
     - 63
     - 51.5
   * - Clarabel
     - 324
     - 10.5
     - 68
     - 73.5
     - 312
     - 13.4
     - 63
     - 88.9
   * - SCS (GPU, cuDSS)
     - 320
     - 11.3
     - 77
     - 35.6
     - 303
     - 17.0
     - 70
     - 48.6
   * - SCS (CPU, MKL Pardiso)
     - 316
     - 11.9
     - 71
     - 56.5
     - 295
     - 19.9
     - 61
     - 84.7
   * - PDLP (OR-Tools)
     - 292
     - 24.5
     - 52
     - 139.0
     - 263
     - 38.6
     - 40
     - 221.3
   * - OSQP
     - 257
     - 42.2
     - 43
     - 220.1
     - 174
     - 131.9
     - 21
     - 474.3
   * - cuOpt (GPU)
     - 219
     - 45.7
     - 25
     - 255.6
     - 204
     - 56.9
     - 20
     - 322.6

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
     - 38.2
     - 21
     - 38.6
   * - CVXOPT
     - 76
     - 52.4
     - 18
     - 111.5
   * - Clarabel
     - 71
     - 68.9
     - 13
     - 257.0
   * - SCS (CPU, MKL Pardiso)
     - 77
     - 107.5
     - 14
     - 1090.7
   * - SCS (GPU, cuDSS)
     - 73
     - 146.5
     - 9
     - 1531.0

