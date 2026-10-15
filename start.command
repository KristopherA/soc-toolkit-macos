#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
trap 'echo "Startup stopped. See the message above, then run start.command again."; read -r -p "Press Return to close… "' ERR
export PATH="/usr/local/bin:$HOME/.docker/bin:/opt/homebrew/bin:$PATH"
command -v docker >/dev/null || { echo "Install Docker Desktop for Mac first: https://www.docker.com/products/docker-desktop/"; exit 1; }
if ! docker info >/dev/null 2>&1; then
  echo "Starting Docker Desktop…"
  open -a Docker
  ready=false
  for ((i=0; i<60; i++)); do
    if docker info >/dev/null 2>&1; then ready=true; break; fi
    sleep 2
  done
  [[ "$ready" == true ]] || { echo "Docker did not become ready. Finish Docker Desktop setup and try again."; exit 1; }
fi
./setup.sh
# Source-built tools are copied from GitHubProjects once; re-run ./sync-sources.sh to update them.
[[ -f src/SYNCED.txt ]] || ./sync-sources.sh
# The dashboard joins Caddy's external "proxy" network for https://$SOC_HOSTNAME.
docker network inspect proxy >/dev/null 2>&1 || docker network create proxy >/dev/null
docker compose config --quiet
echo "Starting the SOC Toolkit. The first run downloads and builds the applications and can take 10+ minutes."
docker compose up -d --build
dashboard_port=$(docker compose port dashboard 8080); dashboard_port=${dashboard_port##*:}
dashboard_ready=false
for ((i=0; i<30; i++)); do
  if curl --silent --fail --max-time 2 "http://localhost:$dashboard_port/api/health" >/dev/null; then dashboard_ready=true; break; fi
  sleep 2
done
[[ "$dashboard_ready" == true ]] || { echo "The dashboard did not become ready. Check: docker compose logs dashboard"; exit 1; }
# Build the command-line images in the background on first run so ./soc is ready when needed.
if ! docker image inspect soc-toolkit-macos/volatility3:local >/dev/null 2>&1; then
  echo "Building command-line tool images in the background (log: cli-build.log)…"
  nohup docker compose --profile cli build > cli-build.log 2>&1 &
fi
dashboard_url="http://localhost:$dashboard_port"
soc_host=$(/usr/bin/sed -n 's/^SOC_HOSTNAME=//p' .env | tail -1)
caddy_dir=$(/usr/bin/sed -n 's/^CADDY_DIR=//p' .env | tail -1); caddy_dir=${caddy_dir:-$HOME/docker/caddy}; caddy_dir=${caddy_dir/#\~/$HOME}
if [[ -n "$soc_host" ]]; then
  # Start Caddy if the Admin Toolkit hasn't already; failures fall back to localhost.
  if [[ -f "$caddy_dir/docker-compose.yml" ]] && ! docker ps --format '{{.Names}}' | /usr/bin/grep -qx caddy; then
    docker compose --project-directory "$caddy_dir" -f "$caddy_dir/docker-compose.yml" up -d >/dev/null 2>&1 || true
  fi
  if ! /usr/bin/grep -Eq "^[[:space:]]*127\.0\.0\.1([[:space:]]+[^[:space:]]+)*[[:space:]]+$soc_host([[:space:]]|$)" /etc/hosts; then
    echo "Missing /etc/hosts entry for $soc_host. Add it with:"
    echo "  echo '127.0.0.1  $soc_host' | sudo tee -a /etc/hosts && sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder"
  elif curl --silent --fail --max-time 3 "https://$soc_host/api/health" >/dev/null; then
    dashboard_url="https://$soc_host"
  else
    echo "Caddy did not answer for $soc_host; using localhost. Check: docker logs caddy"
  fi
fi
echo "Dashboard: $dashboard_url  (fallback: http://localhost:$dashboard_port)"
echo "BloodHound and MobSF take a minute or two to initialize. The dashboard updates their availability."
echo "Command-line tools: ./soc help   ·   Reference: SOC-TOOLKIT-CHEATSHEET.txt"
open "$dashboard_url"
