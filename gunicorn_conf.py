import logging

bind = "0.0.0.0:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"

max_requests = 100
max_requests_jitter = 10

# Logging configuration
loglevel = "info"  # Set the log level to capture errors and above
errorlog = "-"  # Log errors to stdout
accesslog = "-"  # Log access to stdout
