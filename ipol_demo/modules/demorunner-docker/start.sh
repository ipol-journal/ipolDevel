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

cargo install --git https://github.com/ipol-journal/ipol-demorunner.git --rev 7bf38a4cb007ea1113ba6a08f133d3c217a405fa --root . --target-dir target --debug --force --locked

export ROCKET_PROFILE=ipol-$(hostname)
bin/ipol-demorunner >logs 2>&1 &
