#!/bin/bash
set -e

# Activate Virtual Environment
. /usr/workspace/benchpark-dev/benchpark-venv/$SYS_TYPE/bin/activate

# Initialize System
if [ "$HOST" == "lassen" ]; then
    ./bin/benchpark system init --dest=${HOST}-system ${ARCHCONFIG} $SYSTEM_ARGS
else
    ./bin/benchpark system init --dest=${HOST}-system ${ARCHCONFIG} cluster=$HOST $SYSTEM_ARGS
fi

# Initialize Experiment
./bin/benchpark experiment init --dest=${BENCHMARK}-benchmark ${BENCHMARK}${VARIANT}

# Build Workspace
./bin/benchpark setup ${BENCHMARK}-benchmark ${HOST}-system workspace/

# Setup Ramble & Spack
. workspace/setup.sh

# Setup Workspace
cd ./workspace/${BENCHMARK}-benchmark/${HOST}-system/workspace/

ramble --disable-logger --workspace-dir . workspace setup

# Using flux on dane (srun called in "ramble on")
if [ "$HOST" == "dane" ] && \
    # Nightly testing still using slurm
    [ $CI_PIPELINE_SOURCE != "schedule" ]; then
    find . -type f -name execute_experiment -exec sed -i 's/\bsrun\b/flux run --exclusive/g' {} +
fi

# Runs experiments where n_nodes == 1, and Print Log
ramble --disable-logger --workspace-dir . on --executor '{execute_experiment}' --where '{n_nodes} == 1'
find experiments/ -type f -name "*.out" -exec cat {} +

# Analyze Experiments
ramble --disable-logger --workspace-dir . workspace analyze --format json yaml text

cd -

# Benchpark Analyze experiments with "+strong"
if [[ "$VARIANT" == *"+strong"* ]]; then
    ./bin/benchpark analyze --workspace-dir ./workspace/${BENCHMARK}-benchmark/${HOST}-system/workspace/
fi

# Check Experiment Exit Codes
python ./.gitlab/bin/exit-codes ./workspace/${BENCHMARK}-benchmark/${HOST}-system/workspace/results.latest.json