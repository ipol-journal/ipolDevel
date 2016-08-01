#!/bin/sh

cd `dirname $0`
nohup python main.py demorunner.conf >/dev/null &
