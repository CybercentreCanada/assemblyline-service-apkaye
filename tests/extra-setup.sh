#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

mkdir -p /usr/share/man/man1
chmod +x "${SCRIPT_DIR}/../setup_support.sh" && "${SCRIPT_DIR}/../setup_support.sh"
