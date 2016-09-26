#!/bin/sh

cd `dirname $0`
nohup python main.py core.conf >/dev/null &
