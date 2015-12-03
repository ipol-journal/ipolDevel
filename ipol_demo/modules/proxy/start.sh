#!/bin/sh

cd `dirname $0`
nohup python main.py proxy.conf >/dev/null &
