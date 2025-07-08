#!/bin/bash
export JOBID=$(squeue -h --name=${ALLOC_NAME} --format=%A)
([[ -n "${JOBID}" ]] && scancel ${JOBID} || exit 0)