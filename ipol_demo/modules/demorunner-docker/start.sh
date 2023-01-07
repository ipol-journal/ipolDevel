#!/usr/bin/env bash

set -eux

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPTPATH

if [ -f $HOME/.cargo/env ]; then
    source $HOME/.cargo/env
fi

if ! command -v cargo &> /dev/null; then
    echo "cargo is required to launch demorunner-docker" >&2
    echo "see https://rustup.rs/" >&2
    exit 1
fi

cargo install --git https://github.com/ipol-journal/ipol-demorunner.git --rev cf4dce8a406580964dbea58a77b0d780b3878656 --root . --target-dir target --debug --force --locked

export ROCKET_PROFILE=ipol-$(hostname)
bin/ipol-demorunner >logs 2>&1 &
