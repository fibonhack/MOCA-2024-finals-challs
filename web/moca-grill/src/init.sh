#!/bin/sh

cd /app
python3 manage.py migrate
gunicorn backend.wsgi &

sh /docker-entrypoint.sh nginx -g 'daemon off;'