#!/bin/bash
# Run from benchpark root '. examples/compareExperimentRuns.sh'

compilers=("gcc12" "intel")
optParams=("O2")
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
    for j in ${optParams[@]}
    do
        for scale in ${scaling[@]}
        do
            for i in ${compilers[@]}
            do
                echo $i $j $scale
                # Setup specific experiment
                benchpark experiment init --dest=quicksilver$i$j$scale$runNum quicksilver +$scale +openmp ~single_node caliper=mpi
                if [ "$i" == "gcc12" ]; then
                    benchpark setup quicksilver$i$j$scale$runNum daneGCC workspace
                    . workspace/setup.sh
                    ramble --workspace-dir workspace/quicksilver$i$j$scale$runNum/daneGCC/workspace workspace setup
                    ramble --workspace-dir workspace/quicksilver$i$j$scale$runNum/daneGCC/workspace on
                else
                    benchpark setup quicksilver$i$j$scale$runNum daneIntel workspace
                    . workspace/setup.sh
                    ramble --workspace-dir workspace/quicksilver$i$j$scale$runNum/daneIntel/workspace workspace setup
                    ramble --workspace-dir workspace/quicksilver$i$j$scale$runNum/daneIntel/workspace on
                fi
            done
        done
    done
done
