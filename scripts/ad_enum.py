#!/usr/bin/env python3
"""KittyEnum Active Directory enumeration module.

This module performs AD recon using available tools and supports both anonymous
and credentialed enumeration.
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


def info(msg):
    print(f"{MAGENTA}{BOLD}[AD]{RESET} {msg}")


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


def cmd_exists(binary):
    return shutil.which(binary) is not None


def build_credential_args(username, password, domain):
    args = []
    if username is not None:
        args += ["-u", username]
    if password is not None:
        args += ["-p", password]
    if domain is not None:
        args += ["-d", domain]
    return args


def crackmapexec_smb(target, username, password, domain, outdir):
    if not cmd_exists("crackmapexec"):
        warn("crackmapexec not installed — skipping SMB/AD enumeration")
        return
    creds = build_credential_args(username, password, domain)
    outfile = os.path.join(outdir, "ad_crackmapexec_smb.txt")
    cmd = ["crackmapexec", "smb", target, "--shares", "--users", "--groups"] + creds
    run_cmd(cmd, outfile, "CrackMapExec SMB/AD")


def ldapdomaindump_scan(target, username, password, domain, outdir):
    if not cmd_exists("ldapdomaindump"):
        warn("ldapdomaindump not installed — skipping LDAP domain dump")
        return
    outfile = os.path.join(outdir, "ad_ldapdomaindump.txt")
    creds = build_credential_args(username, password, domain)
    if creds:
        cmd = ["ldapdomaindump", target] + creds
    else:
        cmd = ["ldapdomaindump", target]
    run_cmd(cmd, outfile, "LDAPDomainDump")


def bloodhound_scan(target, username, password, domain, outdir):
    if not cmd_exists("bloodhound-python"):
        warn("bloodhound-python not installed — skipping BloodHound collection")
        return
    if username is None or password is None:
        warn("BloodHound requires credentials — skipping")
        return
    outfile = os.path.join(outdir, "ad_bloodhound.txt")
    cmd = [
        "bloodhound-python",
        "-u", username,
        "-p", password,
        "-d", domain or target,
        "-ns", target,
        "-c", "All",
    ]
    run_cmd(cmd, outfile, "BloodHound Collector")


def rubeus_list(target, username, password, domain, outdir):
    # Placeholder for Rubeus / Kerberos tooling if available.
    if not cmd_exists("rubeus"):
        warn("rubeus not installed — skipping Kerberos enumeration")
        return
    if username is None or password is None:
        warn("Rubeus requires credentials — skipping")
        return
    outfile = os.path.join(outdir, "ad_rubeus.txt")
    cmd = [
        "rubeus",
        "kerberoast",
        "/usr:~",
        "/domain:" + (domain or target),
        "/user:" + username,
        "/password:" + password,
    ]
    run_cmd(cmd, outfile, "Rubeus Kerberoast")


def main():
    parser = argparse.ArgumentParser(description="KittyEnum Active Directory enumeration module")
    parser.add_argument("target", help="Domain controller or AD host")
    parser.add_argument("--username", help="Username for credentialed AD recon")
    parser.add_argument("--password", help="Password for credentialed AD recon")
    parser.add_argument("--domain", help="Domain name for AD recon")
    parser.add_argument("--outdir", default="./recon-output")
    args = parser.parse_args()

    info(f"Active Directory enumeration started for {args.target}")
    crackmapexec_smb(args.target, args.username, args.password, args.domain, args.outdir)
    ldapdomaindump_scan(args.target, args.username, args.password, args.domain, args.outdir)
    bloodhound_scan(args.target, args.username, args.password, args.domain, args.outdir)
    rubeus_list(args.target, args.username, args.password, args.domain, args.outdir)
    ok("Active Directory enumeration module complete")


if __name__ == "__main__":
    main()
