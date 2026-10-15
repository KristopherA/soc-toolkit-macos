"""SOC Toolkit dashboard: launcher, bounded availability probes, and the Email Check
proxy to the internal Reacher API. No Docker socket; the only secret it holds is the
Reacher header secret, which never leaves the private Docker network."""
import concurrent.futures
import json
import ssl
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent / "static"

# (id, name, category, description, port env, default port, probe URL, icon, open path)
SERVICES = [
    ("bloodhound", "BloodHound CE", "Identity", "Map Active Directory and Entra ID attack paths from SharpHound or AzureHound collections.", "BLOODHOUND_PORT", 9081, "http://bloodhound:8080/ui/login", "graph", "/ui/login"),
    ("mobsf", "MobSF", "Mobile", "Static analysis of suspicious APK, IPA and AAB files: permissions, trackers, secrets, malware signals.", "MOBSF_PORT", 9082, "http://mobsf:8000/login/", "phone", "/"),
    ("nettacker", "OWASP Nettacker", "Exposure", "Web-UI scanner to validate exposure of hosts you own: ports, services, CVEs, weak configs.", "NETTACKER_PORT", 9083, "https://nettacker:5000/", "radar", "/"),
    ("clickgrab", "ClickGrab", "Phishing", "Analyze fake CAPTCHA / ClickFix lure pages: redirects, clipboard payloads, PowerShell, IOCs.", "CLICKGRAB_PORT", 9084, "http://clickgrab:8501/_stcore/health", "hook", "/"),
    ("email-check", "Email Check", "Phishing", "Verify whether a sender or reply-to address really exists (SMTP, MX, disposable, role account).", "DASHBOARD_PORT", 9080, "http://reacher:8080/version", "mailcheck", "/email-check.html"),
]

# Command-line tools: run on demand with ./soc <tool>. Not probed; containers exit when done.
CLI = [
    ("volatility3", "Volatility 3", "Forensics", "Memory image analysis: processes, network, injected code, persistence.", "./soc vol -f /case/mem.raw windows.pslist", "memory"),
    ("ghidra", "Ghidra Headless", "Forensics", "Batch reverse-engineering of a sample with Ghidra's headless analyzer.", "./soc ghidra /case/ghidra proj -import /case/sample.exe", "binary"),
    ("mvt", "MVT", "Mobile", "Check iPhone backups and Android AndroidQF dumps for spyware indicators.", "./soc mvt-ios check-backup -o /case/mvt-out /case/backup", "phone"),
    ("clickgrab-cli", "ClickGrab CLI", "Phishing", "Batch-analyze lure URLs or pull the live ClickFix feed; reports to cases/.", "./soc clickgrab \"https://suspect.example\" --format html", "hook"),
    ("vtcli", "VirusTotal CLI", "Threat Intel", "Hash, domain, IP and URL reputation from VirusTotal (API key in .env).", "./soc vt file <sha256>", "lookup"),
    ("amass", "Amass", "Exposure", "Passive external attack-surface mapping: subdomains and related infrastructure.", "./soc amass enum -passive -d example.com", "radar"),
    ("tlsx", "tlsx", "Exposure", "TLS certificate and configuration inspection: expiry, self-signed, SANs, versions.", "./soc tlsx -u example.com -san -expired -self-signed", "lock"),
    ("dnsdiag", "dnsdiag", "Exposure", "DNS latency, hijack and resolver-path diagnostics (dnsping, dnstraceroute, dnseval).", "./soc dnsping -c 5 -s 1.1.1.1 example.com", "dns"),
    ("grype", "Grype", "Vulnerability", "Scan container images, folders or SBOMs for known CVEs.", "./soc grype graylog/graylog:6.1", "bug"),
    ("syft", "Syft", "Vulnerability", "Generate a software bill of materials (SBOM) for an image or folder.", "./soc syft graylog/graylog:6.1 -o table", "list"),
    ("hayabusa", "Hayabusa", "Detection", "Windows event log (EVTX) triage: Sigma and Hayabusa rules to a CSV/JSONL timeline.", "./soc hayabusa dfir-timeline -d /case/evtx -o /case/timeline.csv -w", "log"),
    ("sigma", "sigma-cli", "Detection", "Lint Sigma rules and convert them to Lucene queries for Graylog; runs your detections Makefile.", "./soc detections check", "shield"),
    ("snort", "Snort 3 Replay", "Detection", "Replay PCAPs through your Snort 3 rules offline; alert_fast or Graylog-ready alert_json.", "./soc snort-replay /case/rules/local.rules /case/pcaps/test.pcap", "wave"),
    ("pcapgen", "pcapgen", "Detection", "Build small known-content test PCAPs: HTTP, DNS, TLS SNI, TCP/UDP payloads, port-scan fan-out.", "./soc pcapgen tls --sni canary.example.com -o /case/pcaps/sni.pcap", "wave"),
    ("maigret", "Maigret", "OSINT", "Find accounts by username across 3,000+ sites for impersonation cases.", "./soc maigret jsmith --top-sites 200", "person"),
]

# External lookups that complement the Admin Toolkit's sandbox and URL-check links. Never probed.
LINKS = [
    ("admin-toolkit", "Admin Toolkit", "Workspace", "CyberChef, File Triage, EML Analyzer, SO-CRATES, DFIR-IRIS and more.", "http://localhost:8080/", "home"),
    ("abuseipdb", "AbuseIPDB", "Threat Intel", "Community abuse reports and confidence score for an IP address.", "https://www.abuseipdb.com/", "globe"),
    ("greynoise", "GreyNoise", "Threat Intel", "Tells internet-wide scanner noise apart from targeted activity.", "https://viz.greynoise.io/", "globe"),
    ("shodan", "Shodan", "Threat Intel", "What an IP or your own range exposes to the internet.", "https://www.shodan.io/", "globe"),
    ("otx", "AlienVault OTX", "Threat Intel", "Community pulses linking IOCs to campaigns and actors.", "https://otx.alienvault.com/", "globe"),
    ("malwarebazaar", "MalwareBazaar", "Threat Intel", "abuse.ch hash lookups with family tags and YARA hits.", "https://bazaar.abuse.ch/", "globe"),
    ("threatfox", "ThreatFox", "Threat Intel", "abuse.ch IOC database: C2 servers, payload URLs, botnet infrastructure.", "https://threatfox.abuse.ch/", "globe"),
    ("attack", "MITRE ATT&CK", "Reference", "Adversary techniques for mapping detections and incident timelines.", "https://attack.mitre.org/", "book"),
    ("lolbas", "LOLBAS", "Reference", "Windows living-off-the-land binaries, scripts and libraries.", "https://lolbas-project.github.io/", "book"),
    ("gtfobins", "GTFOBins", "Reference", "Unix binaries abused to bypass restrictions or escalate privileges.", "https://gtfobins.github.io/", "book"),
]

def port_of(s):
    return int(os.getenv(s[4], s[5]))

def service_url(s):
    # Nettacker serves HTTPS with its own self-signed certificate.
    scheme = "https" if s[6].startswith("https:") else "http"
    return f"{scheme}://localhost:{port_of(s)}{s[8]}"

def service_catalog():
    return [dict(id=s[0], name=s[1], category=s[2], description=s[3], port=port_of(s),
                 url=service_url(s), icon=s[7]) for s in SERVICES] + \
           [dict(id=c[0], name=c[1], category=c[2], description=c[3], command=c[4], icon=c[5], cli=True) for c in CLI] + \
           [dict(id=l[0], name=l[1], category=l[2], description=l[3], url=l[4], icon=l[5], external=True) for l in LINKS]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

# Internal HTTPS probes (Nettacker) use a self-signed certificate on the private Docker network.
_PROBE_TLS = ssl.create_default_context()
_PROBE_TLS.check_hostname = False
_PROBE_TLS.verify_mode = ssl.CERT_NONE
OPENER = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}),
                                     urllib.request.HTTPSHandler(context=_PROBE_TLS))

def probe(service):
    started = time.monotonic()
    try:
        request = urllib.request.Request(service[6], headers={"User-Agent": "SOC-Toolkit-Dashboard/1.0"})
        try:
            with OPENER.open(request, timeout=4) as response:
                code = response.status
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
        state = "ready" if 200 <= code < 400 or code in (401, 403) else "attention"
        return service[0], {"state": state, "httpCode": code, "latencyMs": round((time.monotonic() - started) * 1000)}
    except (OSError, urllib.error.URLError, ValueError):
        return service[0], {"state": "unavailable", "httpCode": None, "latencyMs": None}

CACHE = {"checkedAt": None, "services": {}}
CACHE_LOCK = threading.Lock()

def check_services():
    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SERVICES)) as pool:
            states = dict(pool.map(probe, SERVICES))
        with CACHE_LOCK:
            CACHE.update(checkedAt=int(time.time()), services=states)
        time.sleep(15)

# Email Check: one lookup at a time; Reacher talks SMTP to the target's mail server.
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}$")
REACHER_URL = os.getenv("REACHER_URL", "http://reacher:8080/v0/check_email")
REACHER_SECRET = os.getenv("REACHER_SECRET", "")
CHECK_LOCK = threading.Lock()

def email_check(body):
    try:
        email = str(json.loads(body or b"{}").get("email", "")).strip()
    except (ValueError, AttributeError):
        return 400, {"error": "Send JSON like {\"email\": \"name@example.com\"}."}
    if not EMAIL_RE.match(email):
        return 400, {"error": "That does not look like a single email address."}
    if not CHECK_LOCK.acquire(blocking=False):
        return 429, {"error": "Another check is running. Try again when it finishes."}
    try:
        headers = {"Content-Type": "application/json", "User-Agent": "SOC-Toolkit-Dashboard/1.0"}
        if REACHER_SECRET:
            headers["x-reacher-secret"] = REACHER_SECRET
        request = urllib.request.Request(REACHER_URL, data=json.dumps({"to_email": email}).encode(), headers=headers, method="POST")
        try:
            with OPENER.open(request, timeout=150) as response:
                return 200, json.loads(response.read(2_000_000))
        except urllib.error.HTTPError as error:
            detail = error.read(2000).decode("utf-8", "replace")
            error.close()
            return 502, {"error": f"Reacher returned HTTP {error.code}.", "detail": detail}
    except (socket.timeout, TimeoutError):
        return 504, {"error": "No answer within 150 seconds. Outbound TCP 25 is probably blocked from this network, so the mail server could not be asked."}
    except urllib.error.URLError as error:
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            return 504, {"error": "No answer within 150 seconds. Outbound TCP 25 is probably blocked from this network, so the mail server could not be asked."}
        return 503, {"error": "Reacher is not reachable. Check: docker compose logs reacher"}
    except (OSError, ValueError):
        return 503, {"error": "Reacher is not reachable. Check: docker compose logs reacher"}
    finally:
        CHECK_LOCK.release()

STATIC = ("/", "/index.html", "/style.css", "/app.js", "/favicon.svg", "/email-check.html", "/email-check.js")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if getattr(self, "_revalidate", False):
            self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        super().end_headers()

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self.send_json(200, {"ok": True})
        if path == "/api/services":
            return self.send_json(200, service_catalog())
        if path == "/api/status":
            with CACHE_LOCK:
                return self.send_json(200, {"checkedAt": CACHE["checkedAt"], "services": dict(CACHE["services"])})
        if path in STATIC:
            self._revalidate = True
            return super().do_GET()
        return self.send_error(404)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/email-check":
            return self.send_error(404)
        # Same-origin only: the browser always sends Origin on a fetch POST.
        origin = self.headers.get("Origin", "")
        host = self.headers.get("Host", "")
        if origin and urlsplit(origin).netloc != host:
            return self.send_json(403, {"error": "Cross-origin request refused."})
        length = int(self.headers.get("Content-Length") or 0)
        if length > 4096:
            return self.send_json(413, {"error": "Request too large."})
        code, data = email_check(self.rfile.read(length))
        return self.send_json(code, data)

if __name__ == "__main__":
    threading.Thread(target=check_services, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
