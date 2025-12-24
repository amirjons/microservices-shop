FROM python:3.13

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python worker_inbox.py & python worker_outbox.py & uvicorn main:app --host 0.0.0.0 --port 8000"]