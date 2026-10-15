#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
gen_value() {
  case "$1" in
    # BloodHound enforces 12+ characters with upper, lower, digit and symbol.
    BLOODHOUND_ADMIN_PASSWORD) echo "Bh-$(openssl rand -hex 12)-Q7!" ;;
    *) openssl rand -hex 24 ;;
  esac
}
command -v openssl >/dev/null || { echo "OpenSSL is required to generate secrets."; exit 1; }
if [[ -f .env ]]; then
  [[ -s .env && -n "$(tail -c1 .env)" ]] && echo >> .env
  # Append settings added to .env.example after this install; never touch existing values.
  added=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^([A-Z0-9_]+)= ]] || continue
    key=${BASH_REMATCH[1]}
    /usr/bin/grep -q "^$key=" .env && continue
    [[ "$line" == *=CHANGE_ME* ]] && line="$key=$(gen_value "$key")"
    printf '%s\n' "$line" >> .env
    added+=("$key")
  done < .env.example
  (( ${#added[@]} )) && echo "Added new settings to .env: ${added[*]}"
  if /usr/bin/grep -q 'CHANGE_ME' .env; then
    echo "Your .env still contains placeholders. Replace them or rename the file and run setup again."
    exit 1
  fi
  chmod 600 .env
  echo "Existing settings preserved."
  exit 0
fi
umask 077
temp_file=$(mktemp .env.tmp.XXXXXX)
trap 'rm -f "$temp_file"' EXIT
while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" =~ ^([A-Z0-9_]+)=CHANGE_ME ]]; then
    line="${BASH_REMATCH[1]}=$(gen_value "${BASH_REMATCH[1]}")"
  fi
  printf '%s\n' "$line" >> "$temp_file"
done < .env.example
mv "$temp_file" .env
echo "Created private settings in .env. Keep this file with your backups."
