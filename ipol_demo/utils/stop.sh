#!/bin/sh
#
# Simple stop script for the ipol demo server.
#
# The PID is expected to be in ./demo.pid 
#
# Copyright 2011 Nicolas Limare <nicolas.limare@cmla.ens-cachan.fr>

if [ "x$BASEDIR" = "x" ]; then
   BASEDIR=${0%/*}
fi
cd $BASEDIR

kill $( cat ./demo.pid ) \
    && rm -f demo.pid \
    && echo "demo stopped" \
    || echo "failed to stop the demo"
