#!/bin/bash
set -e

API_BASE="${KI_API_BASE:-http://127.0.0.1:8765}"

curl -fsS -X POST "$API_BASE/api/admin/rebuild-index"
echo
