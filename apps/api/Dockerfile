# Build context is the repo root (see docker-compose.yml) because the API
# depends on the local packages/* Python packages via editable installs.
FROM python:3.11-slim

WORKDIR /app

COPY packages/risk-engine ./packages/risk-engine
COPY packages/ai-providers ./packages/ai-providers
COPY packages/broker-core ./packages/broker-core
COPY apps/api ./apps/api

WORKDIR /app/apps/api
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
