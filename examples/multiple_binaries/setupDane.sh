#!/bin/bash
# Run from benchpark root '. examples/multiple_binaries/setupDane.sh'

compilers=("gcc12" "intel")
optParams=("O2")
scaling=("weak")
. setup-env.sh
rm -rf daneGCC
rm -rf daneIntel
rm -rf quicksilvergcc*
benchpark system init --dest=daneGCC llnl-cluster cluster=dane compiler=gcc
benchpark system init --dest=daneIntel llnl-cluster cluster=dane compiler=intel
benchpark experiment init --dest=quicksilvergcc12O2weak1 quicksilver +weak
benchpark setup quicksilvergcc12O2weak1 daneGCC workspace
. workspace/setup.sh
for runNum in {1..5}
do 
    for j in ${optParams[@]}
    do
        for scale in ${scaling[@]}
        do
            for i in ${compilers[@]}
            do
                echo $i $j $scale
                # Setup specific experiment
                benchpark experiment init --dest=quicksilver$i$j$scale$runNum quicksilver +$scale
                if [ "$i" == "gcc12" ]; then
                    benchpark setup quicksilver$i$j$scale$runNum daneGCC workspace
                    ramble -P -D ./workspace/quicksilver$i$j$scale$runNum/daneGCC/workspace workspace setup

                else

                    benchpark setup quicksilver$i$j$scale$runNum daneIntel workspace
                    ramble -P -D ./workspace/quicksilver$i$j$scale$runNum/daneIntel/workspace workspace setup
                fi
            done
        done
    done
done
