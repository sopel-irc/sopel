#!/bin/bash

set -e

exec 2>&1

READLINK_CMD=$({
    case "${OS_TYPE}" in
        "darwin"*)
            echo "readlink";;
        *)
            echo "readlink -f";;
    esac
})

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
GIT_DIR=${GIT_DIR:-$(git rev-parse --git-dir)}

# Files to link
TO_LINK=("pre-commit" "pre-push" "main-hook.sh")

# Track files that were successfully symlinked
SYMLINKED_FILES=()

symlink_file () {
    [ "$(${READLINK_CMD} ${2})" = "${1}" ] \
        && {
            echo -e "\033[90mSkipping '\033[33m$(basename ${1})\033[90m'... Already linked."
            return 0
        } || true

    echo -ne "\033[32mAdding symbolic link for \033[33m$(basename ${1}) \033[32min hooks folder... "
    (ln -s "${1}" "${2}" 2> /dev/null) \
        && {
            echo -e "\033[92mOK.\033[0m"
            return 0
        } \
        || {
            rc="${?}"
            echo -e '\033[91mFAILED.\033[0m'
            return "${rc}"
        }
}

unlink_file () {
    echo -ne "\033[90mRemoving symbolic link for \033[33m$(basename ${1}) \033[90min from hooks folder... "
    (unlink "${1}") \
        &&  {
            echo -e "\033[90mOK.\033[0m"
        }
}

cleanup_bad () {
    for linked_file in "${SYMLINKED_FILES[@]}"; do
        unlink_file "${linked_file}"
    done
}

echo -e "Setting up Git hooks..."
for file_to_link in "${TO_LINK[@]}"; do
    from_path="${DIR}/${file_to_link}"
    to_path="${GIT_DIR}/hooks/${file_to_link}"

    (symlink_file "${from_path}" "${to_path}") \
        && SYMLINKED_FILES+=("${to_path}") \
        || {
            rc="${?}"
            echo -e "\033[41mUnable to link '\033[33m${file_to_link}\033[0;41m'... Remove existing file '\033[33m${to_path}\033[0;41m' and try again.\033[0m"
            [ "${#SYMLINKED_FILES[@]}" -gt 0 ] \
                && {
                    echo -e "\033[31mUndoing changes made so far...\033[0m"
                    cleanup_bad
                } || true
            exit "${?}"
        }
done

echo -e "\033[42mGit hooks installed successfully.\033[0m"
exit 0
