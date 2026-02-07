#!/bin/bash

source /opt/venv/bin/activate
cd /code

python manage.py migrate --noinput 
python manage.py auto_admin --force

PORT=8081

export RUNTIME_PORT=${PORT:-8080}
export RUNTIME_HOST=${HOST:-0.0.0.0}

#add static files to the container itself during run time
#python manage.py collectstatic --no-input 
gunicorn cfehome.wsgi:application --bind $RUNTIME_HOST:$RUNTIME_PORT