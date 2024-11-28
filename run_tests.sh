#!/bin/bash
set -e

# make sure the binaries are available
which git || (echo "ERROR: git not found" && exit 1)
which envsubst || (echo "ERROR: envsubst not found" && exit 1)
which gira || (echo "ERROR: gira not found" && exit 1)

cd tests
if bash run.sh > /dev/null; then
    echo "Tests passed"
else
    echo "Tests failed"
    exit 1
fi
