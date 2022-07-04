#!/bin/sh

cd `dirname $0`

if [ ! -d "venv" ]; then
  echo "Demoinfo module virtualenv not found, installing..."
  python3 -m virtualenv venv
  ./venv/bin/pip install -r requirements.txt
fi

export IPOL_HOST=$(hostname -f)
export IPOL_URL=http://$(hostname -f)

nohup bash -c "source ./venv/bin/activate && python main.py demoinfo.conf &" >/dev/null &
