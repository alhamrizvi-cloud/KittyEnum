#!/usr/bin/env python3
"""
KittyEnum — Smart Recon & Enumeration Toolkit
Tested  : Parrot OS — paths verified against your machine

KittyEnum is a fast, opinionated enumeration helper for pentesters and CTF players.
It validates local tooling and wordlists, runs TCP/UDP scans, adds host mappings,
and performs directory, virtual-host, and parameter fuzzing in one pass.

USAGE:
  sudo python3 autoenum.py <IP> <HOSTNAME> [options]

EXAMPLES:
  sudo python3 autoenum.py 10.10.10.10 target.htb
  sudo python3 autoenum.py 10.10.10.10 target.htb -p 8080 --big
  sudo python3 autoenum.py 10.10.10.10 target.htb --no-udp --skip-verify

PHASES:
  0  Verify tools + wordlists
  1  nmap TCP  (-sS -sV -p-)
  2  nmap UDP  (-sU --top-ports 200)
  3  Add IP → /etc/hosts
  4  Gobuster dir     (common.txt or raft-medium)
  5  Gobuster dir     (rockyou.txt)
  6  Gobuster vhost   (subdomain enum)
  7  Gobuster enum    (users/files/dirs extended)
  8  FFUF dir         (fast double-check)
  9  FFUF vhost       (subdomains-top1million-5000.txt)
  10 FFUF params      (burp-parameter-names.txt)

All output → ./recon-<hostname>-<timestamp>/
"""

import subprocess, sys, os, shutil, argparse, socket, urllib.request, urllib.error, uuid
from datetime import datetime

# ─── PARROT OS VERIFIED WORDLIST PATHS ────────────────────────────────────────
SECLISTS    = "/usr/share/seclists"

WL_COMMON   = f"{SECLISTS}/Discovery/Web-Content/common.txt"
WL_RAFT_MED = f"{SECLISTS}/Discovery/Web-Content/raft-medium-directories.txt"
WL_RAFT_LOW = f"{SECLISTS}/Discovery/Web-Content/raft-medium-directories-lowercase.txt"
WL_BIG      = f"{SECLISTS}/Discovery/Web-Content/big.txt"
WL_SUB_5K   = f"{SECLISTS}/Discovery/DNS/subdomains-top1million-5000.txt"
WL_SUB_20K  = f"{SECLISTS}/Discovery/DNS/subdomains-top1million-20000.txt"
WL_SUB_BITQ = f"{SECLISTS}/Discovery/DNS/bitquark-subdomains-top100000.txt"
WL_PARAMS   = f"{SECLISTS}/Discovery/Web-Content/burp-parameter-names.txt"
WL_API      = f"{SECLISTS}/Discovery/Web-Content/common-api-endpoints-mazen160.txt"
WL_ROCKYOU  = "/usr/share/wordlists/rockyou.txt"
WL_DIRBUST  = f"{SECLISTS}/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt"

# ─── COLORS ───────────────────────────────────────────────────────────────────
R="\033[91m"; G="\033[92m"; Y="\033[93m"
B="\033[94m"; C="\033[96m"; M="\033[95m"; W="\033[0m"; BOLD="\033[1m"; DIM="\033[2m"

def banner():
    art = ""
    try:
        with open(os.path.join(os.path.dirname(__file__), "logo.txt"), encoding="utf-8") as f:
            art = f.read().rstrip()
    except Exception:
        art = "KittyEnum — Smart Recon & Enumeration Toolkit"

    print(f"""{M}{BOLD}{art}{W}\n{DIM}         KittyEnum — Smart Recon & Enumeration Toolkit{W}""")

def ph(n, msg):
    label = f"Phase {n} — {msg}"
    pad   = max(0, 56 - len(label))
    print(f"\n{BOLD}{C}╔{'═'*58}╗")
    print(f"║  {label}{' '*pad}║")
    print(f"╚{'═'*58}╝{W}")

def info(m):  print(f"  {B}[*]{W} {m}")
def ok(m):    print(f"  {G}[+]{W} {m}")
def warn(m):  print(f"  {Y}[!]{W} {m}")
def err(m):   print(f"  {R}[-]{W} {m}")
def sep():    print(f"  {DIM}{'─'*55}{W}")

# ─── TOOL / WORDLIST VERIFICATION ─────────────────────────────────────────────
TOOLS = {
    "nmap":      "sudo apt install nmap",
    "gobuster":  "sudo apt install gobuster",
    "ffuf":      "sudo apt install ffuf",
}

WORDLISTS = [
    ("common.txt",                WL_COMMON,   True),
    ("raft-medium-directories",   WL_RAFT_MED, False),
    ("big.txt",                   WL_BIG,      False),
    ("subdomains-top1m-5000",     WL_SUB_5K,   True),
    ("subdomains-top1m-20000",    WL_SUB_20K,  False),
    ("bitquark-subdomains-100k",  WL_SUB_BITQ, False),
    ("burp-parameter-names",      WL_PARAMS,   False),
    ("common-api-endpoints",      WL_API,      False),
    ("rockyou.txt",               WL_ROCKYOU,  True),
    ("dirbuster-big",             WL_DIRBUST,  False),
]

def verify_all():
    ph(0, "Verifying tools & wordlists")
    all_ok = True

    print(f"\n  {BOLD}── Tools ──────────────────────────────────────────────{W}")
    for tool, hint in TOOLS.items():
        path = shutil.which(tool)
        if path:
            try:
                ver = subprocess.check_output(
                    [tool, "--version"], stderr=subprocess.STDOUT, text=True
                ).split("\n")[0][:50]
            except Exception:
                ver = ""
            ok(f"{tool:<12} {G}FOUND{W}  {DIM}{path}{W}  {ver}")
        else:
            err(f"{tool:<12} {R}MISSING{W}  → {hint}")
            all_ok = False

    print(f"\n  {BOLD}── Wordlists ──────────────────────────────────────────{W}")
    for label, path, required in WORDLISTS:
        if os.path.isfile(path):
            kb    = os.path.getsize(path) // 1024
            lines = sum(1 for _ in open(path, "rb"))
            ok(f"{label:<35} {G}OK{W}  {lines:>8,} lines  ({kb:,} KB)")
        else:
            tag = f"{R}MISSING (required){W}" if required else f"{Y}MISSING (optional){W}"
            warn(f"{label:<35} {tag}  {DIM}{path}{W}")
            if required:
                all_ok = False

    # Special check — rockyou still gzipped?
    if os.path.isfile("/usr/share/wordlists/rockyou.txt.gz") and not os.path.isfile(WL_ROCKYOU):
        warn("rockyou.txt is still gzipped! Run:")
        warn("  sudo gunzip /usr/share/wordlists/rockyou.txt.gz")
        all_ok = False

    sep()
    if not all_ok:
        err("Fix missing required items above, then re-run.")
        sys.exit(1)
    ok("All checks passed — starting enumeration\n")

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def resolve_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None

def detect_wildcard(url):
    """Probe random path to detect wildcard redirect — returns (is_wildcard, body_size, status_code)."""
    fake = f"{url}/{uuid.uuid4()}.html"
    try:
        req    = urllib.request.Request(fake, headers={"User-Agent": "kittyenum/2.1"})
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        try:
            resp = opener.open(req, timeout=6)
            body = resp.read()
            return False, len(body), 200
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code in (301, 302, 307, 308):
                warn(f"Wildcard detected! Every path → {e.code}  (size={len(body)})")
                return True, len(body), e.code
            return False, len(body), e.code
    except Exception:
        return False, 0, 0

def run_cmd(cmd, outfile, label=""):
    """Stream command → terminal + file."""
    os.makedirs(os.path.dirname(os.path.abspath(outfile)), exist_ok=True)
    info(f"CMD  → {' '.join(cmd)}")
    info(f"FILE → {outfile}")
    sep()
    with open(outfile, "w") as f:
        f.write(f"# ── {label} ──\n")
        f.write(f"# CMD  : {' '.join(cmd)}\n")
        f.write(f"# START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        for line in proc.stdout:
            sys.stdout.write("    " + line)
            sys.stdout.flush()
            f.write(line)
        proc.wait()
        f.write(f"\n# END: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        rc = proc.returncode
    sep()
    if rc == 0:
        ok(f"Done → {outfile}")
    else:
        warn(f"Exit code {rc} — output saved: {outfile}")
    return rc

def wildcard_flags_gobuster(url):
    is_wc, size, code = detect_wildcard(url)
    flags = []
    if is_wc:
        flags = ["-b", str(code)]
        info(f"Auto-added gobuster flag: -b {code}")
    return flags

def wildcard_flags_ffuf(url):
    is_wc, size, code = detect_wildcard(url)
    flags = []
    if is_wc and size > 0:
        flags = ["-fs", str(size)]
        info(f"Auto-added ffuf flag: -fs {size}")
    return flags

def extract_open_ports(nmap_file):
    try:
        with open(nmap_file) as f:
            ports = [l.strip() for l in f if "/tcp" in l and "open" in l]
        if ports:
            ok("Open TCP ports:")
            for p in ports:
                print(f"    {G}→{W} {p}")
    except Exception:
        pass

def make_url(hostname, port):
    scheme = "https" if port == 443 else "http"
    return f"{scheme}://{hostname}" if port in (80, 443) else f"{scheme}://{hostname}:{port}"

# ─── PHASE 1: TCP NMAP ────────────────────────────────────────────────────────
def tcp_scan(target, outdir):
    ph(1, "TCP Scan — nmap -sS -sV -p-")
    warn("Requires root for SYN scan")
    base = f"{outdir}/nmap_tcp"
    cmd  = [
        "nmap", "-sS", "-sV", "-p-",
        "--min-rate", "3000", "--open",
        "-oN", f"{base}.txt",
        "-oG", f"{base}.gnmap",
        "-oX", f"{base}.xml",
        target
    ]
    run_cmd(cmd, f"{base}.txt", "TCP SYN + Service Scan")
    extract_open_ports(f"{base}.txt")

# ─── PHASE 2: UDP NMAP ────────────────────────────────────────────────────────
def udp_scan(target, outdir):
    ph(2, "UDP Scan — nmap -sU --top-ports 200")
    warn("Slow — requires root")
    base = f"{outdir}/nmap_udp"
    cmd  = [
        "nmap", "-sU", "--top-ports", "200",
        "--min-rate", "1000",
        "-oN", f"{base}.txt",
        "-oG", f"{base}.gnmap",
        target
    ]
    run_cmd(cmd, f"{base}.txt", "UDP Scan")

# ─── PHASE 3: /etc/hosts ──────────────────────────────────────────────────────
def add_hosts(ip, hostname):
    ph(3, f"Adding {ip} → {hostname} to /etc/hosts")
    try:
        content = open("/etc/hosts").read()
    except PermissionError:
        err("Cannot read /etc/hosts"); return

    for line in content.splitlines():
        if ip in line and hostname in line:
            ok(f"Already present: {line.strip()}"); return

    entry = f"{ip}\t{hostname}"
    try:
        with open("/etc/hosts", "a") as f:
            f.write(f"\n# autoenum.py\n{entry}\n")
        ok(f"Added: {entry}")
        resolved = resolve_ip(hostname)
        if resolved == ip:
            ok(f"Confirmed: {hostname} → {resolved}")
        else:
            warn(f"Resolution returned {resolved} — verify /etc/hosts")
    except PermissionError:
        warn("Permission denied — run with sudo or add manually:")
        print(f"\n    {Y}echo '{entry}' | sudo tee -a /etc/hosts{W}\n")

# ─── PHASE 4: GOBUSTER DIR (common / raft-medium) ─────────────────────────────
def gobuster_dir(hostname, port, outdir, big=False):
    ph(4, "Gobuster dir — common.txt / raft-medium")
    wl      = WL_RAFT_MED if (big and os.path.isfile(WL_RAFT_MED)) else WL_COMMON
    url     = make_url(hostname, port)
    outfile = f"{outdir}/gobuster_dir.txt"
    info(f"Wordlist : {wl}")
    info(f"Target   : {url}")
    wc_flags = wildcard_flags_gobuster(url)
    cmd = [
        "gobuster", "dir",
        "-u", url, "-w", wl,
        "-t", "60",
        "-x", "php,html,txt,js,json,bak,zip,conf,xml,sh",
        "--no-error", "--timeout", "10s",
        "-o", outfile,
    ] + wc_flags
    run_cmd(cmd, outfile, "Gobuster Dir")

# ─── PHASE 5: GOBUSTER DIR (rockyou.txt) ──────────────────────────────────────
def gobuster_rockyou(hostname, port, outdir):
    ph(5, "Gobuster dir — rockyou.txt")
    if not os.path.isfile(WL_ROCKYOU):
        warn(f"rockyou.txt not found — skipping  ({WL_ROCKYOU})")
        warn("Run: sudo gunzip /usr/share/wordlists/rockyou.txt.gz")
        return
    url     = make_url(hostname, port)
    outfile = f"{outdir}/gobuster_rockyou.txt"
    lines   = sum(1 for _ in open(WL_ROCKYOU, "rb"))
    info(f"Wordlist : {WL_ROCKYOU}  ({lines:,} lines)")
    warn("14M lines — this will take time. Ctrl+C to stop early, results saved so far.")
    wc_flags = wildcard_flags_gobuster(url)
    cmd = [
        "gobuster", "dir",
        "-u", url, "-w", WL_ROCKYOU,
        "-t", "80",
        "-x", "php,html,txt,bak,zip,sh",
        "--no-error", "--timeout", "10s",
        "-o", outfile,
    ] + wc_flags
    run_cmd(cmd, outfile, "Gobuster Dir (rockyou)")

# ─── PHASE 6: GOBUSTER VHOST (subdomain enum) ─────────────────────────────────
def gobuster_vhost(target, hostname, port, outdir):
    ph(6, "Gobuster vhost — subdomain enumeration")
    wl = next((w for w in [WL_SUB_5K, WL_SUB_20K, WL_SUB_BITQ] if os.path.isfile(w)), None)
    if not wl:
        warn("No subdomain wordlist found — skipping"); return

    url     = make_url(hostname, port)
    outfile = f"{outdir}/gobuster_vhost.txt"
    lines   = sum(1 for _ in open(wl, "rb"))
    info(f"Wordlist : {wl}  ({lines:,} entries)")
    info(f"Trying   : FUZZ.{hostname}")
    cmd = [
        "gobuster", "vhost",
        "-u", url, "-w", wl,
        "-t", "60",
        "--append-domain",
        "--no-error",
        "-o", outfile,
    ]
    run_cmd(cmd, outfile, "Gobuster VHost")
    # Print hits
    try:
        hits = [l.strip() for l in open(outfile) if "Found:" in l or "Status: 200" in l]
        if hits:
            ok(f"Subdomains found ({len(hits)}):")
            for h in hits[:20]:
                print(f"    {G}→{W} {h}")
    except Exception:
        pass

# ─── PHASE 7: GOBUSTER ENUM (extended — api/files/dirbuster) ──────────────────
def gobuster_enum(hostname, port, outdir):
    ph(7, "Gobuster enum — extended (API + DirBuster wordlist)")

    url = make_url(hostname, port)
    wc_flags = wildcard_flags_gobuster(url)

    # 7a: API endpoints
    if os.path.isfile(WL_API):
        outfile = f"{outdir}/gobuster_api.txt"
        info("Scanning API endpoints...")
        cmd = [
            "gobuster", "dir",
            "-u", url, "-w", WL_API,
            "-t", "60",
            "-x", "json,php,txt",
            "--no-error", "--timeout", "10s",
            "-o", outfile,
        ] + wc_flags
        run_cmd(cmd, outfile, "Gobuster API Endpoints")
    else:
        warn(f"API wordlist not found — skipping  ({WL_API})")

    # 7b: DirBuster big list
    if os.path.isfile(WL_DIRBUST):
        outfile = f"{outdir}/gobuster_dirbuster.txt"
        lines   = sum(1 for _ in open(WL_DIRBUST, "rb"))
        info(f"DirBuster big list ({lines:,} lines) — may take a while...")
        cmd = [
            "gobuster", "dir",
            "-u", url, "-w", WL_DIRBUST,
            "-t", "60",
            "-x", "php,html,txt,bak,zip,conf",
            "--no-error", "--timeout", "10s",
            "-o", outfile,
        ] + wc_flags
        run_cmd(cmd, outfile, "Gobuster DirBuster Big")
    else:
        warn(f"DirBuster wordlist not found — skipping  ({WL_DIRBUST})")

# ─── PHASE 8: FFUF DIR ────────────────────────────────────────────────────────
def ffuf_dir(hostname, port, outdir):
    ph(8, "FFUF dir — fast directory fuzz")
    url     = make_url(hostname, port)
    outfile = f"{outdir}/ffuf_dir.txt"
    wc_flags = wildcard_flags_ffuf(url)
    cmd = [
        "ffuf",
        "-u", f"{url}/FUZZ",
        "-w", WL_COMMON,
        "-t", "150",
        "-mc", "200,201,204,301,302,307,401,403,405,500",
        "-ic", "-c",
        "-o", outfile, "-of", "md",
    ] + wc_flags
    run_cmd(cmd, outfile, "FFUF Dir")

# ─── PHASE 9: FFUF VHOST ──────────────────────────────────────────────────────
def ffuf_vhost(target, hostname, port, outdir):
    ph(9, "FFUF vhost — subdomain fuzzing")
    wl = next((w for w in [WL_SUB_5K, WL_SUB_20K] if os.path.isfile(w)), None)
    if not wl:
        warn("No subdomain wordlist — skipping"); return

    url     = make_url(target, port)
    outfile = f"{outdir}/ffuf_vhost.txt"
    lines   = sum(1 for _ in open(wl, "rb"))
    info(f"Wordlist : {wl}  ({lines:,} entries)")
    info(f"Host hdr : FUZZ.{hostname}")
    wc_flags = wildcard_flags_ffuf(url)
    if not wc_flags:
        wc_flags = ["-fs", "0"]
        warn("No wildcard size detected — using -fs 0. Adjust if noisy.")
    cmd = [
        "ffuf",
        "-u", url,
        "-H", f"Host: FUZZ.{hostname}",
        "-w", wl,
        "-t", "100",
        "-mc", "200,201,301,302,307,401,403,405",
        "-ic", "-c",
        "-o", outfile, "-of", "md",
    ] + wc_flags
    run_cmd(cmd, outfile, "FFUF VHost")
    # Print found subdomains
    try:
        hits = [l for l in open(outfile) if "| 2" in l or "| 3" in l or "| 4" in l]
        if hits:
            ok(f"Subdomains found by ffuf ({len(hits)}):")
            for h in hits[:20]:
                print(f"    {G}→{W} {h.strip()}")
    except Exception:
        pass

# ─── PHASE 10: FFUF PARAMS ────────────────────────────────────────────────────
def ffuf_params(hostname, port, param_path, outdir):
    ph(10, "FFUF params — GET parameter fuzz")
    if not os.path.isfile(WL_PARAMS):
        warn(f"burp-parameter-names.txt not found — skipping"); return
    url     = make_url(hostname, port)
    outfile = f"{outdir}/ffuf_params.txt"
    cmd = [
        "ffuf",
        "-u", f"{url}{param_path}?FUZZ=autoenum_test",
        "-w", WL_PARAMS,
        "-t", "80",
        "-mc", "200,301,302,400,401,403,405,500",
        "-ic", "-c",
        "-o", outfile, "-of", "md",
    ]
    run_cmd(cmd, outfile, "FFUF Params")

# ─── PHASE 11/12: HTB LINUX ENUMERATION ───────────────────────────────────────
def nmap_linux_enum(target, outdir):
    ph(11, "Nmap Linux — service/script enumeration")
    outfile = f"{outdir}/nmap_linux_enum.txt"
    cmd = [
        "nmap",
        "-sV",
        "-p", "22,80,111,139,445,2049",
        "--script", "default,discovery,auth,vuln,smb-enum*",
        "--min-rate", "1000",
        "-oN", outfile,
        target,
    ]
    run_cmd(cmd, outfile, "Nmap Linux Enumeration")


def enum4linux_scan(target, outdir):
    ph(12, "Enum4linux — SMB/host enumeration")
    if not shutil.which("enum4linux"):
        warn("enum4linux not installed — skipping")
        return
    outfile = f"{outdir}/enum4linux.txt"
    cmd = ["enum4linux", "-a", target]
    run_cmd(cmd, outfile, "Enum4linux")


def ssh_audit_scan(target, outdir):
    if not shutil.which("ssh-audit"):
        warn("ssh-audit not installed — skipping")
        return
    ph(13, "SSH audit")
    outfile = f"{outdir}/ssh_audit.txt"
    cmd = ["ssh-audit", target]
    run_cmd(cmd, outfile, "SSH Audit")


def linux_enum(target, hostname, outdir):
    ph("⧗", "HTB Linux enumeration")
    nmap_linux_enum(target, outdir)
    enum4linux_scan(target, outdir)
    ssh_audit_scan(target, outdir)

# ─── SUMMARY ──────────────────────────────────────────────────────────────────
def summary(outdir, target, hostname, start_time):
    elapsed = datetime.now() - start_time
    ph("✓", "Enumeration Complete")
    print(f"\n  {BOLD}Target   :{W} {target}")
    print(f"  {BOLD}Hostname :{W} {hostname}")
    print(f"  {BOLD}Duration :{W} {str(elapsed).split('.')[0]}")
    print(f"  {BOLD}Output   :{W} {outdir}/\n")
    print(f"  {BOLD}── Output Files ───────────────────────────────────────{W}")
    total = 0
    for root, _, files in os.walk(outdir):
        for fn in sorted(files):
            fp   = os.path.join(root, fn)
            size = os.path.getsize(fp)
            total += size
            rel  = fp.replace(outdir + "/", "")
            kb   = size // 1024
            bar  = "░" * min(kb // 10, 30)
            print(f"  {G}•{W} {rel:<38} {kb:>6} KB  {C}{bar}{W}")
    sep()
    print(f"  {BOLD}Total:{W} {total//1024:,} KB across {len(os.listdir(outdir))} files\n")
    print(f"  {Y}Quick greps:{W}")
    print(f"  {DIM}grep -rih 'admin\\|login\\|secret\\|api\\|token\\|password\\|backup' {outdir}/{W}")
    print(f"  {DIM}cat {outdir}/gobuster_vhost.txt | grep Found{W}")
    print(f"  {DIM}cat {outdir}/ffuf_vhost.txt{W}\n")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    banner()
    p = argparse.ArgumentParser(
        description="KittyEnum — Smart Recon & Enumeration Toolkit",
        formatter_class=argparse.RawTextHelpFormatter
    )
    p.add_argument("target",          help="Target IP  e.g. 10.10.10.10")
    p.add_argument("hostname",        help="Hostname   e.g. target.htb")
    p.add_argument("-p","--port",     type=int, default=80,  help="Web port (default: 80)")
    p.add_argument("--no-udp",        action="store_true",   help="Skip UDP scan")
    p.add_argument("--no-hosts",      action="store_true",   help="Skip /etc/hosts entry")
    p.add_argument("--no-rockyou",    action="store_true",   help="Skip gobuster rockyou scan")
    p.add_argument("--no-vhost",      action="store_true",   help="Skip all vhost/subdomain phases")
    p.add_argument("--no-enum",       action="store_true",   help="Skip gobuster extended enum (phase 7)")
    p.add_argument("--no-params",     action="store_true",   help="Skip ffuf param fuzz")
    p.add_argument("--big",           action="store_true",   help="Use raft-medium for gobuster dir")
    p.add_argument("--param-path",    default="/",           help="Path for param fuzz (default: /)")
    p.add_argument("--skip-verify",   action="store_true",   help="Skip tool/wordlist verification")
    p.add_argument("--linux",         action="store_true",   help="Run extra HTB Linux enumeration phases")
    args = p.parse_args()

    start  = datetime.now()
    stamp  = start.strftime("%Y%m%d-%H%M%S")
    outdir = f"./recon-{args.hostname}-{stamp}"
    os.makedirs(outdir, exist_ok=True)

    print(f"  {BOLD}Target   :{W} {args.target}")
    print(f"  {BOLD}Hostname :{W} {args.hostname}")
    print(f"  {BOLD}Port     :{W} {args.port}")
    print(f"  {BOLD}Output   :{W} {outdir}/")
    print(f"  {BOLD}Started  :{W} {start.strftime('%Y-%m-%d %H:%M:%S')}")

    if not args.skip_verify:
        verify_all()

    tcp_scan(args.target, outdir)

    if not args.no_udp:
        udp_scan(args.target, outdir)

    if not args.no_hosts:
        add_hosts(args.target, args.hostname)

    gobuster_dir(args.hostname, args.port, outdir, big=args.big)

    if not args.no_rockyou:
        gobuster_rockyou(args.hostname, args.port, outdir)

    if not args.no_vhost:
        gobuster_vhost(args.target, args.hostname, args.port, outdir)

    if not args.no_enum:
        gobuster_enum(args.hostname, args.port, outdir)

    ffuf_dir(args.hostname, args.port, outdir)

    if not args.no_vhost:
        ffuf_vhost(args.target, args.hostname, args.port, outdir)

    if not args.no_params:
        ffuf_params(args.hostname, args.port, args.param_path, outdir)

    if args.linux:
        linux_enum(args.target, args.hostname, outdir)

    summary(outdir, args.target, args.hostname, start)

if __name__ == "__main__":
    main()
