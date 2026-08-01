#!/usr/bin/env bash
set -uo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
TARGET="."
MODE="consumer"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      [ "$#" -ge 2 ] || { echo "ERROR --mode requires a value"; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --mode=*) MODE="${1#--mode=}"; shift ;;
    -*) echo "ERROR unknown option: $1"; exit 2 ;;
    *) TARGET="$1"; shift ;;
  esac
done

[ "$MODE" = "consumer" ] || [ "$MODE" = "template" ] || {
  echo "ERROR mode must be consumer or template"
  exit 2
}

cd "$REPOSITORY_ROOT"
[ -e "$TARGET" ] || { echo "ERROR target does not exist: $TARGET"; exit 2; }

found=0
while IFS= read -r -d '' file; do
  relative="${file#./}"
  template_allowed=0
  case "$relative" in
    *-template.md|*ADR-000-template.md|docs/governance/style-guide.md) template_allowed=1 ;;
  esac
  [ "$MODE" = "template" ] && template_allowed=1

  line_number=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_number=$((line_number + 1))
    scan_line="$(printf '%s' "$line" | sed -E 's/\$\{\{[^{}]*\}\}//g')"
    while [[ "$scan_line" =~ \{\{([^{}]*)\}\} ]]; do
      placeholder="${BASH_REMATCH[0]}"
      token="${BASH_REMATCH[1]}"
      invalid=0
      if [ "$template_allowed" -eq 0 ] && [[ "$token" =~ ^[[:space:]]*[A-Za-z][A-Za-z0-9_-]*[[:space:]]*$ ]]; then
        invalid=1
      elif [ "$template_allowed" -eq 1 ] && ! [[ "$token" =~ ^[A-Z][A-Z0-9_]*$ ]] && [ "$token" != "xxx" ]; then
        invalid=1
      fi
      if [ "$invalid" -eq 1 ]; then
        printf '  %s:%d: invalid placeholder %s\n' "$relative" "$line_number" "$placeholder"
        found=$((found + 1))
      fi
      scan_line="${scan_line/"$placeholder"/}"
    done
    if [ "$MODE" = "consumer" ] && [ "$relative" = ".github/CODEOWNERS" ] && [[ "$line" == *'@your-org/'* ]]; then
      printf '  %s:%d: unresolved CODEOWNERS marker\n' "$relative" "$line_number"
      found=$((found + 1))
    fi
  done < "$file"
done < <(
  find "$TARGET" \
    \( -type d \( -name '.git' -o -name '.venv' -o -name 'node_modules' -o -name '__pycache__' -o -name '.pytest_cache' -o -name 'runtime' -o -name 'static_dist' -o -name 'dist' -o -name 'build' -o -name 'tmp' -o -name '.tmp' -o -name 'test-results' \) -prune \) -o \
    \( -type f \( -iname '*.md' -o -iname '*.yml' -o -iname '*.yaml' -o -name 'CODEOWNERS' \) -print0 \)
)

if [ "$found" -eq 0 ]; then
  echo "OK placeholder checks passed."
  exit 0
fi

echo "FAIL found $found placeholder issue(s)."
exit 1
