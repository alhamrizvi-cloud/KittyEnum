#!/usr/bin/env python3
"""KittyEnum Linux enumeration module.
This module is intended to run extra HTB/Linux-focused scans in a separate file,
so the main autoenum script can stay modular and extensible.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime

MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def info(msg):
    print(f"{MAGENTA}{BOLD}[LINUX]{RESET} {msg}")


def ok(msg):
    print(f"{GREEN}{BOLD}[OK]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}{BOLD}[WARN]{RESET} {msg}")


def run_cmd(cmd, outfile, label):
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    info(f"Running {label}")
    info(f"CMD → {' '.join(cmd)}")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(f"# {label}\n# CMD: {' '.join(cmd)}\n# START: {datetime.now()}\n\n")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            print(line, end="")
            f.write(line)
        proc.wait()
        f.write(f"\n# END: {datetime.now()}\n")
    if proc.returncode == 0:
        ok(f"Completed {label} → {outfile}")
    else:
        warn(f"{label} exited with {proc.returncode}")
    return proc.returncode


def nmap_linux_enum(target, outdir):
    outfile = os.path.join(outdir, "linux_nmap.txt")
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
    if not shutil_which("enum4linux"):
        warn("enum4linux not installed — skipping")
        return
    outfile = os.path.join(outdir, "enum4linux.txt")
    cmd = ["enum4linux", "-a", target]
    run_cmd(cmd, outfile, "Enum4linux")


def ssh_audit_scan(target, outdir):
    if not shutil_which("ssh-audit"):
        warn("ssh-audit not installed — skipping")
        return
    outfile = os.path.join(outdir, "ssh_audit.txt")
    cmd = ["ssh-audit", target]
    run_cmd(cmd, outfile, "SSH Audit")


def shutil_which(name):
    return subprocess.run(["which", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def main():
    parser = argparse.ArgumentParser(description="KittyEnum Linux enumeration module")
    parser.add_argument("target")
    parser.add_argument("--outdir", default="./recon-output")
    args = parser.parse_args()

    info(f"Linux enumeration module started for {args.target}")
    nmap_linux_enum(args.target, args.outdir)
    enum4linux_scan(args.target, args.outdir)
    ssh_audit_scan(args.target, args.outdir)
    ok("Linux enumeration module complete")


if __name__ == "__main__":
    main()
