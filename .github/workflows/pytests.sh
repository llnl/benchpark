#!/bin/bash
for file in lib/benchpark/test/*.py; do
    filename="$(basename "$file")"
    if [[ "$filename" == "__init__.py" ]] || [[ "$filename" == "conftest.py" ]]; then
        continue
    fi
    echo "Running tests in $file"
    ./bin/benchpark unit-test "$file"
done