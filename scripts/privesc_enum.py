#!/usr/bin/env python3
"""KittyEnum privilege escalation helper module.
This module runs extra local enumeration helpers and checks for privesc tools.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def info(msg):
    print(f"{CYAN}{BOLD}[PRIVESC]{RESET} {msg}")


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


def cmd_exists(command):
    return subprocess.run(["which", command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def sudo_enumeration(outdir):
    outfile = os.path.join(outdir, "sudo_list.txt")
    cmd = ["sudo", "-l"]
    run_cmd(cmd, outfile, "Sudo Privilege Check")


def linpeas_scan(outdir):
    linpeas = find_script(["linpeas.sh", "linpeas"], [".", "/tmp", "/usr/local/bin", "/usr/bin"])
    if not linpeas:
        warn("linpeas not found — skipping")
        return
    outfile = os.path.join(outdir, "linpeas.txt")
    run_cmd([linpeas], outfile, "LinPEAS scan")


def linenum_scan(outdir):
    linenum = find_script(["linenum.sh", "linenum"], [".", "/tmp", "/usr/local/bin", "/usr/bin"])
    if not linenum:
        warn("linenum not found — skipping")
        return
    outfile = os.path.join(outdir, "linenum.txt")
    run_cmd([linenum], outfile, "Linux Enumeration Script")


def searchsploit_suggestions(outdir):
    if not cmd_exists("searchsploit"):
        warn("searchsploit not installed — skipping")
        return
    outfile = os.path.join(outdir, "searchsploit_suggestions.txt")
    run_cmd(["searchsploit", "linux kernel", "--nmap"], outfile, "Searchsploit Linux Kernel Suggestions")


def find_script(names, paths):
    for path in paths:
        for name in names:
            candidate = os.path.join(path, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return None


def main():
    parser = argparse.ArgumentParser(description="KittyEnum privilege escalation helper module")
    parser.add_argument("--outdir", default="./recon-output")
    args = parser.parse_args()

    info("Privilege escalation module started")
    sudo_enumeration(args.outdir)
    linpeas_scan(args.outdir)
    linenum_scan(args.outdir)
    searchsploit_suggestions(args.outdir)
    ok("Privilege escalation module complete")


if __name__ == "__main__":
    main()
