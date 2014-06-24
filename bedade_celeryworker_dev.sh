#!/bin/bash
NAME="bedade_celeryworker"                    # Name of the application
DJANGODIR=/webapps/bedade/bedade              # Django project directory

echo "Starting $NAME as `whoami`"
# Activate the virtual environment
cd $DJANGODIR
source ./venv/bin/activate
# this is bad idea to run the worker with superuser privileges 
# C_FORCE_ROOT env variable should be set in this case
# change this in production environment 
export C_FORCE_ROOT=1
exec celery -A app worker -l info