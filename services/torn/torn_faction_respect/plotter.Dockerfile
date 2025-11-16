FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY plotter.py .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    psycopg2-binary \
    pandas \
    seaborn \
    matplotlib \
    python-dateutil \
    requests \
    python-dotenv

ENV PYTHONUNBUFFERED=1

EXPOSE 8008

CMD ["uvicorn", "plotter:app", "--host", "0.0.0.0", "--port", "8008"]