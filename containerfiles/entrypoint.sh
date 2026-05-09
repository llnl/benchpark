#!/bin/bash

# Source benchpark environment
source /home/fluxuser/benchpark/setup-env.sh

# Start flux with bash
exec /usr/bin/flux start -s4 /bin/bash
