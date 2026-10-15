# Sources and versions

Checked 2026-10-15 on Apple Silicon (Docker Desktop 29.8.2, ARM64). Tags marked `latest` are configurable in `.env`; the digest below is what was verified.

## Published images

| Image | Version seen | Digest | Arch | Licence / notes |
|---|---|---|---|---|
| specterops/bloodhound:latest | API v9.8.0 | sha256:88aeb602…f4d301 | ARM64 + AMD64 | Apache-2.0 |
| neo4j:4.4 | 4.4 | sha256:6a5b0f7d…103ce4 | ARM64 + AMD64 | GPLv3 (Community) |
| postgres:16-alpine | 16 | sha256:721873c3…6080ea | multi | PostgreSQL |
| opensecurity/mobile-security-framework-mobsf:latest | 4.x | sha256:69851c52…2c7b | ARM64 + AMD64 | GPL-3.0 |
| reacherhq/backend:latest | 0.11.7 | sha256:6f05f029…c8153 | **AMD64 only** (Rosetta) | AGPL-3.0, with a commercial licence required for some commercial use. Internal organizational use: confirm with Reacher's licence terms before relying on it. |
| owaspamass/amass:latest | v5.1.1 | sha256:79c06d6c…8111a | ARM64 + AMD64 | Apache-2.0 |
| projectdiscovery/tlsx:latest | v1.2.2 | sha256:8a329810…bf4dbc | ARM64 + AMD64 | MIT |
| anchore/grype:latest | 0.120.1 | sha256:e4a44ef4…aebbbe | ARM64 + AMD64 | Apache-2.0 |
| anchore/syft:latest | 1.54.1 | sha256:3eb5379b…1aa | ARM64 + AMD64 | Apache-2.0 |
| soxoj/maigret:latest | 0.6.6 | sha256:def84769…a40 | ARM64 + AMD64 | MIT |
| busybox:1.37 | 1.37 | sha256:bdf57e52…f82e | multi | GPL-2.0 (MobSF volume-permission helper) |

`owasp/nettacker:latest` was rejected: the published image dates from 2024 and pulled as AMD64. Nettacker is built from source instead.

## Built from local source (copied into src/ by sync-sources.sh)

| Tool | Source in GitHubProjects | Version / commit | Dockerfile |
|---|---|---|---|
| Volatility 3 | Forensics-DFIR/volatility3 | 2.8.1, git 8d7edfdc | build/volatility3 (python:3.12-slim + yara-python, capstone, pycryptodome) |
| MVT | Forensics-DFIR/mvt-main | 2.6.1 (zip, 2026-05-05) | build/mvt (multi-stage; compiles pyahocorasick, no USB toolchain) |
| ClickGrab | Malware-Analysis-RE/ClickGrab-main | zip, 2026-05-05 | build/clickgrab (python:3.12-slim, non-root) |
| vt-cli | Threat-Intel-Hunting/vt-cli | git d340558 | build/vtcli (Go 1.23 build, distroless nonroot) |
| dnsdiag | Network-Security/dnsdiag | 2.9.0, git c996a70 | upstream Dockerfile (python:3.14-alpine) |
| OWASP Nettacker | Network-Security/Nettacker | 0.4.1, git a2157ee | upstream Dockerfile |
| Ghidra | Malware-Analysis-RE/ghidra_12.0_PUBLIC (built in place, GHIDRA_DIR) | 12.0 PUBLIC | upstream docker/Dockerfile, platform linux/amd64 (decompiler is x86_64 only) |

Excluded when copying: ClickGrab's nightly_reports/docs/public (620+ MB of published reports), a stray Python virtualenv inside the Nettacker folder, and test/doc folders.
