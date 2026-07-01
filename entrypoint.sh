#!/bin/sh
set -e

mkdir -p /app/runtime/webapp

echo "知识岛启动中 (host=0.0.0.0, port=8765)..."
exec python -c "
import sys
sys.path.insert(0, '/app')
from backend.api.server import run_server
raise SystemExit(run_server(host='0.0.0.0', port=8765))
"
