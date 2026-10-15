# Verification — 2026-10-15

Mac: Apple Silicon, Docker Desktop 29.8.2. Admin Toolkit running alongside (no port conflicts).

## Web tools

| Check | Result |
|---|---|
| Dashboard http://localhost:9080 `/api/health`, `/api/services`, `/api/status` | Pass; all 5 web tools report "ready" |
| BloodHound CE: `POST /api/v2/login` as admin with `BLOODHOUND_ADMIN_PASSWORD` | Pass, HTTP 200, `auth_expired: true` (password change forced) |
| MobSF `/login/` | Pass, HTTP 200 (after adding the `mobsf-init` volume-ownership step) |
| Nettacker `https://localhost:9083/` | Pass, HTTP 200 (self-signed TLS) |
| ClickGrab `/_stcore/health` | Pass, HTTP 200 |
| Email Check → Reacher | Partial. API path, secret header and disposable/syntax checks work. **Outbound TCP 25 is blocked from this network**, so SMTP probes time out (now reported as a clear 504 message). Reacher 0.11.7 also returned empty MX for example.com and mailinator.com while container DNS resolves both (gmail.com resolved correctly) — treat MX results as unreliable on this network. |

## Command-line tools (./soc)

| Tool | Test | Result |
|---|---|---|
| Volatility 3 | `vol -h`, plugin list | Pass (no memory image tested) |
| MVT | `mvt-ios download-iocs`, `mvt-android --help` | Pass; IOCs persist in volume |
| ClickGrab CLI | `clickgrab https://example.com --format json` | Pass; report written to cases/clickgrab |
| vt-cli | `vt file <hash>` without key | Pass (correct "API key is needed" error); no key available to test lookups |
| Amass | `enum -passive -d example.com`, `subs -names -d example.com` | Pass; enum is slow (>4 min), subs lists stored names |
| tlsx | `-json`, `-mismatched`, `-san` against example.com | Pass. `-san` cannot be combined with `-expired` (tool limitation) |
| dnsdiag | `dnsping -c 3 -s 1.1.1.1 example.com` | Pass |
| Grype / Syft | scan alpine:3.20 | Pass |
| Maigret | `--top-sites 15` | Pass (many sites deny automated checks) |
| Ghidra headless | import + analyze busybox ELF | Pass, about 2 minutes under Rosetta; image build about 15 minutes |

## Fixes made during verification
- Nettacker switched from the stale published image to a source build.
- MobSF crash-looped on a root-owned volume; added `mobsf-init`.
- Nettacker serves HTTPS; dashboard probe and link changed.
- MVT build failed on pyahocorasick (no ARM64 wheel); now compiled in a builder stage.
- Docker Desktop's resolver returned an empty MX answer for example.com; Reacher, Amass and tlsx now use public resolvers (`PUBLIC_DNS_1/2`).
- MobSF's built-in healthcheck calls host.docker.internal and gets HTTP 400; replaced with a localhost check (now healthy).
- 2026-10-15: dashboard published as https://soc.tools.kristopher.cloud through Caddy (route + proxy network alias soc-dashboard); verified /api/health 200 with valid wildcard certificate via --resolve.
