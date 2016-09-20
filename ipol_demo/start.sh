#!/bin/sh

cd `dirname $0`
nohup python demo.py demo.conf >/dev/null &
