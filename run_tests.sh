#!/bin/bash
set -e

# make sure the binaries are available
which git
which envsubst
which gira

cd tests
. run.sh
