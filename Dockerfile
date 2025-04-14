# Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Download Spacy model
RUN python -m spacy download en_core_web_sm

RUN chmod +x /app/entrypoint.sh  # Make the entrypoint script executable

EXPOSE 8000

# CMD ["gunicorn", "main:app", "-c", "/app/gunicorn_conf.py"]
CMD ["./entrypoint.sh"]
