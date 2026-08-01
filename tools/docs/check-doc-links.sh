#!/usr/bin/env bash
#
# Validate local links in downstream project Markdown documents.
#
# Usage:
#   bash tools/docs/check-doc-links.sh
#   bash tools/docs/check-doc-links.sh docs
#   bash tools/docs/check-doc-links.sh --target /path/to/project
#
# Exit codes:
#   0 = all local links are valid
#   1 = one or more invalid local links were found
#   2 = invalid target or the target could not be scanned

set -uo pipefail

target="."
positional_target_seen=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      if [ "$#" -lt 2 ]; then
        echo "ERROR --target requires a value"
        exit 2
      fi
      target="$2"
      positional_target_seen=1
      shift 2
      ;;
    --target=*)
      target="${1#--target=}"
      positional_target_seen=1
      shift
      ;;
    -*)
      echo "ERROR unknown option: $1"
      exit 2
      ;;
    *)
      if [ "$positional_target_seen" -eq 1 ]; then
        echo "ERROR only one target may be provided"
        exit 2
      fi
      target="$1"
      positional_target_seen=1
      shift
      ;;
  esac
done

if [ ! -e "$target" ]; then
  echo "ERROR target does not exist: $target"
  exit 2
fi

target_is_file=0
files=()
known_paths=()

if [ -d "$target" ]; then
  if ! scan_root="$(cd "$target" 2>/dev/null && pwd -P)"; then
    echo "ERROR unable to scan target: $target"
    exit 2
  fi
  while IFS= read -r -d '' file; do
    files+=("$file")
  done < <(
    find "$scan_root" \
      \( -type d \( \
        -name '.git' -o -name '.venv' -o -name 'node_modules' -o \
        -name '__pycache__' -o -name '.pytest_cache' -o -name 'runtime' -o \
        -name 'static_dist' -o -name 'dist' -o -name 'build' -o \
        -name 'release-cache' -o -name 'docker-workspace' -o -name 'tmp' -o \
        -name '.tmp' -o -name 'temp' -o -name 'test-results' \
      \) -prune \) -o \
      \( -type f -iname '*.md' -print0 \) 2>/dev/null
  )
  while IFS= read -r -d '' entry; do
    known_paths+=("$entry")
  done < <(
    find "$scan_root" \
      \( -type d \( \
        -name '.git' -o -name '.venv' -o -name 'node_modules' -o \
        -name '__pycache__' -o -name '.pytest_cache' -o -name 'runtime' -o \
        -name 'static_dist' -o -name 'dist' -o -name 'build' -o \
        -name 'release-cache' -o -name 'docker-workspace' -o -name 'tmp' -o \
        -name '.tmp' -o -name 'temp' -o -name 'test-results' \
      \) -prune \) -o -print0 2>/dev/null
  )
elif [ -f "$target" ] && [[ "$target" == *.[mM][dD] ]]; then
  target_is_file=1
  target_dir="$(dirname "$target")"
  target_name="$(basename "$target")"
  if ! scan_root="$(cd "$target_dir" 2>/dev/null && pwd -P)"; then
    echo "ERROR unable to scan target: $target"
    exit 2
  fi
  files+=("$scan_root/$target_name")
else
  echo "ERROR target must be a directory or a Markdown file: $target"
  exit 2
fi

echo "==> checking local Markdown links under $target"

invalid_count=0
normalized_path=""
percent_decoded=""
slug_result=""

normalize_path() {
  local value="${1//\\//}"
  local part
  local joined
  local -a parts stack

  IFS='/' read -r -a parts <<< "$value"
  stack=()
  for part in "${parts[@]}"; do
    case "$part" in
      ''|.)
        ;;
      ..)
        if [ "${#stack[@]}" -gt 0 ]; then
          unset 'stack[${#stack[@]}-1]'
        fi
        ;;
      *)
        stack+=("$part")
        ;;
    esac
  done

  joined=""
  for part in "${stack[@]}"; do
    joined="$joined/$part"
  done
  if [ -z "$joined" ]; then
    joined="/"
  fi
  normalized_path="$joined"
}

path_case_exact() {
  local value="$1"
  local path_to_walk="$value"
  local part entry
  local current="/"
  local -a parts

  [ -e "$value" ] || return 1
  if [ "$target_is_file" -eq 0 ] && { [ "$value" = "$scan_root" ] || [[ "$value" == "$scan_root/"* ]]; }; then
    for entry in "${known_paths[@]}"; do
      if [ "$entry" = "$value" ]; then
        return 0
      fi
    done
    return 1
  fi

  # MSYS/Cygwin drive mounts such as /c may exist without being enumerable as
  # children of /. Start inside the virtual drive and keep checking every real
  # path segment with case-sensitive find matching.
  case "${OSTYPE:-}" in
    msys*|cygwin*|mingw*)
      if [[ "$path_to_walk" =~ ^/([A-Za-z])(/|$) ]]; then
        current="/${BASH_REMATCH[1]}"
        path_to_walk="${path_to_walk:2}"
        path_to_walk="${path_to_walk#/}"
      elif [[ "$path_to_walk" =~ ^([A-Za-z]):(/|$) ]]; then
        current="${BASH_REMATCH[1]}:/"
        path_to_walk="${path_to_walk:3}"
      fi
      ;;
  esac

  IFS='/' read -r -a parts <<< "$path_to_walk"
  for part in "${parts[@]}"; do
    [ -n "$part" ] || continue
    entry="$(find "$current" -mindepth 1 -maxdepth 1 -name "$part" -print -quit 2>/dev/null)"
    [ -n "$entry" ] || return 1
    current="$entry"
  done
  return 0
}

percent_decode() {
  local value="$1"
  local output=""
  local index=0
  local character hex decoded

  while [ "$index" -lt "${#value}" ]; do
    character="${value:$index:1}"
    if [ "$character" = '%' ] && [ $((index + 2)) -lt "${#value}" ]; then
      hex="${value:$((index + 1)):2}"
      if [[ "$hex" =~ ^[0-9A-Fa-f]{2}$ ]] && [ "$hex" != "00" ]; then
        printf -v decoded '%b' "\\x$hex"
        output="$output$decoded"
        index=$((index + 3))
        continue
      fi
    fi
    output="$output$character"
    index=$((index + 1))
  done
  percent_decoded="$output"
}

convert_to_anchor_slug() {
  local text="$1"
  local html_re='<[^>]+>'
  local match
  local character code
  local output=""
  local index

  while [[ "$text" =~ $html_re ]]; do
    match="${BASH_REMATCH[0]}"
    text="${text/"$match"/}"
  done
  text="$(printf '%s' "$text" | tr '[:upper:]' '[:lower:]')"

  for ((index = 0; index < ${#text}; index++)); do
    character="${text:$index:1}"
    if [[ "$character" =~ [A-Za-z0-9_-] ]]; then
      output="$output$character"
    elif [[ "$character" =~ [[:space:]] ]]; then
      output="$output-"
    else
      printf -v code '%d' "'$character"
      if [ "$code" -gt 127 ]; then
        output="$output$character"
      fi
    fi
  done
  slug_result="$output"
}

anchor_exists() {
  local file="$1"
  local wanted="$2"
  local line marker character heading base anchor existing
  local line_number=0
  local in_fence=0
  local fence_character=""
  local fence_length=0
  local count
  local fence_re='^[[:space:]]*(`{3,}|~{3,})'
  local heading_re='^[[:space:]]{0,3}#{1,6}[[:space:]]+(.+)[[:space:]]*$'
  local trailing_hash_re='[[:space:]]+#+[[:space:]]*$'
  local id_double_re='<[A-Za-z][^>]*[[:space:]](id|name)[[:space:]]*=[[:space:]]*"([^"]+)"[^>]*>'
  local id_single_re="<[A-Za-z][^>]*[[:space:]](id|name)[[:space:]]*=[[:space:]]*'([^']+)'[^>]*>"
  local -a base_slugs

  base_slugs=()
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    line_number=$((line_number + 1))
    if [ "$in_fence" -eq 1 ]; then
      if [[ "$line" =~ $fence_re ]]; then
        marker="${BASH_REMATCH[1]}"
        character="${marker:0:1}"
        if [ "$character" = "$fence_character" ] && [ "${#marker}" -ge "$fence_length" ]; then
          in_fence=0
          fence_character=""
          fence_length=0
        fi
      fi
      continue
    fi
    if [[ "$line" =~ $fence_re ]]; then
      marker="${BASH_REMATCH[1]}"
      in_fence=1
      fence_character="${marker:0:1}"
      fence_length="${#marker}"
      continue
    fi

    if [[ "$line" =~ $id_double_re ]] && [ "${BASH_REMATCH[2]}" = "$wanted" ]; then
      return 0
    fi
    if [[ "$line" =~ $id_single_re ]] && [ "${BASH_REMATCH[2]}" = "$wanted" ]; then
      return 0
    fi

    if [[ "$line" =~ $heading_re ]]; then
      heading="${BASH_REMATCH[1]}"
      if [[ "$heading" =~ $trailing_hash_re ]]; then
        heading="${heading%"${BASH_REMATCH[0]}"}"
      fi
      convert_to_anchor_slug "$heading"
      base="$slug_result"
      [ -n "$base" ] || continue

      count=0
      for existing in "${base_slugs[@]}"; do
        if [ "$existing" = "$base" ]; then
          count=$((count + 1))
        fi
      done
      base_slugs+=("$base")
      anchor="$base"
      if [ "$count" -gt 0 ]; then
        anchor="$base-$count"
      fi
      if [ "$anchor" = "$wanted" ]; then
        return 0
      fi
    fi
  done < "$file"

  return 1
}

report_invalid() {
  local display_path="$1"
  local line_number="$2"
  local reason="$3"
  local destination="$4"
  echo "  ${display_path}:${line_number}: [$reason] $destination"
  invalid_count=$((invalid_count + 1))
}

validate_destination() {
  local raw_destination="$1"
  local is_image="$2"
  local source_file="$3"
  local line_number="$4"
  local display_path="$5"
  local destination path_part fragment=""
  local has_fragment=0
  local candidate lower_candidate

  destination="$raw_destination"
  if [[ "$destination" == '<'*'>' ]]; then
    destination="${destination:1:${#destination}-2}"
  fi

  case "$destination" in
    [hH][tT][tT][pP]://*|[hH][tT][tT][pP][sS]://*|[mM][aA][iI][lL][tT][oO]:*|\?*)
      return
      ;;
  esac

  if [[ "$destination" == *'#'* ]]; then
    has_fragment=1
    path_part="${destination%%#*}"
    fragment="${destination#*#}"
  else
    path_part="$destination"
  fi
  path_part="${path_part%%\?*}"

  percent_decode "$path_part"
  path_part="${percent_decoded//\\//}"
  if [ "$has_fragment" -eq 1 ]; then
    percent_decode "$fragment"
    fragment="$percent_decoded"
  fi

  if [ -z "$path_part" ]; then
    candidate="$source_file"
  elif [[ "$path_part" == /* ]]; then
    candidate="$scan_root/${path_part#/}"
  else
    candidate="$(dirname "$source_file")/$path_part"
  fi
  normalize_path "$candidate"
  candidate="$normalized_path"

  if [ ! -e "$candidate" ]; then
    report_invalid "$display_path" "$line_number" "missing-target" "$raw_destination"
    return
  fi
  if ! path_case_exact "$candidate"; then
    report_invalid "$display_path" "$line_number" "case-mismatch" "$raw_destination"
    return
  fi
  if [ "$is_image" -eq 1 ] && [ -d "$candidate" ]; then
    report_invalid "$display_path" "$line_number" "image-target-not-file" "$raw_destination"
    return
  fi

  if [ "$has_fragment" -eq 1 ] && [ -n "$fragment" ]; then
    lower_candidate="$(printf '%s' "$candidate" | tr '[:upper:]' '[:lower:]')"
    if [ -d "$candidate" ] || [[ "$lower_candidate" != *.md ]]; then
      report_invalid "$display_path" "$line_number" "anchor-target-not-markdown" "$raw_destination"
      return
    fi
    if ! anchor_exists "$candidate" "$fragment"; then
      report_invalid "$display_path" "$line_number" "missing-anchor" "$raw_destination"
      return
    fi
  fi
}

link_re='(!?)\[[^]]*\]\([[:space:]]*(<[^>]+>|[^)[:space:]]+)'
reference_re='^[[:space:]]*\[[^]]+\]:[[:space:]]*(<[^>]+>|[^[:space:]]+)'
fence_re='^[[:space:]]*(`{3,}|~{3,})'

for file in "${files[@]}"; do
  if [ "$target_is_file" -eq 1 ]; then
    display_path="$(basename "$file")"
  else
    display_path="${file#"$scan_root"/}"
  fi

  line_number=0
  in_fence=0
  fence_character=""
  fence_length=0

  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    line_number=$((line_number + 1))
    if [ "$in_fence" -eq 1 ]; then
      if [[ "$line" =~ $fence_re ]]; then
        marker="${BASH_REMATCH[1]}"
        character="${marker:0:1}"
        if [ "$character" = "$fence_character" ] && [ "${#marker}" -ge "$fence_length" ]; then
          in_fence=0
          fence_character=""
          fence_length=0
        fi
      fi
      continue
    fi
    if [[ "$line" =~ $fence_re ]]; then
      marker="${BASH_REMATCH[1]}"
      in_fence=1
      fence_character="${marker:0:1}"
      fence_length="${#marker}"
      continue
    fi

    rest="$line"
    while [[ "$rest" =~ $link_re ]]; do
      match="${BASH_REMATCH[0]}"
      image_marker="${BASH_REMATCH[1]}"
      destination="${BASH_REMATCH[2]}"
      is_image=0
      if [ "$image_marker" = '!' ]; then
        is_image=1
      fi
      validate_destination "$destination" "$is_image" "$file" "$line_number" "$display_path"
      rest="${rest#*"$match"}"
    done

    if [[ "$line" =~ $reference_re ]]; then
      validate_destination "${BASH_REMATCH[1]}" 0 "$file" "$line_number" "$display_path"
    fi
  done < "$file"
done

if [ "$invalid_count" -eq 0 ]; then
  echo "OK no invalid local Markdown links."
  exit 0
fi

echo "FAIL found $invalid_count invalid local Markdown link(s)."
exit 1
