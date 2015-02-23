#!/bin/sh
#
# git post-update hook

set -e
set -x

# use ccache if available
export PATH="/usr/lib/ccache:$PATH"
export CCACHE_DIR=/srv/ipol/ccache

# system init script for the demo
INITSCRIPT=/etc/init.d/ipol-demo

# folders should be group-writable
umask 0002

# stop the service
sudo $INITSCRIPT stop
# update the source
git reset --hard
git clean -fd
# start the service
sudo $INITSCRIPT start
