FROM node:24-alpine AS frontend-build

WORKDIR /app

COPY package.json package-lock.json vite.config.js ./
COPY frontend ./frontend

RUN npm ci && npm run build


FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-docker.txt ./requirements-docker.txt
RUN python -m pip install --no-cache-dir -r requirements-docker.txt

COPY app.py ./app.py
COPY webapp ./webapp
COPY backend ./backend
COPY --from=frontend-build /app/webapp/static_dist ./webapp/static_dist
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/runtime/webapp \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8765

HEALTHCHECK --interval=10s --timeout=5s --retries=6 --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health', timeout=5).read()"

ENTRYPOINT ["/entrypoint.sh"]
