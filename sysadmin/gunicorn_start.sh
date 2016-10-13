#!/bin/bash

NAME="ipol_webapp"                                  # Name of the application
DJANGODIR=/home/ipol/ipolDevel/ipol_webapp             # Django project directory
SOCKFILE=/home/ipol/ipolDevel/ipol_webapp/run/gunicorn.sock  # we will communicte using this unix socket
#VENV=venv                                        # virtual environment directory

USER=ipol                                       # the user to run as
GROUP=ipol                                     # the group to run as

NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=ipol_webapp.settings             # which settings file should Django use
DJANGO_WSGI_MODULE=ipol_webapp.wsgi                     # WSGI module name


echo "*** Starting $NAME as `whoami` with group $GROUP ***"

# Activate the virtual environment
cd $DJANGODIR
#source ../$VENV/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

#Collect static files for app
python manage.py collectstatic --noinput

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
echo "*** Starting gunicorn ***"
exec gunicorn -b 0.0.0.0:8001 ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-

# (venv) mini:ipol_webapp martin$ gunicorn -b 127.0.0.1:8003 ipol_webapp.wsgi