#!/bin/sh

find_source_files() {
    find . -name '*.py' -size +0 -print | grep -ve './docs' -e 'env' -e './contrib' -e './conftest.py'
}
files=$(find_source_files)
# These are acceptable (for now). 128 and 127 should be removed eventually.
ignore='--ignore=E501,E128,E127'
# These are ignored by default (and we want to keep them ignored)
ignore=$ignore',W504'
# These are forbidding certain __future__ imports. The plugin has errors both
# for having and not having them; we want to always have them, so we ignore
# the having them errors and keep the not having them errors.
ignore=$ignore',FI50,FI51,FI52,FI53,FI54,FI55'
# F12 is with_statement, which is already in 2.7. F15 requires and F55 forbids
# generator_stop, which should probably be made mandatory at some point.
ignore=$ignore',F12,F15,F55'
# These are rules that are relatively new or have had their definitions tweaked
# recently, so we'll forgive them until versions of PEP8 in various developers'
# distros are updated
ignore=$ignore',E265,E713,E111,E113,E402,E731'
# For now, go through all the checking stages and only die at the end
exit_code=0

if ! flake8 $ignore --filename=*.py $(find_source_files); then
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
