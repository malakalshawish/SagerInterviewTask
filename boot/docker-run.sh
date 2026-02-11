#!/bin/bash
set -e

# Ensure we use the venv-installed packages (psycopg, etc.)
export PATH="/opt/venv/bin:$PATH"

cd /code

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn cfehome.wsgi:application \
--bind 0.0.0.0:${PORT:-8000} \
--workers 3



# set -e
# source /opt/venv/bin/activate
# cd /code

# python manage.py migrate --noinput 
# python manage.py auto_admin --force

# # PORT=8080

# # export RUNTIME_PORT=${PORT:-8080}
# # export RUNTIME_HOST=${HOST:-0.0.0.0}

# #add static files to the container itself during run time
# #python manage.py collectstatic --no-input 
# exec gunicorn cfehome.wsgi:application --bind 0.0.0.0:${PORT:-8000}