#!/bin/bash

system_spec="$1"
benchmark_spec="$2"

timestamp=$(date +%s)
benchmark="b-$timestamp"
system="s-$timestamp"
./bin/benchpark system init --dest=$system $system_spec
./bin/benchpark experiment init --dest=$benchmark $benchmark_spec
./bin/benchpark setup ./$benchmark ./$system workspace/
. workspace/setup.sh
ramble \
    --workspace-dir "workspace/$benchmark/$system/workspace" \
    --disable-progress-bar \
    --disable-logger \
    workspace setup --dry-run