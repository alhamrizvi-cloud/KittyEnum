gi#!/usr/bin/env python3
"""KittyEnum privilege escalation helper module.
This module performs SSH-friendly local enumeration for Linux privilege escalation.
It avoids installing external root-level tools and focuses on user-level checks.
"""

import argparse
import os
import shutil
import subprocess
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


def write_output(path, header, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {header}\n# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        f.write(content)


def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result.returncode, result.stdout


def cmd_exists(command):
    return shutil.which(command) is not None


def collect_system_info(outdir):
    info("Collecting system information")
    commands = {
        "os_release": ["cat", "/etc/os-release"],
        "uname": ["uname", "-a"],
        "hostname": ["hostname"],
        "uptime": ["uptime"],
        "id": ["id"],
        "whoami": ["whoami"],
        "env": ["printenv"],
        "current_path": ["bash", "-lc", "echo $PATH"],
    }
    for name, cmd in commands.items():
        rc, out = run_cmd(cmd)
        write_output(os.path.join(outdir, f"privesc_{name}.txt"), f"System info: {name}", out)


def collect_user_info(outdir):
    info("Collecting user and account information")
    commands = {
        "groups": ["groups"],
        "passwd": ["cat", "/etc/passwd"],
        "shadow_access": ["bash", "-lc", "ls -l /etc/shadow 2>/dev/null || true"],
        "shell_history": ["bash", "-lc", "ls -1 ~/.bash_history ~/.zsh_history ~/.mysql_history 2>/dev/null || true"],
        "sudo_list": ["sudo", "-n", "-l"],
    }
    for name, cmd in commands.items():
        rc, out = run_cmd(cmd)
        if name == "sudo_list" and rc != 0:
            warning = "sudo unavailable or requires password; try sudo -l manually if needed\n"
            out = warning + out
        write_output(os.path.join(outdir, f"privesc_{name}.txt"), f"User info: {name}", out)


def find_files(command, outfile, label, outdir):
    info(f"Running {label}")
    rc, out = run_cmd(command)
    write_output(os.path.join(outdir, outfile), label, out)
    return rc


def collect_privilege_vectors(outdir):
    info("Collecting local privilege escalation vectors")
    find_commands = {
        "writable_files.txt": ["bash", "-lc", "find / -xdev -type f -perm -2 -user $(id -u) 2>/dev/null | head -n 200"],
        "world_writable_files.txt": ["bash", "-lc", "find / -xdev -type f -perm -2 2>/dev/null | head -n 200"],
        "suid_files.txt": ["bash", "-lc", "find / -xdev -perm -4000 -type f 2>/dev/null | sort | head -n 200"],
        "sgid_files.txt": ["bash", "-lc", "find / -xdev -perm -2000 -type f 2>/dev/null | sort | head -n 200"],
        "capabilities.txt": ["bash", "-lc", "which getcap >/dev/null 2>&1 && getcap -r / 2>/dev/null | head -n 200 || true"],
        "interesting_sudoers.txt": ["bash", "-lc", r"grep -RInE '^([^#].*NOPASSWD|[^#].*ALL\(ALL\)|[^#].*sudo' /etc/sudoers* 2>/dev/null || true"],
        "cron_jobs.txt": ["bash", "-lc", "ls -al /etc/cron* 2>/dev/null; crontab -l 2>/dev/null || true"],
        "systemd_timers.txt": ["bash", "-lc", "systemctl list-timers --all 2>/dev/null || true"],
        "ssh_keys.txt": ["bash", "-lc", r"find ~ -maxdepth 3 \( -name 'id_rsa' -o -name 'id_dsa' -o -name 'authorized_keys' \) 2>/dev/null | sort | head -n 100"],
        "interesting_files.txt": ["bash", "-lc", r"find / -xdev \( -name '*.conf' -o -name '*.log' -o -name '*.sql' -o -name '*.bak' \) 2>/dev/null | grep -E 'passwd|pass|secret|cred|key|token' | head -n 200 || true"],
    }
    for outfile, cmd in find_commands.items():
        find_files(cmd, outfile, f"Privilege escalation vector: {outfile}", outdir)


def collect_ssh_and_keys(outdir):
    info("Collecting SSH and key material hints")
    commands = {
        "ssh_authorized_keys.txt": ["bash", "-lc", r"find / -xdev -type f \( -name 'authorized_keys' -o -name 'known_hosts' \) 2>/dev/null | head -n 100"],
        "ssh_private_keys.txt": ["bash", "-lc", r"find / -xdev -type f \( -name 'id_rsa' -o -name 'id_dsa' -o -name 'id_ecdsa' -o -name 'id_ed25519' \) 2>/dev/null | head -n 100"],
    }
    for name, cmd in commands.items():
        rc, out = run_cmd(cmd)
        write_output(os.path.join(outdir, name), f"SSH key hunt: {name}", out)


def collect_password_artifacts(outdir):
    info("Collecting password-related artifacts")
    commands = {
        "shadow_access.txt": ["bash", "-lc", "ls -l /etc/shadow 2>/dev/null || true"],
        "opasswd.txt": ["bash", "-lc", "ls -l /etc/security/opasswd 2>/dev/null || true"],
        "passwd_files.txt": ["bash", "-lc", r"find / -xdev -type f \( -name '*passwd*' -o -name '*shadow*' \) 2>/dev/null | head -n 100"],
    }
    for name, cmd in commands.items():
        rc, out = run_cmd(cmd)
        write_output(os.path.join(outdir, name), f"Password artifacts: {name}", out)


def main():
    parser = argparse.ArgumentParser(description="KittyEnum privilege escalation helper module")
    parser.add_argument("--outdir", default="./recon-output")
    args = parser.parse_args()

    info("Privilege escalation module started")
    os.makedirs(args.outdir, exist_ok=True)
    collect_system_info(args.outdir)
    collect_user_info(args.outdir)
    collect_privilege_vectors(args.outdir)
    collect_ssh_and_keys(args.outdir)
    collect_password_artifacts(args.outdir)
    warn("No external privesc tools are installed automatically. Use the results above to decide the next step.")
    ok("Privilege escalation module complete")


if __name__ == "__main__":
    main()
