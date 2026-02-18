// Copyright 2023 Lawrence Livermore National Security, LLC and other
// Benchpark Project Developers. See the top-level COPYRIGHT file for details.
//
// SPDX-License-Identifier: Apache-2.0

#include <iostream>
#include <unistd.h>
#include <mpi.h>
#ifdef USE_CUDA
#include <cuda_runtime.h>
#define MEMALLOC(x, size)            cudaMalloc(&x, size)
#define MEMCOPY(da, ha, size, xmode) cudaMemcpy(da, ha, size, xmode)
#define MEMFREE(da)                  cudaFree(da)
#define HTOD                         cudaMemcpyHostToDevice
#define DTOH                         cudaMemcpyDeviceToHost
#define KERNEL(kernel, dr, dx, dy, n) kernel<<<NB, NT>>>(dr, dx, dy, n)
#define DEVICE __device__
#define GLOBAL __global__
#elif USE_HIP
#include <hip/hip_runtime.h>
#define MEMALLOC(x, size)            hipMalloc(&x, size)
#define MEMCOPY(da, ha, size, xmode) hipMemcpy(da, ha, size, xmode)
#define MEMFREE(da)                  hipFree(da)
#define HTOD     hipMemcpyHostToDevice
#define DTOH     hipMemcpyDeviceToHost
#define KERNEL(kernel, dr, dx, dy, n) hipLaunchKernelGGL(kernel, dim3(NB), dim3(NT), 0, 0, dr, dx, dy, n)
#define DEVICE __device__
#define GLOBAL __global__
#elif USE_OPENMP
#include <omp.h>
#define KERNEL(kernel, dr, dx, dy, n) kernel(dr, dx, dy, n)
#define DEVICE
#define GLOBAL
#else
#define KERNEL(kernel, dr, dx, dy, n) kernel(dr, dx, dy, n)
#define DEVICE
#define GLOBAL
#endif

#ifdef USE_CALIPER
#include <caliper/cali.h>
#include <adiak.h>
#endif

#include "config.hh"

constexpr int NB = 4;
constexpr int NT = 256;

using DTYPE=float;

DEVICE inline DTYPE saxpy(DTYPE xi, DTYPE yi) {
  return 3.14 * xi + yi;
}

#if defined (USE_CUDA) || defined (USE_HIP)
GLOBAL void saxpy_kernel(DTYPE *r, DTYPE *x, DTYPE *y, int size) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid < size) {
        r[tid] = saxpy(x[tid], y[tid]);
    }
}

void kernel_driver(DTYPE *h_r, DTYPE *h_x, DTYPE *h_y, 
                   int N) {
    DTYPE *d_x, *d_y, *d_r;
    size_t nbytes = N * sizeof(DTYPE);

    MEMALLOC(d_x, nbytes);
    MEMALLOC(d_y, nbytes);
    MEMALLOC(d_r, nbytes);

    MEMCOPY(d_x, h_x, nbytes, HTOD);
    MEMCOPY(d_y, h_y, nbytes, HTOD);

    KERNEL(saxpy_kernel, d_r, d_x, d_y, N);

    MEMCOPY(h_r, d_r, nbytes, DTOH);

    MEMFREE(d_x);
    MEMFREE(d_y);
    MEMFREE(d_r);
}
#else
void saxpy_kernel(DTYPE *r, DTYPE *x, DTYPE *y, int size) {
#ifdef USE_OPENMP
    #pragma omp parallel for
#endif
    for (int i = 0; i < size; ++i) {
        r[i] = saxpy(x[i], y[i]);
    }
}

void kernel_driver(DTYPE *h_r, DTYPE *h_x, DTYPE *h_y, 
                   int N) {
    KERNEL(saxpy_kernel, h_r, h_x, h_y, N);
}
#endif

int main(int argc, char** argv) {
    int opt;
    int N = 0;

    MPI_Comm comm = MPI_COMM_WORLD;

    while ((opt = getopt(argc, argv, "n:")) != -1) {
        switch (opt) {
            case 'n':
                N = atoi(optarg);
                fprintf(stdout, "Problem size: %d\n", N);
                break;
            case '?':
                fprintf(stderr, "Unknown option -%c.\n", optopt);
                return 1;
            default:
                return 1;
        }
    }

    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(comm, &rank);
    MPI_Comm_size(comm, &size);

    #ifdef USE_CALIPER
      /*-----------------------------------------------------------
       * Set Caliper and Adiak metadata
       *----------------------------------------------------------*/
      adiak_init(&comm);
      adiak_collect_all();
      adiak_namevalue("compiler", adiak_general, NULL, "%s", SAXPY_COMPILER_ID);
      adiak_namevalue("compiler version", adiak_general, NULL, "%s", SAXPY_COMPILER_VERSION);
      CALI_MARK_BEGIN("main");

      adiak_namevalue("Problem", adiak_general, NULL, "%s", "standard");
      CALI_MARK_BEGIN("problem");
    #endif

    DTYPE *h_x, *h_y, *h_r;

    h_x = new DTYPE[N];
    h_y = new DTYPE[N];
    h_r = new DTYPE[N];

    #ifdef USE_CALIPER
      CALI_MARK_BEGIN("setup");
    #endif
    for (int i = 0; i < N; ++i) {
      h_x[i] = i;
      h_y[i] = i*i;
    }
    #ifdef USE_CALIPER
      CALI_MARK_END("setup");
    #endif

    #ifdef USE_CALIPER
      CALI_MARK_BEGIN("kernel");
    #endif
    kernel_driver(h_r, h_x, h_y, N);
    #ifdef USE_CALIPER
      CALI_MARK_END("kernel");
    #endif

    std::cout << "Kernel done (" << rank << "): " << N << std::endl;

    delete[] h_x;
    delete[] h_y;
    delete[] h_r;

    #ifdef USE_CALIPER
      CALI_MARK_END("problem");

      CALI_MARK_END("main");
      adiak_fini();
    #endif

    MPI_Finalize();
    return 0;
}
