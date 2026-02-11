#!/bin/bash
set -e

export PATH="/opt/venv/bin:$PATH"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# If this container is the MQTT worker, run the subscriber instead of gunicorn
if [ "${RUN_MQTT}" = "1" ]; then
exec python manage.py run_mqtt
fi

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