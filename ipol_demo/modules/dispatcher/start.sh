#!/bin/sh

cd `dirname $0`
nohup python main.py dispatcher.conf >/dev/null &
