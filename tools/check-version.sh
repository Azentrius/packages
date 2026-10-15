#!/bin/sh
# The version lives in VERSION (the version of azentrius-repository). It must be a version like
# 1.0.0, and CHANGELOG.md needs a section for it. Prints the version; exit 1 when anything is off.
# SPDX-License-Identifier: Apache-2.0
set -eu
cd "$(dirname "$0")/.."
v=$(tr -d ' \n' < VERSION)
if ! printf '%s\n' "$v" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.]+)?$'; then
    echo "VERSION \"$v\" is not a version like 1.0.0" >&2
    exit 1
fi
if ! sh tools/release-notes.sh "$v" > /dev/null; then
    echo "CHANGELOG.md has no section for $v" >&2
    exit 1
fi
echo "$v"
