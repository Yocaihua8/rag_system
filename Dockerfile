FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn[standard]>=0.30.0"

COPY app.py ./app.py
COPY webapp ./webapp
COPY src/__init__.py ./src/__init__.py
COPY src/config ./src/config

EXPOSE 8765

CMD ["python", "-c", "from webapp.server import run_server; raise SystemExit(run_server(host='0.0.0.0', port=8765))"]
