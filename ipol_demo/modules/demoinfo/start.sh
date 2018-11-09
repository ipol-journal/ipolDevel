#!/bin/sh

cd `dirname $0`

if [ ! -d "venv" ]; then
  echo "Demoinfo module virtualenv not found, installing..."
  python3 -m virtualenv venv
  ./venv/bin/pip install -r requirements.txt
fi

nohup bash -c "source ./venv/bin/activate && python main.py demoinfo.conf &" >/dev/null &
