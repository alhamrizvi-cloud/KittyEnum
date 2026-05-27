#!/usr/bin/env python3
"""KittyEnum subdomain enumeration module.
This module runs passive and active subdomain discovery, plus HTTP probing.
"""

import argparse
import os
import shutil
import subprocess
from datetime import datetime

MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

DEFAULT_DNS_WORDLIST = "/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt"
DEFAULT_RESOLVERS = "./resolvers.txt"


def info(msg):
    print(f"{MAGENTA}{BOLD}[SUBDOM]{RESET} {msg}")


def ok(msg):
    print(f"{GREEN}{BOLD}[OK]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}{BOLD}[WARN]{RESET} {msg}")


def cmd_exists(name):
    return shutil.which(name) is not None


def write_output(path, title, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        f.write(content)


def run_cmd(cmd, outfile, label, env=None):
    info(f"{label}")
    info(f"CMD → {' '.join(cmd)}")
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    write_output(outfile, label, result.stdout)
    if result.returncode == 0:
        ok(f"{label} completed")
    else:
        warn(f"{label} exited {result.returncode}")
    return result.returncode


def merge_lists(target_file, source_files):
    found = set()
    for path in source_files:
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                entry = line.strip()
                if entry:
                    found.add(entry)
    sorted_lines = sorted(found)
    write_output(target_file, "Merged subdomain list", "\n".join(sorted_lines) + "\n")
    ok(f"Merged {len(sorted_lines)} unique entries into {os.path.basename(target_file)}")
    return target_file


def passive_enumeration(target, args):
    info("Running passive subdomain enumeration")
    outputs = []
    base = args.outdir

    if cmd_exists("subfinder"):
        outfile = os.path.join(base, "subfinder_subs.txt")
        run_cmd(["subfinder", "-d", target, "-all", "-recursive", "-silent", "-o", outfile], outfile, "Subfinder passive enumeration")
        outputs.append(outfile)
    else:
        warn("subfinder not installed — skipping")

    if cmd_exists("amass"):
        outfile = os.path.join(base, "amass_passive_subs.txt")
        run_cmd(["amass", "enum", "-passive", "-d", target, "-o", outfile], outfile, "Amass passive enumeration")
        outputs.append(outfile)
    else:
        warn("amass not installed — skipping passive amass")

    if cmd_exists("assetfinder"):
        outfile = os.path.join(base, "assetfinder_subs.txt")
        run_cmd(["assetfinder", "--subs-only", target], outfile, "Assetfinder passive enumeration")
        outputs.append(outfile)
    else:
        warn("assetfinder not installed — skipping")

    if cmd_exists("findomain"):
        outfile = os.path.join(base, "findomain_subs.txt")
        run_cmd(["findomain", "-t", target, "-q"], outfile, "Findomain passive enumeration")
        outputs.append(outfile)
    else:
        warn("findomain not installed — skipping")

    if cmd_exists("chaos"):
        outfile = os.path.join(base, "chaos_subs.txt")
        run_cmd(["chaos", "-d", target, "-silent"], outfile, "Chaos passive enumeration")
        outputs.append(outfile)
    else:
        warn("chaos not installed — skipping")

    if cmd_exists("curl") and cmd_exists("jq"):
        outfile = os.path.join(base, "crtsh_subs.txt")
        cmd = ["bash", "-lc", f"curl -s 'https://crt.sh/?q=%25.{target}&output=json' | jq -r '.[].name_value' | sed 's/\\*\\.//g' | sort -u"]
        rc = run_cmd(cmd, outfile, "crt.sh passive enumeration")
        if rc == 0:
            outputs.append(outfile)
    else:
        warn("curl or jq missing — skipping crt.sh enumeration")

    if cmd_exists("github-subdomains"):
        if args.github_token:
            outfile = os.path.join(base, "github_subs.txt")
            run_cmd(["github-subdomains", "-d", target, "-t", args.github_token, "-o", outfile], outfile, "GitHub subdomains enumeration")
            outputs.append(outfile)
        else:
            warn(".github token not provided — skipping github-subdomains")
    else:
        warn("github-subdomains not installed — skipping")

    merged = merge_lists(os.path.join(base, "passive_subdomains.txt"), outputs)
    return merged


def active_enumeration(target, args):
    info("Running active subdomain discovery")
    outputs = []
    base = args.outdir
    wordlist = args.wordlist or DEFAULT_DNS_WORDLIST
    resolvers = args.resolvers or DEFAULT_RESOLVERS

    if cmd_exists("amass"):
        outfile = os.path.join(base, "amass_active_subs.txt")
        run_cmd(["amass", "enum", "-active", "-d", target, "-o", outfile], outfile, "Amass active enumeration")
        outputs.append(outfile)
    else:
        warn("amass not installed — skipping active amass")

    passive_file = os.path.join(base, "passive_subdomains.txt")
    if os.path.isfile(passive_file) and cmd_exists("dnsx"):
        outfile = os.path.join(base, "dnsx_resolved.txt")
        run_cmd(["dnsx", "-silent", "-l", passive_file], outfile, "DNSX resolve passive subdomains")
        outputs.append(outfile)
    elif not os.path.isfile(passive_file):
        warn("passive_subdomains.txt not found — skipping dnsx pass")
    else:
        warn("dnsx not installed — skipping DNSX resolve")

    if cmd_exists("gobuster") and os.path.isfile(wordlist):
        outfile = os.path.join(base, "gobuster_dns.txt")
        run_cmd(["gobuster", "dns", "-d", target, "-w", wordlist, "-t", "50", "--timeout", "3s", "-o", outfile], outfile, "Gobuster DNS bruteforce")
        outputs.append(outfile)
    else:
        warn("gobuster not installed or wordlist missing — skipping gobuster dns")

    if cmd_exists("puredns") and os.path.isfile(wordlist) and os.path.isfile(resolvers):
        outfile = os.path.join(base, "puredns_subs.txt")
        run_cmd(["puredns", "bruteforce", wordlist, target, "-r", resolvers, "--write", outfile], outfile, "PureDNS bruteforce")
        outputs.append(outfile)
    else:
        warn("puredns, wordlist, or resolvers missing — skipping puredns")

    if cmd_exists("massdns") and os.path.isfile(resolvers):
        raw = os.path.join(base, "massdns_raw.txt")
        outfile = os.path.join(base, "massdns_subs.txt")
        run_cmd(["massdns", "-r", resolvers, "-t", "A", "-o", "S", os.path.join(base, "subdomains.txt")], raw, "MassDNS active resolution")
        if os.path.isfile(raw):
            run_cmd(["bash", "-lc", f"grep ' A ' {raw} | cut -d' ' -f1 | sed 's/\\.$//' | sort -u > {outfile}"], outfile, "MassDNS parse results")
            outputs.append(outfile)
    else:
        warn("massdns or resolvers missing — skipping massdns")

    if cmd_exists("shuffledns") and os.path.isfile(wordlist) and os.path.isfile(resolvers):
        outfile = os.path.join(base, "shuffledns_subs.txt")
        run_cmd(["shuffledns", "-d", target, "-w", wordlist, "-r", resolvers, "-silent"], outfile, "Shuffledns bruteforce")
        outputs.append(outfile)
    else:
        warn("shuffledns, wordlist, or resolvers missing — skipping shuffledns")

    merged = merge_lists(os.path.join(base, "active_subdomains.txt"), outputs)
    return merged


def probe_website(args, subdomain_file):
    info("Running HTTP probing and live host discovery")
    base = args.outdir
    if not os.path.isfile(subdomain_file):
        warn(f"Resolved input list {subdomain_file} not found — skipping probe")
        return

    if cmd_exists("httpx"):
        outfile = os.path.join(base, "live_websites_httpx.txt")
        run_cmd(["httpx", "-l", subdomain_file, "-p", "80,443,8080,8443", "-silent", "-title", "-sc", "-ip", "-o", outfile], outfile, "HTTPX probing")
    else:
        warn("httpx not installed — skipping HTTPX")

    if cmd_exists("httprobe"):
        outfile2 = os.path.join(base, "live_websites_httprobe.txt")
        run_cmd(["bash", "-lc", f"cat {subdomain_file} | httprobe"], outfile2, "Httprobe probing")
    else:
        warn("httprobe not installed — skipping httprobe")

    login_file = os.path.join(base, "login_endpoints.txt")
    if os.path.isfile(os.path.join(base, "live_websites_httpx.txt")):
        run_cmd(["bash", "-lc", f"cat {os.path.join(base, 'live_websites_httpx.txt')} | grep -Ei 'login|admin|signin|dashboard' | sort -u > {login_file}"], login_file, "Endpoint filtering")
        ok("Filtered login/admin endpoints")


def main():
    parser = argparse.ArgumentParser(description="KittyEnum subdomain enumeration module")
    parser.add_argument("target", help="Target domain")
    parser.add_argument("--outdir", default="./recon-output")
    parser.add_argument("--github-token", help="GitHub token for github-subdomains")
    parser.add_argument("--wordlist", default=DEFAULT_DNS_WORDLIST, help="DNS wordlist for brute force")
    parser.add_argument("--resolvers", default=DEFAULT_RESOLVERS, help="Resolver list for active DNS tools")
    parser.add_argument("--passive", action="store_true", help="Run passive subdomain enumeration")
    parser.add_argument("--active", action="store_true", help="Run active subdomain enumeration")
    parser.add_argument("--probe", action="store_true", help="Run HTTP probing against resolved hosts")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    info(f"Subdomain enumeration module started for {args.target}")

    if not args.passive and not args.active and not args.probe:
        args.passive = args.active = args.probe = True

    passive_file = None
    if args.passive:
        passive_file = passive_enumeration(args.target, args)

    active_file = None
    if args.active:
        active_file = active_enumeration(args.target, args)

    if args.probe:
        probe_source = active_file or passive_file
        if probe_source:
            probe_website(args, probe_source)
        else:
            warn("No subdomain list available for probing")

    ok("Subdomain enumeration module complete")


if __name__ == "__main__":
    main()
