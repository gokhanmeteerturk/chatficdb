#!/bin/bash

# Run migrations if necessary
#python migrate.py migrate
python database/migrate.py
# aerich migrate
aerich upgrade

# Start your application
exec gunicorn main:app -c /app/gunicorn_conf.py
