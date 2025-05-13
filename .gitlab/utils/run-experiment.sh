#!/bin/bash

# Activate Virtual Environment
source /usr/workspace/benchpark-dev/benchpark-venv/$SYS_TYPE/bin/activate

# Initialize System
EXTRA_ARGS=""
if [ "$HOST" == "tioga" ]; then
    EXTRA_ARGS="~gtl"
fi

if [ "$HOST" == "lassen" ]; then
    ./bin/benchpark system init --dest="${HOST}-system" ${ARCHCONFIG} $EXTRA_ARGS  # llnl-sierra has no 'cluster'
else
    ./bin/benchpark system init --dest="${HOST}-system" ${ARCHCONFIG} cluster="$HOST" $EXTRA_ARGS
fi

# Initialize Experiment
./bin/benchpark experiment init --dest="${BENCHMARK}-benchmark" "${BENCHMARK}${VARIANT}"

# Build Workspace
./bin/benchpark setup "${BENCHMARK}-benchmark" "${HOST}-system" /dev/shm/workspace/

# Setup Ramble & Spack
source /dev/shm/workspace/setup.sh

# Setup Workspace
cd /dev/shm/workspace/${BENCHMARK}-benchmark/${HOST}-system/workspace/
ramble --workspace-dir . --disable-progress-bar --disable-logger workspace setup

# Run Experiments
ramble --workspace-dir . --disable-progress-bar --disable-logger on --executor \
  '{execute_experiment}' --where '{n_nodes} == 1'

# Analyze Experiments
ramble --workspace-dir . --disable-progress-bar workspace analyze --format json yaml text

# Check Experiment Exit Codes
cd -
python ./.gitlab/bin/exit-codes /dev/shm/workspace/${BENCHMARK}-benchmark/${HOST}-system/workspace/results.latest.json