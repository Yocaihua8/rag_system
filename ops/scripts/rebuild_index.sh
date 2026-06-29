#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_URL="${KI_BASE_URL:-http://127.0.0.1:8765}"
PROJECT_ID="${KI_PROJECT_ID:-${1:-}}"
ENDPOINT="${BASE_URL%/}/api/admin/rebuild-index"

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "$value"
}

PAYLOAD="{}"
if [[ -n "$PROJECT_ID" ]]; then
  PAYLOAD="{\"project_id\":\"$(json_escape "$PROJECT_ID")\"}"
fi

curl_args=(
  -sS
  -X POST
  "$ENDPOINT"
  -H "Content-Type: application/json"
  --data "$PAYLOAD"
)

if [[ -n "${KI_API_KEY:-}" ]]; then
  curl_args+=( -H "X-API-Key: ${KI_API_KEY}" )
fi

if [[ -n "${KI_BEARER_TOKEN:-}" ]]; then
  curl_args+=( -H "Authorization: Bearer ${KI_BEARER_TOKEN}" )
fi

curl "${curl_args[@]}"
echo
