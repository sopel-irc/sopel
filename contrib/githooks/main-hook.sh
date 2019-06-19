#!/bin/bash

set -e

_GIT_COMMAND=${_GIT_COMMAND:-"hook test"}

# Redirect stdout to stderr
exec 1>&2

# Track whether stash was set
STASH_SET=0

# Trap to clean up nicely
trap "{ do_exit 130; }" SIGINT SIGTERM

setup () {
    # Stash any changes that are not getting committed.
    case "$(git status)" in
        *"Changes not staged for commit"*)
            echo -ne '\033[90mFound unstaged changes. Stashing... \033[0m'
            (git stash --keep-index > /dev/null) \
                && {
                    STASH_SET=1
                    echo -e '\033[90mOK.\033[0m'
                }
            ;;
    esac
}

cleanup () {
    [ "${STASH_SET}" -eq "1" ] \
        && {
            echo -ne '\033[90mPutting back stashed changes... \033[0m'
            (git stash pop > /dev/null) \
                && echo -e '\033[90mOK.\033[0m'
        } || true
}

do_exit () {
    cleanup
    exit "${1}"
}

# Start hook
setup

# Decide which parts of the hook will run
RUN_CHECKSTYLE=$([ "${SKIP_CHECKSTYLE}" = "1" ] && echo "0" || echo "1")
RUN_PYTEST=$([ "${SKIP_PYTEST}" = "1" ] && echo "0" || echo "1")

# ./checkstyle first
[ "${RUN_CHECKSTYLE}" -eq "1" ] \
    && {
        echo -ne "\033[32mRunning \033[33mcheckstyle.sh \033[32mbefore ${_GIT_COMMAND}... \033[0m"

        cs_output=$(./checkstyle.sh)
        cs="${?}"
        if [ "${cs}" -ne "0" ]; then
            echo -e '\033[91mFAILED.\033[0m'
            echo "${cs_output}"
            do_exit "${cs}"
        fi

        echo -e '\033[92mOK.\033[0m'
    } || true

# pytest
[ "${RUN_PYTEST}" -eq "1" ] \
    && {
        echo -e "\033[32mRunning \033[33mpytest_run.py \033[32mbefore ${_GIT_COMMAND}... \033[0m"

        python pytest_run.py
        pt="${?}"
        if [ "${pt}" -ne "0" ]; then
            echo -e '\033[91mFAILED.\033[0m'
            do_exit "${pt}"
        fi

        echo -e '\033[92mOK.\033[0m'
    } || true

# All parts OK (or skipped)
do_exit 0