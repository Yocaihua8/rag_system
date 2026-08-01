FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    KI_API_HOST=0.0.0.0 \
    KI_API_PORT=8765

WORKDIR /app

COPY backend/requirements/base.txt ./backend/requirements/base.txt
RUN pip install --no-cache-dir -r backend/requirements/base.txt

COPY backend ./backend

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/runtime/v2 \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8765

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health', timeout=2)" || exit 1

ENTRYPOINT ["/bin/sh", "backend/entrypoint.sh"]
