#!/bin/sh

find_source_files() {
    find . -name '*.py' -size +0 -print | grep -ve './docs' -e 'env' -e './contrib' -e './conftest.py'
}
files=$(find_source_files)
# For now, go through all the checking stages and only die at the end
exit_code=0

if ! flake8; then
    echo "ERROR: flake8 does not pass."
    exit_code=1
fi

fail_coding=false
for file in $(find_source_files); do
    line=$(head -n 1 $file)
    if echo $line | grep -q '#!/usr/bin/env python'; then
        line=$(head -n 2 $file | tail -n 1)
    fi
    if ! echo $line | grep -q '# coding=utf-8'; then
        echo $file
        fail_coding=true
    fi
done
if $fail_coding; then
    echo "ERROR: Above files do not have utf-8 coding declared."
    exit_code=1
fi

# Find files which use the unicode type but (heuristically) don't make it py3
# safe
fail_py3_unicode=false
for file in $(find_source_files); do
    if grep -qle 'unicode(' -e 'class .*(unicode)' $file; then
        if ! grep -L 'unicode = str' $file; then
            fail_py3_unicode=true
        fi
    fi
done
if $fail_py3_unicode; then
    echo "ERROR: Above files use unicode() but do not make it safe for Python 3."
    exit_code=1
fi

exit $exit_code
