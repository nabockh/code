#!/bin/bash
NAME="bedade_web"                                  # Name of the application
DJANGODIR=/root/projects/bedade              # Django project directory
echo "Starting $NAME as `whoami`"
# Activate the virtual environment
cd $DJANGODIR
source ./venv/bin/activate
exec python manage.py runserver 0.0.0.0:8000 --noreload