import logging

bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"

# Logging configuration
loglevel = "info"  # Set the log level to capture errors and above
errorlog = "-"  # Log errors to stdout
accesslog = "-"  # Log access to stdout
