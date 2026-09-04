#!/bin/bash
set -e

TEST_STATUS_FILE="${CI_PROJECT_DIR}/test_status.txt"

# Activate Virtual Environment
. /usr/workspace/benchpark-dev/benchpark-venv/$SYS_TYPE/bin/activate

echo "./bin/benchpark system init --dest=${HOST} ${ARCHCONFIG} $([ "$HOST" != "matrix" ] && echo "cluster=$HOST") $SYSTEM_ARGS"
echo "./bin/benchpark experiment init --dest=${BENCHMARK} ${HOST} ${BENCHMARK} ${VARIANT}"
echo "./bin/benchpark setup ${HOST}/${BENCHMARK} wkp/"
echo ". wkp/setup.sh"
echo "cd ./wkp/${HOST}/${BENCHMARK}/workspace/"
echo "ramble --disable-logger --workspace-dir . workspace setup"
echo "ramble --disable-logger --workspace-dir . on --executor '{execute_experiment}' --where '{n_nodes} == 1'"
echo "ramble --disable-logger --workspace-dir . workspace analyze --format json yaml text"

printf 'Build\n' > "${TEST_STATUS_FILE}"

# Ensure proper bootstrap location configured
./bin/benchpark configure --bootstrap-location $CUSTOM_CI_BUILDS_DIR

# Initialize System
./bin/benchpark system init --dest=${HOST} ${ARCHCONFIG} $([ "$HOST" != "matrix" ] && echo "cluster=$HOST") $SYSTEM_ARGS

# Initialize Experiment
BV=""
if [[ -n "$BENCHMARK_VERSION" ]]; then
    BV="version=$BENCHMARK_VERSION"
fi
./bin/benchpark experiment init --dest=${BENCHMARK} ${HOST} ${BENCHMARK} ${VARIANT} ${BV}

# Build Workspace
./bin/benchpark setup ${HOST}/${BENCHMARK} wkp/

# Setup Ramble & Spack
. wkp/setup.sh

# Setup Workspace
cd ./wkp/${HOST}/${BENCHMARK}/workspace/

ramble --disable-logger --workspace-dir . workspace setup

# Using flux on dane (srun called in "ramble on")
if [ "$HOST" == "dane" ] && \
    # Nightly testing still using slurm
    [ $CI_PIPELINE_SOURCE != "schedule" ]; then
    find . -type f -name execute_experiment -exec sed -i 's/\bsrun\b/flux run --exclusive/g' {} +
fi

# Runs experiments where n_nodes == 1, and Print Log
printf 'Run\n' > "${TEST_STATUS_FILE}"
ramble --disable-logger --workspace-dir . on --executor '{execute_experiment}' --where '{n_nodes} == 1'
find experiments/ -type f -name "*.out" -exec cat {} +
# Fail if log files are empty or don't exist
find experiments/ -type f -name "*.out" | grep -q . || { echo "No .out files found"; exit 1; }; find experiments/ -type f -name "*.out" -empty -print -quit | grep -q . && { echo "Empty .out file found"; exit 1; }

# Analyze Experiments
ramble --disable-logger --workspace-dir . workspace analyze --format json yaml text

cd -

# Test 'benchpark analyze' 
if [[ "$TEST_ANALYZE" == "true" ]]; then
    ./bin/benchpark analyze --workspace-dir ./wkp/${HOST}/${BENCHMARK}/workspace/
fi

# Check Experiment Exit Codes
python ./.gitlab/bin/exit-codes ./wkp/${HOST}/${BENCHMARK}/workspace/results.latest.json

printf 'Pass\n' > "${TEST_STATUS_FILE}"
