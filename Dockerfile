# Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

# CMD ["gunicorn", "main:app", "-c", "/app/gunicorn_conf.py"]
CMD ["./entrypoint.sh"]
