#!/bin/sh

cd `dirname $0`
nohup python main.py conversion.conf >/dev/null &
