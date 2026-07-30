#!/usr/bin/env bash
#
# 检查模板占位符：
#   - consumer：拒绝非模板文件中的任何 {{...}} 残留、残缺双花括号，
#     以及 .github/CODEOWNERS 中未替换的 @your-org/。若存在
#     .docs-template/state.tsv，仅精确豁免其中 placeholder_policy=preserve-template
#     的安全 destination；无 state 时使用内置窄 allowlist。
#   - template：允许模板源文件保留占位符，但校验 token 必须使用
#     SCREAMING_SNAKE_CASE；examples 等非模板内容仍不得残留占位符。
#
# 用法：
#   bash scripts/check-placeholders.sh
#   bash scripts/check-placeholders.sh docs/features
#   bash scripts/check-placeholders.sh --mode template
#
# 退出码：0 = 通过；1 = 发现残留或非法 token；2 = 参数或目标路径错误

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$REPO_ROOT"

TARGET="."
MODE="consumer"
TARGET_SEEN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      [ "$#" -ge 2 ] || { echo "ERROR --mode requires a value."; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --mode=*)
      MODE="${1#--mode=}"
      shift
      ;;
    -*)
      echo "ERROR unknown option: $1"
      exit 2
      ;;
    *)
      if [ "$TARGET_SEEN" -eq 1 ]; then
        echo "ERROR only one target may be provided."
        exit 2
      fi
      TARGET="$1"
      TARGET_SEEN=1
      shift
      ;;
  esac
done

if [ "$MODE" != "consumer" ] && [ "$MODE" != "template" ]; then
  echo "ERROR unknown mode: ${MODE}. Use consumer or template."
  exit 2
fi

if [ ! -e "$TARGET" ]; then
  echo "ERROR target does not exist: ${TARGET}"
  exit 2
fi

if [ ! -d "$TARGET" ]; then
  target_name="$(basename "$TARGET")"
  case "$target_name" in
    CODEOWNERS|*.[mM][dD]|*.[yY][mM][lL]|*.[yY][aA][mM][lL]|*.[tT][sS][vV]) ;;
    *)
      echo "ERROR target must be a directory or a supported documentation file: $TARGET"
      exit 2
      ;;
  esac
fi

if [ -d "$TARGET" ]; then
  target_absolute="$(cd "$TARGET" && pwd -P)"
else
  target_absolute="$(cd "$(dirname "$TARGET")" && pwd -P)/$(basename "$TARGET")"
fi

if [ "$target_absolute" = "$REPO_ROOT" ]; then
  SCAN_TARGET="."
elif [[ "$target_absolute" == "$REPO_ROOT/"* ]]; then
  SCAN_TARGET=".${target_absolute#"$REPO_ROOT"}"
else
  SCAN_TARGET="$target_absolute"
fi

CONSUMER_TEMPLATE_RE='(-template\.md$|ADR-000-template\.md$|^docs/style-guide\.md$)'
TEMPLATE_REPOSITORY_RE='(^AGENTS\.md$|^CHANGELOG\.md$|^CONTRIBUTING\.md$|^README\.md$|^SECURITY\.md$|^TEMPLATE_REPOSITORY_MAINTENANCE\.md$|^template-mapping\.md$|^docs/.*\.md$|^scaffold/.*\.tsv$|^scaffold/templates/.*$|^\.github/pull_request_template\.md$|^\.github/ISSUE_TEMPLATE/.*\.ya?ml$|^\.github/CODEOWNERS$)'
BALANCED_PLACEHOLDER_RE='\{\{([^{}]*)\}\}'
VALID_TOKEN_RE='^[A-Z][A-Z0-9_]*$'
STATE_PRESENT=0
STATE_ALLOWLIST=""
STATE_DESTINATION_KEYS=""
STATE_TEMPLATE_VERSION=""
SHA256_RESULT=""

state_error() {
  echo "ERROR invalid .docs-template/state.tsv: $1"
  exit 2
}

safe_state_destination() {
  local value="$1"
  [ -n "$value" ] || return 1
  case "$value" in /*|*\\*|*:*|*/|*//*|.|..|./*|../*|*/./*|*/../*|*/.|*/..) return 1 ;; esac
  return 0
}

valid_state_packs() {
  local value="$1"
  local pack seen=""
  local -a pack_values

  [[ "$value" =~ ^[a-z0-9]+(-[a-z0-9]+)*(\;[a-z0-9]+(-[a-z0-9]+)*)*$ ]] || return 1
  IFS=';' read -r -a pack_values <<< "$value"
  for pack in "${pack_values[@]}"; do
    if state_list_has "$seen" "$pack"; then
      return 1
    fi
    if [ -n "$seen" ]; then
      seen="$seen"$'\n'"$pack"
    else
      seen="$pack"
    fi
  done
  return 0
}

authorized_preserve_destination() {
  local value="$1"
  case "$value" in
    *-template.md|docs/style-guide.md)
      return 0
      ;;
  esac
  return 1
}

sha256_file() {
  local path="$1"
  local output

  if command -v sha256sum >/dev/null 2>&1; then
    output="$(sha256sum -- "$path")" || state_error "unable to hash '$path'."
    SHA256_RESULT="${output%%[[:space:]]*}"
  elif command -v shasum >/dev/null 2>&1; then
    output="$(shasum -a 256 -- "$path")" || state_error "unable to hash '$path'."
    SHA256_RESULT="${output%%[[:space:]]*}"
  elif command -v openssl >/dev/null 2>&1; then
    output="$(openssl dgst -sha256 "$path")" || state_error "unable to hash '$path'."
    SHA256_RESULT="${output##*= }"
  else
    state_error "no SHA-256 command is available."
  fi
  SHA256_RESULT="$(printf '%s' "$SHA256_RESULT" | tr '[:upper:]' '[:lower:]')"
}

state_list_has() {
  local list="$1"
  local value="$2"
  [ -n "$list" ] && printf '%s\n' "$list" | grep -Fqx -- "$value"
}

if [ "$MODE" = "consumer" ] && [ -e ".docs-template/state.tsv" ]; then
  [ -f ".docs-template/state.tsv" ] || state_error "state.tsv is not a regular file."
  STATE_PRESENT=1
  expected_header=$'schema_version\ttemplate_version\tdestination\tsource\tpacks\tplaceholder_policy\tsha256'
  state_line_number=0
  while IFS= read -r state_line || [ -n "$state_line" ]; do
    state_line_number=$((state_line_number + 1))
    state_line="${state_line%$'\r'}"
    if [ "$state_line_number" -eq 1 ]; then
      [ "$state_line" = "$expected_header" ] || state_error "unexpected header."
      continue
    fi
    [ -n "$state_line" ] || state_error "blank row at line $state_line_number."

    without_tabs="${state_line//$'\t'/}"
    tab_count=$(( ${#state_line} - ${#without_tabs} ))
    [ "$tab_count" -eq 6 ] || state_error "expected 7 columns at line $state_line_number."
    converted="${state_line//$'\t'/$'\034'}"
    IFS=$'\034' read -r schema_version template_version destination source packs placeholder_policy sha256 <<< "$converted"

    [ "$schema_version" = "1" ] || state_error "unsupported schema_version at line $state_line_number."
    [[ "$template_version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || state_error "invalid template_version '$template_version' at line $state_line_number."
    if [ -z "$STATE_TEMPLATE_VERSION" ]; then
      STATE_TEMPLATE_VERSION="$template_version"
    elif [ "$template_version" != "$STATE_TEMPLATE_VERSION" ]; then
      state_error "inconsistent template_version '$template_version' at line $state_line_number."
    fi
    safe_state_destination "$destination" || state_error "unsafe destination '$destination' at line $state_line_number."
    safe_state_destination "$source" || state_error "unsafe source '$source' at line $state_line_number."
    destination_key="$(printf '%s' "$destination" | tr '[:upper:]' '[:lower:]')"
    source_key="$(printf '%s' "$source" | tr '[:upper:]' '[:lower:]')"
    if [ "$destination_key" = ".docs-template/state.tsv" ] || [ "$source_key" = ".docs-template/state.tsv" ]; then
      state_error "state.tsv cannot reference itself at line $state_line_number."
    fi
    if state_list_has "$STATE_DESTINATION_KEYS" "$destination_key"; then
      state_error "duplicate destination '$destination' at line $state_line_number."
    fi
    if [ -n "$STATE_DESTINATION_KEYS" ]; then
      STATE_DESTINATION_KEYS="$STATE_DESTINATION_KEYS"$'\n'"$destination_key"
    else
      STATE_DESTINATION_KEYS="$destination_key"
    fi

    valid_state_packs "$packs" || state_error "invalid packs '$packs' at line $state_line_number."
    case "$placeholder_policy" in
      replace|preserve-template|none) ;;
      *) state_error "unknown placeholder_policy '$placeholder_policy' at line $state_line_number." ;;
    esac
    [[ "$sha256" =~ ^[0-9a-f]{64}$ ]] || state_error "invalid sha256 at line $state_line_number."
    if [ "$placeholder_policy" = "preserve-template" ]; then
      authorized_preserve_destination "$destination" || state_error "unauthorized preserve-template destination '$destination' at line $state_line_number."
      preserved_path="$REPO_ROOT/$destination"
      [ -f "$preserved_path" ] || state_error "preserve-template destination '$destination' does not exist as a file."
      sha256_file "$preserved_path"
      [ "$SHA256_RESULT" = "$sha256" ] || state_error "sha256 mismatch for preserve-template destination '$destination'."
      if [ -n "$STATE_ALLOWLIST" ]; then
        STATE_ALLOWLIST="$STATE_ALLOWLIST"$'\n'"$destination"
      else
        STATE_ALLOWLIST="$destination"
      fi
    fi
  done < ".docs-template/state.tsv"
  [ "$state_line_number" -gt 0 ] || state_error "unexpected header."
fi

is_token_allowed() {
  local rel="$1"
  if [ "$MODE" = "consumer" ] && [ "$STATE_PRESENT" -eq 1 ]; then
    state_list_has "$STATE_ALLOWLIST" "$rel"
    return $?
  fi
  if [[ "$rel" =~ $CONSUMER_TEMPLATE_RE ]]; then
    return 0
  fi
  if [ "$MODE" = "template" ] && [[ "$rel" =~ $TEMPLATE_REPOSITORY_RE ]]; then
    return 0
  fi
  return 1
}

is_syntax_example() {
  local rel="$1"
  local token="$2"
  [ "$rel" = "docs/style-guide.md" ] && [ "$token" = "xxx" ]
}

echo "==> 扫描 ${TARGET} 中的模板占位符"
if [ "$MODE" = "template" ]; then
  echo "    Mode: template，模板源允许合法 token，非模板内容不得残留。"
else
  echo "    Mode: consumer，非模板文件不得残留占位符。"
fi
echo

found=0
while IFS= read -r -d '' file; do
  rel="${file#./}"
  token_allowed=false
  if is_token_allowed "$rel"; then
    token_allowed=true
  fi

  line_number=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_number=$((line_number + 1))
    original_line="$line"

    if [[ "$line" =~ \{\{\{|\}\}\} ]]; then
      printf '  %s:%d: malformed triple-brace marker: %s\n' "$rel" "$line_number" "$original_line"
      found=$((found + 1))
    fi

    remaining="$line"
    while [[ "$remaining" =~ $BALANCED_PLACEHOLDER_RE ]]; do
      matched="${BASH_REMATCH[0]}"
      token="${BASH_REMATCH[1]}"
      if [ "$token_allowed" = false ]; then
        printf '  %s:%d: unresolved placeholder %s\n' "$rel" "$line_number" "$matched"
        found=$((found + 1))
      elif ! [[ "$token" =~ $VALID_TOKEN_RE ]] && ! is_syntax_example "$rel" "$token"; then
        printf '  %s:%d: invalid placeholder token %s\n' "$rel" "$line_number" "$matched"
        found=$((found + 1))
      fi
      remaining="${remaining/"$matched"/}"
    done

    if [[ "$remaining" == *'{{'* ]] || [[ "$remaining" == *'}}'* ]]; then
      printf '  %s:%d: incomplete double-brace marker: %s\n' "$rel" "$line_number" "$original_line"
      found=$((found + 1))
    fi

    if [ "$MODE" = "consumer" ] && [[ "$rel" =~ (^|/)\.github/CODEOWNERS$ ]]; then
      marker_remaining="$line"
      while [[ "$marker_remaining" == *'@your-org/'* ]]; do
        printf '  %s:%d: unresolved CODEOWNERS marker @your-org/\n' "$rel" "$line_number"
        found=$((found + 1))
        marker_remaining="${marker_remaining#*'@your-org/'}"
      done
    fi
  done < "$file"
done < <(
  find "$SCAN_TARGET" -type f \
    ! -path '*/.git/*' \
    \( -iname '*.md' -o -iname '*.yml' -o -iname '*.yaml' -o -iname '*.tsv' -o -name 'CODEOWNERS' \) \
    -print0
)

echo
if [ "$found" -eq 0 ]; then
  echo "OK placeholder checks passed."
  exit 0
fi

echo "FAIL found ${found} placeholder issue(s)."
if [ "$MODE" = "consumer" ]; then
  echo "     Replace project placeholders and CODEOWNERS markers before committing."
else
  echo "     Template tokens must use SCREAMING_SNAKE_CASE; examples must remain placeholder-clean."
fi
exit 1
