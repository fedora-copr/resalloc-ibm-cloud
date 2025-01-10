#! /bin/bash

# Execute scripts directly from git.

base=$(basename "$0")
base=${base//resalloc-/}
base=${base//-/_}
file="resalloc_ibm_cloud/$base.py"

die() { echo >&2 "fatal: $*"; exit 1; }

cd "$(dirname "$(readlink -f "$0")")" || exit 1

test -e "$file" || die "$file not found"

echo >&2 "WARNING: You run the command from Git repo, debugging only (no support)!"
exec python3 -c "from resalloc_ibm_cloud.$base import main; import sys; sys.argv[0] = '$0'; main()" "$@"
