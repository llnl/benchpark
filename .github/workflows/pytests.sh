#!/bin/bash
for file in lib/benchpark/test/*.py; do
    echo "Running tests in $file"
    ./bin/benchpark unit-test "$file"
done
