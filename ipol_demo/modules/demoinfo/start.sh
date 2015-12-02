#!/bin/sh

cd `dirname $0`
nohup python main.py demoinfo.conf >/dev/null &
