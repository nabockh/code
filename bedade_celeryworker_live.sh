#!/bin/bash
NAME="bedade_celeryworker"                                  # Name of the application
DJANGODIR=/webapps/bedade/bedade              # Django project directory
echo "Starting $NAME as `whoami`"
# Activate the virtual environment
cd $DJANGODIR
source ./venv/bin/activate
exec celery -A app worker --beat -l info