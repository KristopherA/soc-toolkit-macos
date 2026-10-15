#!/bin/bash
# Copy the source-built tools from GitHubProjects into src/ so builds never depend on that folder.
# Re-run after updating a project in GitHubProjects, then: docker compose --profile cli build
set -euo pipefail
cd "$(dirname "$0")"
gp=$(/usr/bin/sed -n 's/^GITHUB_PROJECTS_DIR=//p' .env 2>/dev/null | tail -1)
gp=${gp:-~/Documents/GitHubProjects}
gp=${gp/#\~/$HOME}
[[ -d "$gp" ]] || { echo "GitHubProjects folder not found: $gp (set GITHUB_PROJECTS_DIR in .env)"; exit 1; }
copy() { # copy <name> <relative path> [extra rsync excludes...]
  local name=$1 rel=$2; shift 2
  [[ -d "$gp/$rel" ]] || { echo "  missing: $gp/$rel"; return 1; }
  mkdir -p "src/$name"
  /usr/bin/rsync -a --delete --exclude .git --exclude .DS_Store --exclude __pycache__ "$@" "$gp/$rel/" "src/$name/"
  echo "  src/$name  <-  $rel"
}
echo "Syncing sources from $gp"
# ClickGrab: skip the 600+ MB of published reports and website assets; the tool does not need them.
copy clickgrab   Malware-Analysis-RE/ClickGrab-main --exclude /nightly_reports --exclude /docs --exclude /public --exclude 'analysis/blog_data_*.json'
copy vt-cli      Threat-Intel-Hunting/vt-cli
copy mvt         Forensics-DFIR/mvt-main --exclude /tests
copy dnsdiag     Network-Security/dnsdiag --exclude /tests
copy volatility3 Forensics-DFIR/volatility3 --exclude /test --exclude /development --exclude /doc
copy nettacker   Network-Security/Nettacker --exclude /tests --exclude /docs --exclude /bin --exclude /include --exclude /lib --exclude /pyvenv.cfg --exclude /.venv
date "+Synced %Y-%m-%d %H:%M" > src/SYNCED.txt
echo "Done. Rebuild with: docker compose --profile cli build"
