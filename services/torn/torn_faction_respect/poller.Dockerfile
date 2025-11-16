FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY poller.py .

RUN pip install --no-cache-dir requests psycopg2-binary

ENV PYTHONUNBUFFERED=1

CMD ["python3", "./poller.py"]