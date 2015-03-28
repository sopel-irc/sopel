#!/bin/sh

find_source_files() {
    find . -name '*.py' -size +0 -print | grep -ve './docs' -e './contrib' -e './conftest.py'
}
files=$(find_source_files)
# These are acceptable (for now). 128 and 127 should be removed eventually.
ignore='--ignore=E501,E128,E127'
# These are rules that are relatively new or have had their definitions tweaked
# recently, so we'll forgive them until versions of PEP8 in various developers'
#distros are updated
ignore=$ignore',E265,E713,E111,E113,E402,E731'
# For now, go through all the checking stages and only die at the end
exit_code=0

if ! pep8 $ignore --filename=*.py $(find_source_files); then
    echo "ERROR: PEP8 does not pass."
    exit_code=1
fi

fail_coding=false
for file in $(find_source_files); do
    line=$(head -n 1 $file)
    if echo $line | grep -q '#!/usr/bin/env python'; then
        line=$(head -n 2 $file | tail -n 1)
    fi
    if ! echo $line | grep -q '# coding=utf8'; then
        echo $file
        fail_coding=true
    fi
done
if $fail_coding; then
    echo "ERROR: Above files do not have utf8 coding declared."
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

check_future () {
    fail_unicode_literals=false
    for file in $files; do
        if ! grep -L "from __future__ import $1" $file; then
            fail_unicode_literals=true
        fi
    done
    if $fail_unicode_literals; then
        if $2; then
            echo "ERROR: Above files do not have $1 import."
            exit_code=1
        else
            echo "WARNING: Above files do not have $1 import."
        fi
    fi
}
for mandatory in unicode_literals
do
    check_future $mandatory true
done
for optional in division print_function absolute_import
do
    check_future $optional false
done

exit $exit_code
