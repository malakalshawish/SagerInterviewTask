#!/bin/bash

source /opt/venv/bin/activate
cd /code

python manage.py migrate --noinput 
python manage.py auto_admin --force

export RUNTIME_PORT=8080

#add static files to the container itself during run time
#python manage.py collectstatic --no-input 
gunicorn cfehome.wsgi:application --bind 0.0.0.0:$RUNTIME_PORT