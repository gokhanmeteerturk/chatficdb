#!/bin/bash
# import nltk and get stopwords:
python -c "import nltk; nltk.download('stopwords')"

# Run migrations if necessary
#python migrate.py migrate
python database/migrate.py
# aerich migrate
aerich upgrade

# Start the Huey worker in the background
/usr/local/bin/huey_consumer helpers.tasks.huey > /proc/1/fd/1 2>/proc/1/fd/2 &

# Start the FastAPI application
exec gunicorn main:app -c /app/gunicorn_conf.py
