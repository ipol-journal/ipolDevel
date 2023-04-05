#!/bin/sh

cd `dirname $0`

if [ ! -d "venv" ]; then
  echo "Archive module virtualenv not found, installing..."
  python3 -m virtualenv venv
  ./venv/bin/pip install -r requirements.txt
fi

export IPOL_HOST=$(hostname -f)
export IPOL_URL=http://$(hostname -f)

# TODO modify host IP to integration and prod. Port is ok already
uvicorn archive:app --reload --host 0.0.0.0 --port 9000
