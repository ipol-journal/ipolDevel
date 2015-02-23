#!/bin/sh
#
# Simple start script for the ipol demo server.
#
# The demo script is expected to be in ./demo/demo.py. The process is
# forked to the background, and the PID is stored in ./demo.pid 
#
# Copyright 2011 Nicolas Limare <nicolas.limare@cmla.ens-cachan.fr>

if [ "x$BASEDIR" = "x" ]; then
   BASEDIR=${0%/*}
fi
cd $BASEDIR

./demo/demo.py build
./demo/demo.py 1> ./demo.stdout 2> ./demo.stderr &
PID=$!
sleep 1
if [ "x$PID" != "x" -a -d /proc/$PID ]; then
    echo $PID > ./demo.pid
    echo "demo started"
else
    echo "failed to start the demo"
fi
