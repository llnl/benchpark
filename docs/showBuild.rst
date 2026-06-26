..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

############
 Show Build
############

If you build an experiment with Benchpark, you can see exactly how the experiment was
built.

``` bin/benchpark experiment init --dest=def-raja-perf raja-perf bin/benchpark system
init --dest=def-ruby llnl-cluster cluster=ruby compiler=gcc bin/benchpark setup
def-ruby/def-raja-perf/ workspace/ . `pwd`/workspace/setup.sh ramble --workspace-dir
`pwd`/workspace/def-raja-perf/def-ruby/workspace workspace setup ```

You will now be able to `benchpark show-build dump`, a command that will dump a log of
how Spack built the experiment:

``` bin/benchpark show-build dump
/usr/workspace/scheibel/oslic/benchpark2/workspace/def-raja-perf/def-ruby/workspace/
build-test/ ```

for this example, it will add the following artifacts to `build-test/`

1. `build-raja-perf.log`: a full log of all build commands and their output
2. `extracted-commands.txt`: [1] but with most output filtered out (generally much
   easier to understand what commands to run to do the build)
3. `spack-build-env.txt`: the environment variables set at build time

############################
 Build outside of Benchpark
############################

2 steps to build packages the way Benchpark builds packages without running Benchpark:

1. Use the spack-packages commit that Benchpark uses:

``` git clone https://github.com/llnl/benchpark.git export packages_commit=python -c
"import yaml;
print(yaml.safe_load(open('benchpark/checkout-versions.yaml'))['versions']['spack-packages'])"
git clone https://github.com/spack/spack-packages.git pushd spack-packages && git
checkout $packages_commit $$ $ popd ```

2. Layer Benchpark's dedicated package repo on top:

``` spack repo add spack-packages/repos/spack_repo/builtin/ spack repo add
benchpark/repos/spack_repo/benchpark/ ```
