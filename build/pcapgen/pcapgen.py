#!/usr/local/bin/python3
"""pcapgen - write small test PCAPs with known content for IDS rule testing.

  pcapgen http --host evil.example --uri /gate.php --ua "Mozilla/4.0" -o /case/pcaps/c2.pcap
  pcapgen dns  --qname bad.example -o /case/pcaps/dns.pcap
  pcapgen tls  --sni canary.example.com -o /case/pcaps/sni.pcap
  pcapgen tcp  --dport 4444 --payload 'whoami\\n' -o /case/pcaps/shell.pcap
  pcapgen udp  --dport 53 --payload '\\x00\\x01' -o /case/pcaps/udp.pcap
  pcapgen scan --ports 1-200 -o /case/pcaps/scan.pcap

Defaults use documentation/private ranges: client 10.20.1.55, server 203.0.113.10 (TEST-NET-3).
--count repeats the session (repeated-SID tests); --append adds to an existing PCAP.
"""
import argparse, codecs, ipaddress, os, random, struct, sys, time
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import IP, TCP, UDP, DNS, DNSQR, DNSRR, Ether, Raw, wrpcap

CLIENT_MAC, SERVER_MAC = "02:00:00:00:00:01", "02:00:00:00:00:02"
MSS = 1400

class Clock:
    def __init__(self, start): self.t = start
    def tick(self, d=0.001): self.t += d; return self.t

def frame(src, dst, l4, clock, from_client=True):
    eth = Ether(src=CLIENT_MAC if from_client else SERVER_MAC, dst=SERVER_MAC if from_client else CLIENT_MAC)
    p = eth / IP(src=src, dst=dst, ttl=64 if from_client else 52) / l4
    p.time = clock.tick()
    return p

def tcp_session(a, clock, client_data=b"", server_data=b"", dport=80):
    """Handshake, client data, server data, FIN/ACK teardown."""
    c, s = a.src, a.dst
    sport = a.sport or random.randint(49152, 65000)
    cs, ss = random.randint(1, 2**31), random.randint(1, 2**31)
    pk = [frame(c, s, TCP(sport=sport, dport=dport, flags="S", seq=cs, options=[("MSS", 1460)]), clock),
          frame(s, c, TCP(sport=dport, dport=sport, flags="SA", seq=ss, ack=cs + 1, options=[("MSS", 1460)]), clock, False),
          frame(c, s, TCP(sport=sport, dport=dport, flags="A", seq=cs + 1, ack=ss + 1), clock)]
    cs += 1; ss += 1
    for data, client in ((client_data, True), (server_data, False)):
        for i in range(0, len(data), MSS):
            chunk = data[i:i + MSS]
            if client:
                pk.append(frame(c, s, TCP(sport=sport, dport=dport, flags="PA", seq=cs, ack=ss) / Raw(chunk), clock))
                cs += len(chunk)
                pk.append(frame(s, c, TCP(sport=dport, dport=sport, flags="A", seq=ss, ack=cs), clock, False))
            else:
                pk.append(frame(s, c, TCP(sport=dport, dport=sport, flags="PA", seq=ss, ack=cs) / Raw(chunk), clock, False))
                ss += len(chunk)
                pk.append(frame(c, s, TCP(sport=sport, dport=dport, flags="A", seq=cs, ack=ss), clock))
    pk += [frame(c, s, TCP(sport=sport, dport=dport, flags="FA", seq=cs, ack=ss), clock),
           frame(s, c, TCP(sport=dport, dport=sport, flags="FA", seq=ss, ack=cs + 1), clock, False),
           frame(c, s, TCP(sport=sport, dport=dport, flags="A", seq=cs + 1, ack=ss + 1), clock)]
    return pk

def unescape(s):
    return codecs.escape_decode(s.encode())[0] if s else b""

def http(a, clock):
    lines = [f"{a.method} {a.uri} HTTP/1.1", f"Host: {a.host}", f"User-Agent: {a.ua}", "Accept: */*"]
    lines += a.header
    body = unescape(a.body)
    if body: lines.append(f"Content-Length: {len(body)}")
    req = ("\r\n".join(lines) + "\r\n\r\n").encode() + body
    rbody = unescape(a.resp_body)
    resp = (f"HTTP/1.1 {a.status} OK\r\nServer: nginx\r\nContent-Type: text/html\r\nContent-Length: {len(rbody)}\r\n\r\n").encode() + rbody
    return tcp_session(a, clock, req, resp, a.dport)

def dns(a, clock):
    sport = a.sport or random.randint(49152, 65000)
    qid = random.randint(1, 65535)
    q = DNS(id=qid, rd=1, qd=DNSQR(qname=a.qname, qtype=a.qtype))
    ans = DNSRR(rrname=a.qname, type="A", ttl=300, rdata=a.answer) if a.answer and a.qtype == "A" else None
    r = DNS(id=qid, qr=1, rd=1, ra=1, rcode=0 if ans or a.qtype != "A" else 3, qd=DNSQR(qname=a.qname, qtype=a.qtype), an=ans)
    return [frame(a.src, a.dst, UDP(sport=sport, dport=a.dport) / q, clock),
            frame(a.dst, a.src, UDP(sport=a.dport, dport=sport) / r, clock, False)]

def client_hello(sni):
    name = sni.encode()
    ext_sni = struct.pack("!HHHBH", 0x0000, len(name) + 5, len(name) + 3, 0, len(name)) + name
    ext_groups = struct.pack("!HHH", 0x000a, 4, 2) + struct.pack("!H", 0x001d)
    ext_sig = struct.pack("!HHH", 0x000d, 6, 4) + struct.pack("!HH", 0x0403, 0x0804)
    ext_ver = struct.pack("!HHB", 0x002b, 5, 4) + struct.pack("!HH", 0x0304, 0x0303)
    ext_alpn = struct.pack("!HHHB", 0x0010, 11, 9, 8) + b"http/1.1"
    exts = ext_sni + ext_groups + ext_sig + ext_ver + ext_alpn
    ciphers = struct.pack("!HHHH", 6, 0x1301, 0x1302, 0xc02f)
    body = struct.pack("!H", 0x0303) + os.urandom(32) + b"\x20" + os.urandom(32) + ciphers + b"\x01\x00" + struct.pack("!H", len(exts)) + exts
    hs = b"\x01" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x01" + struct.pack("!H", len(hs)) + hs

def server_hello():
    ext_ver = struct.pack("!HHH", 0x002b, 2, 0x0304)
    body = struct.pack("!H", 0x0303) + os.urandom(32) + b"\x20" + os.urandom(32) + struct.pack("!H", 0x1301) + b"\x00" + struct.pack("!H", len(ext_ver)) + ext_ver
    hs = b"\x02" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x03" + struct.pack("!H", len(hs)) + hs

def tls(a, clock):
    return tcp_session(a, clock, client_hello(a.sni), server_hello(), a.dport)

def tcp(a, clock):
    return tcp_session(a, clock, unescape(a.payload), unescape(a.reply), a.dport)

def udp(a, clock):
    sport = a.sport or random.randint(49152, 65000)
    pk = [frame(a.src, a.dst, UDP(sport=sport, dport=a.dport) / Raw(unescape(a.payload)), clock)]
    if a.reply: pk.append(frame(a.dst, a.src, UDP(sport=a.dport, dport=sport) / Raw(unescape(a.reply)), clock, False))
    return pk

def parse_ports(spec):
    ports = []
    for part in spec.split(","):
        lo, _, hi = part.partition("-")
        ports += range(int(lo), int(hi or lo) + 1)
    if not ports or min(ports) < 1 or max(ports) > 65535: raise argparse.ArgumentTypeError("ports must be 1-65535")
    return ports

def scan(a, clock):
    sport = a.sport or random.randint(49152, 65000)
    open_ports = set(a.open)
    pk = []
    for p in a.ports:
        seq = random.randint(1, 2**31)
        pk.append(frame(a.src, a.dst, TCP(sport=sport, dport=p, flags="S", seq=seq), clock))
        flags = "SA" if p in open_ports else "RA"
        pk.append(frame(a.dst, a.src, TCP(sport=p, dport=sport, flags=flags, seq=0 if flags == "RA" else random.randint(1, 2**31), ack=seq + 1), clock, False))
    return pk

def ip_arg(v):
    ipaddress.ip_address(v); return v

def main():
    ap = argparse.ArgumentParser(prog="pcapgen", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-o", "--out", required=True, help="output PCAP, e.g. /case/pcaps/test.pcap")
    common.add_argument("--src", type=ip_arg, default="10.20.1.55", help="client IP (default 10.20.1.55)")
    common.add_argument("--dst", type=ip_arg, default="203.0.113.10", help="server IP (default 203.0.113.10)")
    common.add_argument("--sport", type=int, default=0, help="client port (default random 49152-65000)")
    common.add_argument("--count", type=int, default=1, help="repeat the session N times")
    common.add_argument("--interval", type=float, default=1.0, help="seconds between repeats (default 1)")
    common.add_argument("--append", action="store_true", help="append to an existing PCAP")
    common.add_argument("--seed", type=int, help="fixed random seed for reproducible ports/sequence numbers")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("http", parents=[common], help="HTTP request and response")
    p.add_argument("--dport", type=int, default=80); p.add_argument("--method", default="GET")
    p.add_argument("--host", default="www.example.com"); p.add_argument("--uri", default="/")
    p.add_argument("--ua", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    p.add_argument("--header", action="append", default=[], help="extra header line, repeatable: 'X-Id: 1'")
    p.add_argument("--body", default="", help="request body (\\x escapes allowed)")
    p.add_argument("--status", type=int, default=200); p.add_argument("--resp-body", default="<html>ok</html>")
    p.set_defaults(fn=http)

    p = sub.add_parser("dns", parents=[common], help="DNS query and response over UDP")
    p.add_argument("--dport", type=int, default=53); p.add_argument("--qname", required=True)
    p.add_argument("--qtype", default="A"); p.add_argument("--answer", default="198.51.100.7", help="A record answer ('' for NXDOMAIN)")
    p.set_defaults(fn=dns)

    p = sub.add_parser("tls", parents=[common], help="TLS ClientHello with SNI, plus ServerHello")
    p.add_argument("--dport", type=int, default=443); p.add_argument("--sni", required=True)
    p.set_defaults(fn=tls)

    p = sub.add_parser("tcp", parents=[common], help="TCP session with a raw payload")
    p.add_argument("--dport", type=int, required=True); p.add_argument("--payload", default="")
    p.add_argument("--reply", default="", help="server payload"); p.set_defaults(fn=tcp)

    p = sub.add_parser("udp", parents=[common], help="UDP datagram (and optional reply)")
    p.add_argument("--dport", type=int, required=True); p.add_argument("--payload", default="")
    p.add_argument("--reply", default=""); p.set_defaults(fn=udp)

    p = sub.add_parser("scan", parents=[common], help="SYN scan fan-out from one source")
    p.add_argument("--ports", type=parse_ports, default=parse_ports("1-100"), help="e.g. 1-1024 or 22,80,443")
    p.add_argument("--open", type=parse_ports, default=[], help="ports that answer SYN-ACK")
    p.set_defaults(fn=scan)

    a = ap.parse_args()
    if a.seed is not None: random.seed(a.seed)
    out_dir = os.path.dirname(os.path.abspath(a.out))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    clock = Clock(time.time())
    packets = []
    for i in range(max(1, a.count)):
        packets += a.fn(a, clock)
        clock.tick(a.interval)
    wrpcap(a.out, packets, append=a.append and os.path.exists(a.out))
    print(f"pcapgen: wrote {len(packets)} packets ({a.cmd} x{max(1, a.count)}) to {a.out}")

if __name__ == "__main__":
    main()
