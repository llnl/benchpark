# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

#!/bin/bash

benchmark_spec="$1"
system_spec="$2"

timestamp=$(date +%s)
benchmark="b-$timestamp"
system="s-$timestamp"
./bin/benchpark system init --dest=$system $system_spec
./bin/benchpark experiment init --dest=$benchmark $benchmark_spec
./bin/benchpark setup ./$benchmark ./$system workspace/
. workspace/setup.sh
ramble \
    --workspace-dir "workspace/$benchmark/$system/workspace" \
    --disable-logger \
    workspace setup --dry-run