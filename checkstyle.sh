#!/bin/sh

# For now, go through all the checking stages and only die at the end
exit_code=0

if ! flake8; then
    echo "ERROR: flake8 does not pass."
    exit_code=1
fi

exit $exit_code
