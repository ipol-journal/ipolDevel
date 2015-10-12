#!/bin/sh

cd `dirname $0`
nohup python main.py archive.conf >/dev/null &
