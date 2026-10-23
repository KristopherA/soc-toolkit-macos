# SOC Toolkit — macOS edition

SOC analysis tools on one dashboard, in one Docker Compose project, next to the Docker Admin Toolkit. Five web tools stay running; eleven command-line tools run on demand in throwaway containers through `./soc`. All web ports bind to **127.0.0.1**. Nothing overlaps the Admin Toolkit (CyberChef, File Triage, SO-CRATES, EML Analyzer, DFIR-IRIS and the rest stay there; the dashboard links back to it).

## Start

1. Double-click **start.command** (or run `./start.command`). On first run it creates `.env` with fresh secrets, copies tool sources from GitHubProjects into `src/`, builds and starts the web tools, opens the dashboard, and builds the CLI images in the background (`cli-build.log`).
2. Visit **https://soc.tools.kristopher.cloud** (or http://localhost:9080 as a fallback).
3. Stop with **stop.command**. Data, settings and `cases/` are kept.

Ghidra is not built automatically (about 15 minutes under Rosetta): `docker compose --profile ghidra build ghidra`.

## Web tools

All web tools sit behind the shared Caddy proxy (`~/docker/caddy`, wildcard `*.tools.kristopher.cloud` certificate). The 127.0.0.1 ports stay as a fallback, and the dashboard links use the HTTPS names whenever `SOC_DOMAIN` is set.

| Tool | HTTPS via Caddy | Fallback | Sign-in |
|---|---|---|---|
| Dashboard | https://soc.tools.kristopher.cloud | http://localhost:9080 | None |
| BloodHound CE | https://bloodhound.tools.kristopher.cloud | :9081 | `admin` / `BLOODHOUND_ADMIN_PASSWORD`; change forced at first login |
| MobSF | https://mobsf.tools.kristopher.cloud | :9082 | `mobsf` / `MOBSF_ADMIN_PASSWORD` |
| OWASP Nettacker | https://nettacker.tools.kristopher.cloud | https://localhost:9083 | paste `NETTACKER_API_KEY` |
| ClickGrab | https://clickgrab.tools.kristopher.cloud | :9084 | None |
| Email Check | https://soc.tools.kristopher.cloud/email-check.html | :9080 | None |

Caddy reaches the dashboard, BloodHound, MobSF and Nettacker on the external `proxy` network (aliases `soc-*`). ClickGrab is reached through its host port (`host.docker.internal:9084`), so the container that fetches hostile pages never joins the network shared with the Admin Toolkit. Reacher, Postgres and Neo4j are not exposed.

Each name needs a 127.0.0.1 line in /etc/hosts. On first run start.command offers to add any missing names (it asks for your Mac password through sudo), then opens https://soc.tools.kristopher.cloud. If you decline, or Caddy does not answer, it opens http://localhost:9080 instead.

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
./soc hayabusa dfir-timeline -d /case/ir-042/evtx -o /case/ir-042/timeline.csv -w
./soc detections check                          # make check in DETECTIONS_DIR (sigma check + convert)
./soc sigma convert -t lucene -p /detections/pipelines/snort-graylog.yml /detections/rules
./soc pcapgen http --host evil.example --uri /gate.php -o /case/pcaps/c2.pcap
./soc snort-replay /case/rules/local.rules /case/pcaps/c2.pcap   # add --json for Graylog fields
```

### Detection engineering loop

1. Write or edit a Snort rule (for example `cases/rules/local.rules`).
2. Build a PCAP that should fire it with `pcapgen`, plus one that should not (a near-miss).
3. `./soc snort-replay --check` validates syntax; `./soc snort-replay rules pcap` shows the alerts.
4. `--json` prints the same alert_json fields the Graylog `parse_json` pipeline receives, so Sigma field names can be checked against real output.
5. `./soc detections check` lints and converts the Sigma rules before they become Graylog event definitions.

`DETECTIONS_DIR` in `.env` points at your detections repo and is mounted at `/detections` (read-write for `sigma`/`detections`, read-only for `snort`). Unset, it falls back to `cases/detections`.

Full reference: **SOC-TOOLKIT-CHEATSHEET.txt**.

## Layout

```
compose.yml            services; CLI tools under the "cli" profile, Ghidra under "ghidra"
.env / .env.example    ports, secrets, tags, GHIDRA_DIR, GITHUB_PROJECTS_DIR, DETECTIONS_DIR, PUBLIC_DNS_1/2
setup.sh               creates .env; later runs only append new settings
start.command / stop.command
soc                    CLI wrapper (docker compose run --rm ...)
sync-sources.sh        copies source-built tools from GitHubProjects into src/
dashboard/             launcher, availability probes, Email Check proxy
build/                 Dockerfiles for ClickGrab, vt-cli, MVT, Volatility 3, Hayabusa, sigma-cli, Snort 3, pcapgen
cases/                 evidence and output (git-ignored; keep out of iCloud)
```

## Safety notes

- **ClickGrab and Email Check contact the target** from this Mac's public IP. ClickGrab runs on its own Docker network (`lures`) away from the other tools.
- **Nettacker, Amass and tlsx** generate traffic toward targets. Use them only on organization-owned assets or with written authorization.
- **Grype and Syft** mount the Docker socket read-only so they can scan local images.
- **Email Check needs outbound TCP 25.** It is blocked on the network this was tested on, so mailbox probes time out; syntax and disposable-domain checks still work. Reacher can use a SOCKS5 proxy for SMTP if needed.
- **Public resolvers.** Docker Desktop's resolver returned an empty MX answer for example.com (likely the internal split-horizon zone), so Reacher, Amass and tlsx use `PUBLIC_DNS_1/2` for an external view.
- **Snort, sigma-cli and pcapgen run with no network** (`network_mode: none`). Hayabusa needs network only for `update-rules`.
- Real-world PCAPs from malware-traffic-analysis.net and similar can contain live malware in reassembled streams; keep them in `cases/` and never extract carved files on the Mac.
- MVT has no USB support in Docker on a Mac: use iOS backups and AndroidQF output.

## Updating

```
./sync-sources.sh && ./soc build          # source-built tools after updating GitHubProjects
docker compose --profile cli pull && docker compose up -d   # published images
```

Versions and digests: SOURCES.md. Test results: VERIFICATION.md.
