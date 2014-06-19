from fabric.api import *
from fabric.colors import green, red
from fabric.contrib import django
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# # hosts
# env.hosts = [
#     '162.243.205.164',
# ]

django.settings_module('app.settings')
from django.conf import settings
from django.contrib.auth.models import User
dbsettings = settings.DATABASES['default']

if dbsettings['USER'] and dbsettings['PASSWORD']:
    DB_CONNECTION_STRING = "dbname='postgres' user='{0}' password='{1}' host='{2}'".format(
        dbsettings['USER'], dbsettings['PASSWORD'], dbsettings['HOST'])
else:
    DB_CONNECTION_STRING = "dbname='postgres'"


def prepare_deploy():
    local("python manage.py test")
    local("git add -p && git commit")


def create_superuser():
    u = User(username='admin')
    u.set_password('admin')
    u.is_superuser = True
    u.is_staff = True
    u.save()


def drop_db():
    with psycopg2.connect(DB_CONNECTION_STRING) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as curs:
            curs.execute("DROP DATABASE IF EXISTS {0}".format(dbsettings['NAME']))


def create_db():
    with psycopg2.connect(DB_CONNECTION_STRING) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as curs:
            curs.execute("CREATE DATABASE {0} WITH OWNER = postgres".format(dbsettings['NAME']))


def deploy_local():
    drop_db()
    create_db()
    local("python manage.py syncdb --noinput")
    # local("python manage.py migrate")
    create_superuser()
    local("python manage.py runserver")
    # local("python manage.py collectstatic --noinput")
    # local("gunicorn app.wsgi --bind=127.0.0.1:8001")


def demo_server():
    """Demo server configuration Ubuntu 14.04 x32"""
    # The IP of your server
    env.host_string = '95.85.42.42'
    # Set the username
    env.user = "root"
    # Set the password [NOT RECOMMENDED]
    env.password = "rauuayhbngvv"


def prod_server():
    """Production server configuration Ubuntu 14.04 x32"""
    # The IP of your server
    env.host_string = '107.170.123.130'
    # Set the username
    env.user = "root"
    # Set the password [NOT RECOMMENDED]
    env.password = "xnlhcjlgdbao"    

def deploy():
    # path to the directory on the server where your vhost is set up
    path = "/root/projects/bedade"
    # name of the application process
    process_web = "bedade_web"
    process_worker = "bedade_celeryworker"

    print(red("Beginning Deploy:"))
    with cd("%s" % path):
        run("pwd")
        print(green("Pulling master from GitHub..."))
        run("git pull origin master")
        print(green("Installing requirements..."))
        run("source %s/venv/bin/activate && pip install -r requirements.txt" % path)
        print(green("Collecting static files..."))
        run("source %s/venv/bin/activate && python manage.py collectstatic --noinput" % path)
        # print(green("Creating the database..."))
        # run("sudo -u postgres createdb %s" % dbsettings['NAME'])
        print(green("Syncing the database..."))
        run("source %s/venv/bin/activate && python manage.py syncdb" % path)
        # print(green("Migrating the database..."))
        # run("source %s/venv/bin/activate && python manage.py migrate" % path)

        print(green("Restarting celery worker..."))
        run("sudo supervisorctl restart %s" % process_worker)
        # print(green("Starting gunicorn..."))
        # run("source %s/venv/bin/activate && gunicorn app.wsgi:application --bind 0.0.0.0:8001" % path)
        # print(green("Starting django dev server..."))
        # run("source %s/venv/bin/activate && python manage.py runserver 0.0.0.0:8000" % path)
        print(green("Restart the django dev server"))
        run("sudo supervisorctl restart %s" % process_web)

    print(red("DONE!"))

def bootstrap():
    # before running bootstrap it's needed to generate ssh key
    # and add it to deployment keys in bitbucket repo settings
    run("aptitude     update")
    run("aptitude  -y upgrade")
    run("aptitude  -y install python-virtualenv")
    sudo("aptitude -y install python-dev")
    sudo("aptitude -y install supervisor")
    run("aptitude  -y install git")
    # install postgres
    sudo("aptitude -y install postgresql postgresql-contrib-9.3")
    run("aptitude  -y install postgresql-server-dev-9.3")

    # # set password for postgres user
    # sudo -u postgres psql postgres
    # \password postgres
    run("sudo -u postgres createuser --superuser $USER")
    run("sudo -u postgres createdb %s" % dbsettings['NAME'])

    run("aptitude  -y install rabbitmq-server")
    
    run("mkdir projects")
    with cd("projects"):
        run("git clone git@bitbucket.org:Perfectial/bedade.git")
        with cd("bedade"):
            run("virtualenv venv")
            sudo("chmod a+x bedade_web_dev.sh") 
            sudo("chmod a+x bedade_celeryworker_dev.sh")

    for conf in ['bedade_web.conf', 'bedade_celeryworker.conf']:
        put('jenkins_scripts/%s' % conf, '/etc/supervisor/conf.d/%s' % conf)

    sudo("supervisorctl reread")
    sudo("supervisorctl update")


def ssh_create():
    run("ssh-keygen")
    run("ssh-agent /bin/bash")
    run("ssh-add ~/.ssh/id_rsa")
    # run("cat ~/.ssh/id_rsa.pub")
