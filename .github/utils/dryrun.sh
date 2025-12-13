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
./bin/benchpark experiment init --dest=$benchmark $system $benchmark_spec
./bin/benchpark setup ./$system/$benchmark workspace/
. workspace/setup.sh
ramble \
    --workspace-dir "workspace/$system/$benchmark/workspace" \
    --disable-logger \
    workspace setup --dry-run