#!/bin/bash

python manage.py makemigrations --empty controlpanel && \
python manage.py makemigrations controlpanel && \
python manage.py migrate controlpanel && \
python manage.py migrate && \
python manage.py collectstatic
