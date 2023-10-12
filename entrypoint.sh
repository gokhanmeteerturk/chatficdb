#!/bin/bash

# Run migrations if necessary
#python migrate.py migrate
python migrate.py

# Start your application
exec gunicorn main:app -c /app/gunicorn_conf.py
