# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

AWS x86 ParallelCluster 3.7.2
-----------------------------

This config should work on any AWS x86 ParallelCluster 3.7.2 instance with the
following caveats:

1) All compute instances must be x86 and EFA enabled. Supported instance types
   can be found here:

   https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html#efa-instance-types

2) Any OS supported by ParallelCluster 3.7.2 should work, but only Amazon
   Linux 2 has been tested

3) ParallelCluster does not install optimized versions of BLAS/LAPACK. This
   config uses the generic versions installed via:

   sudo yum install lapack

3) OpenMPI is the only supported MPI flavor. IntelMPI is not yet supported.

   OpenMPI is running in verbose mode so the user than confirm that EFA is
   being used when running experiments. A line similar to the following in
   slurm-NNN.out confirms EFA is being used:

   mtl_ofi_component.c:362: mtl:ofi:provider: rdmap0s6-rdm 

   This debugging output can be silenced by removing the env variable
   'OMPI_MCA_mtl_base_verbose=100' from the srun line in variables.yaml. 
