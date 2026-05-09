#!/bin/bash
# Run from benchpark root '. docs/examples/compare_experiment_builds/compareExperimentBuilds.sh'

compilers=("gcc12" "intel")
scaling=("weak")
. setup-env.sh
rm -rf daneGCC
rm -rf daneIntel
rm -rf quicksilvergcc*
benchpark system init --dest=daneGCC llnl-cluster cluster=dane compiler=gcc
benchpark system init --dest=daneIntel llnl-cluster cluster=dane compiler=intel
# Set up all experiments
for runNum in {1..3}
do 
    for scale in ${scaling[@]}
    do
        for i in ${compilers[@]}
        do
            echo $i $scale
            # Setup specific experiment
            benchpark experiment init --dest=quicksilver$i$scale$runNum quicksilver +$scale +openmp caliper=mpi
            if [ "$i" == "gcc12" ]; then
                benchpark setup daneGCC/quicksilver$i$scale$runNum workspace
                . workspace/setup.sh
                ramble --workspace-dir workspace/quicksilver$i$scale$runNum/daneGCC/workspace workspace setup
                ramble --workspace-dir workspace/quicksilver$i$scale$runNum/daneGCC/workspace on
            else
                benchpark setup daneIntel/quicksilver$i$scale$runNum workspace
                . workspace/setup.sh
                ramble --workspace-dir workspace/quicksilver$i$scale$runNum/daneIntel/workspace workspace setup
                ramble --workspace-dir workspace/quicksilver$i$scale$runNum/daneIntel/workspace on
            fi
        done
    done
done
