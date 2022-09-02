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

cargo install --git https://github.com/kidanger/ipol-demorunner.git --rev 2bb39ccd8193178055ee6802a702061dd6227666 --root . --target-dir target --debug --force --locked

export ROCKET_PROFILE=ipol-$(hostname)
bin/ipol-demorunner >logs 2>&1 &
