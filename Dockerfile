FROM python:3.12-slim AS backend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ---------------------------------------------------------------------------

FROM node:22-slim AS frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# --- Production frontend ---
FROM node:22-slim AS frontend

WORKDIR /app

COPY --from=frontend-builder /app/.next/standalone ./
COPY --from=frontend-builder /app/.next/static ./.next/static
COPY --from=frontend-builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
