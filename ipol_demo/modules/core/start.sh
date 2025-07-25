#!/bin/sh

cd `dirname $0`

if [ ! -d "venv" ]; then
  echo "Core module virtualenv not found, installing..."
  python3.9 -m virtualenv venv
  ./venv/bin/pip install -r requirements.txt
fi

export IPOL_HOST=$(hostname -f)
export IPOL_URL=http://$(hostname -f)

uvicorn app:app --reload --host 0.0.0.0 --port 8080