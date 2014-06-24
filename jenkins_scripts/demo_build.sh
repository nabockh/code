#!/bin/bash -ex
PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
# needed on my mac to compile c-extensions
PATH=$PATH:/Library/PostgreSQL/9.3/bin
export CFLAGS=-Qunused-arguments
export CPPFLAGS=-Qunused-arguments

cd $WORKSPACE
virtualenv -q venv
source ./venv/bin/activate
pip install -r requirements.txt
#python manage.py migrate
#python manage.py jenkins
fab demo_server deploy