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

# Files to unlink
TO_LINK=("pre-commit" "pre-push" "main-hook.sh")

# Track removed files
REMOVED_FILES=()

unlink_hook () {
    hook_file="${GIT_DIR}/hooks/${1}"
    orig_file="${DIR}/${1}"

    [ "$(${READLINK_CMD} ${hook_file})" = "${orig_file}" ] \
        && {
            echo -ne "\033[32mRemoving symbolic link for \033[33m${1} \033[32mfrom hooks folder... \033[0m"
            unlink "${hook_file}" && echo -e "\033[92mOK.\033[0m"
        } \
        || {
            rc="${?}"
            echo -e "\033[90mSkipping '\033[33m${1}\033[90m'... not found in hooks folder, or not a symlink.\033[0m"
            return "${rc}"
        }

}

echo -e "Removing Git hooks..."
for file_to_unlink in "${TO_LINK[@]}"; do
    unlink_hook "${file_to_unlink}" \
        && REMOVED_FILES+=("${file_to_unlink}") \
        || true
done

[ "${#REMOVED_FILES[@]}" -gt "0" ] \
    && echo -e "\033[42mGit hooks uninstalled successfully.\033[0m" \
    || echo -e "No installed hooks found."

exit 0
