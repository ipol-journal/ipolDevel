#!/bin/bash
cd /home/ipol/ipolDevel/ipol_webapp && \
python manage.py makemigrations --empty controlpanel && \
python manage.py makemigrations controlpanel && \
python manage.py migrate controlpanel && \
python manage.py migrate && \
python manage.py collectstatic

cd /home/ipol/ipolDevel/cp2 && \
python3 -m virtualenv cp2 && \
source cp2/bin/activate && \
pip3 install -r requirements.txt && \
cd ControlPanel && python3 manage.py migrate && deactivate