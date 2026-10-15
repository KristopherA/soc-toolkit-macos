#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/usr/local/bin:$HOME/.docker/bin:/opt/homebrew/bin:$PATH"
docker compose stop
echo "SOC Toolkit stopped. Your data and settings are preserved."
