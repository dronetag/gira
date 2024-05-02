#!/bin/bash
set -e

# make sure the binaries are available
which git
which envsubst
which gira

cd tests
if bash run.sh > /dev/null; then
    echo "Tests passed"
else
    echo "Tests failed"
    exit 1
fi
