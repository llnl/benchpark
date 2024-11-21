#!/bin/bash

compilers=("gcc12" "gccSpack")
optParams=("O2")
scaling=("weak")
. setup-env.sh
benchpark system init --dest=daneTCE rubyExp cluster=dane compiler=gcc
benchpark system init --dest=daneSpack rubyExp cluster=dane compiler=gccSpack
benchpark experiment init --dest=quicksilvergcc12O2weak1 quicksilver experiment=weak caliper=mpi
benchpark setup quicksilvergcc12O2weak1 daneTCE workspace
. workspace/setup.sh
spack install gcc@12.1.0
for runNum in {1..2}
do 
    for j in ${optParams[@]}
    do
        for scale in ${scaling[@]}
        do
            for i in ${compilers[@]}
            do
                #echo $i $j $scale
                benchpark experiment init --dest=quicksilver$i$j$scale$runNum quicksilver experiment=$scale caliper=mpi
                if [ "$i" == "gcc12" ]; then
                    benchpark setup quicksilver$i$j$scale$runNum daneTCE workspace
                    ramble -P -D ./workspace/quicksilver$i$j$scale$runNum/Rubyexp-957b932/workspace workspace setup

                else
                    benchpark setup quicksilver$i$j$scale$runNum daneSpack workspace
                    ramble -P -D ./workspace/quicksilver$i$j$scale$runNum/Rubyexp-fd15164/workspace workspace setup
                fi
            done
        done
    done
done
