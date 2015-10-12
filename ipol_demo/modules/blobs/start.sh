#!/bin/sh

cd `dirname $0`
nohup python main.py blobs.conf >/dev/null &
