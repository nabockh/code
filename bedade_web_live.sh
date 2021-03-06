#!/bin/bash
 
NAME="bedade_web"                                  # Name of the application
DJANGODIR=/webapps/bedade/bedade             # Django project directory
SOCKFILE=/webapps/bedade/bedade/run/gunicorn.sock  # we will communicte using this unix socket
USER=bedade                                        # the user to run as
GROUP=webapps                                     # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=app.settings             # which settings file should Django use
DJANGO_WSGI_MODULE=app.wsgi                     # WSGI module name
NEW_RELIC_CONFIG_FILE=/webapps/bedade/bedade/newrelic.ini
 
echo "Starting $NAME as `whoami`"
 
# Activate the virtual environment
cd $DJANGODIR
source ./venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
export NEW_RELIC_CONFIG_FILE

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR
 
# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec newrelic-admin run-program gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --log-level=debug \
  --bind=unix:$SOCKFILE
