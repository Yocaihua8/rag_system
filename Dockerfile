FROM node:20-slim AS frontend-build

WORKDIR /app

COPY package.json package-lock.json vite.config.js ./
COPY frontend ./frontend

RUN npm ci
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn[standard]>=0.30.0"

COPY backend ./backend
COPY --from=frontend-build /app/backend/knowledge_island/static_dist ./backend/knowledge_island/static_dist
COPY legacy/__init__.py ./legacy/__init__.py
COPY legacy/desktop/__init__.py ./legacy/desktop/__init__.py
COPY legacy/desktop/config ./legacy/desktop/config

EXPOSE 8765

CMD ["python", "-c", "from backend.knowledge_island.server import run_server; raise SystemExit(run_server(host='0.0.0.0', port=8765))"]
