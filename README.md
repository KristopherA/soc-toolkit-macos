# SOC Toolkit — macOS edition

SOC analysis tools on one dashboard, in one Docker Compose project, next to the Docker Admin Toolkit. Five web tools stay running; eleven command-line tools run on demand in throwaway containers through `./soc`. All web ports bind to **127.0.0.1**. Nothing overlaps the Admin Toolkit (CyberChef, File Triage, SO-CRATES, EML Analyzer, DFIR-IRIS and the rest stay there; the dashboard links back to it).

## Start

1. Double-click **start.command** (or run `./start.command`). On first run it creates `.env` with fresh secrets, copies tool sources from GitHubProjects into `src/`, builds and starts the web tools, opens the dashboard, and builds the CLI images in the background (`cli-build.log`).
2. Visit **https://soc.tools.kristopher.cloud** (Caddy, wildcard Let's Encrypt cert) or **http://localhost:9080**. The HTTPS name needs `127.0.0.1  soc.tools.kristopher.cloud` in /etc/hosts; start.command prints the command if it is missing.
3. Stop with **stop.command**. Data, settings and `cases/` are kept.

Ghidra is not built automatically (about 15 minutes under Rosetta): `docker compose --profile ghidra build ghidra`.

## Web tools

| Tool | Address | Sign-in |
|---|---|---|
| Dashboard | http://localhost:9080 | None |
| BloodHound CE | http://localhost:9081 | `admin` / `BLOODHOUND_ADMIN_PASSWORD`; change forced at first login |
| MobSF | http://localhost:9082 | `mobsf` / `MOBSF_ADMIN_PASSWORD` |
| OWASP Nettacker | https://localhost:9083 (self-signed) | paste `NETTACKER_API_KEY` |
| ClickGrab | http://localhost:9084 | None |
| Email Check (Reacher) | http://localhost:9080/email-check.html | None |

Print a value: `sed -n 's/^MOBSF_ADMIN_PASSWORD=//p' .env`

## Command-line tools

Put evidence in `./cases`; every tool sees it as `/case`. Run `./soc help` for the list.

```
./soc vol -f /case/mem.raw windows.pstree        # Volatility 3
./soc ghidra /case/gh proj -import /case/x.exe   # Ghidra headless
./soc mvt-ios check-backup -o /case/out /case/backup
./soc clickgrab "https://suspect.example" --format html
./soc vt file <sha256>                          # needs VTCLI_APIKEY in .env
./soc amass enum -passive -d example.com -silent -timeout 15
./soc tlsx -u example.com -json -silent
./soc dnsping -c 5 -s 1.1.1.1 example.com
./soc grype graylog/graylog:6.1 -q
./soc syft graylog/graylog:6.1 -o table
./soc maigret jsmith --top-sites 300 --html
```

Full reference: **SOC-TOOLKIT-CHEATSHEET.txt**.

## Layout

```
compose.yml            services; CLI tools under the "cli" profile, Ghidra under "ghidra"
.env / .env.example    ports, secrets, tags, GHIDRA_DIR, GITHUB_PROJECTS_DIR, PUBLIC_DNS_1/2
setup.sh               creates .env; later runs only append new settings
start.command / stop.command
soc                    CLI wrapper (docker compose run --rm ...)
sync-sources.sh        copies source-built tools from GitHubProjects into src/
dashboard/             launcher, availability probes, Email Check proxy
build/                 Dockerfiles for ClickGrab, vt-cli, MVT, Volatility 3
cases/                 evidence and output (git-ignored; keep out of iCloud)
```

## Safety notes

- **ClickGrab and Email Check contact the target** from this Mac's public IP. ClickGrab runs on its own Docker network (`lures`) away from the other tools.
- **Nettacker, Amass and tlsx** generate traffic toward targets. Use them only on organization-owned assets or with written authorization.
- **Grype and Syft** mount the Docker socket read-only so they can scan local images.
- **Email Check needs outbound TCP 25.** It is blocked on the network this was tested on, so mailbox probes time out; syntax and disposable-domain checks still work. Reacher can use a SOCKS5 proxy for SMTP if needed.
- **Public resolvers.** Docker Desktop's resolver returned an empty MX answer for example.com (likely the internal split-horizon zone), so Reacher, Amass and tlsx use `PUBLIC_DNS_1/2` for an external view.
- MVT has no USB support in Docker on a Mac: use iOS backups and AndroidQF output.

## Updating

```
./sync-sources.sh && ./soc build          # source-built tools after updating GitHubProjects
docker compose --profile cli pull && docker compose up -d   # published images
```

Versions and digests: SOURCES.md. Test results: VERIFICATION.md.
