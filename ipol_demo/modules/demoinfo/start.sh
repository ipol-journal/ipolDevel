#!/bin/sh

cd `dirname $0`
# nohup python main.py demoinfo.conf >/dev/null &
nohup bash -c "source ./venv/bin/activate && python main.py demoinfo.conf &" >/dev/null &
