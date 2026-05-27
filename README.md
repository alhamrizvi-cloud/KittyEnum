# KittyEnum

KittyEnum is a smart reconnaissance and enumeration toolkit built for pentesters, red teamers, and Capture The Flag players.
It automates the discovery workflow by validating required tools and wordlists, running TCP/UDP scans, mapping hostnames, and discovering
web directories, virtual hosts, and hidden parameters with fuzzing.

KittyEnum is designed to be fast, repeatable, and easy to use while giving you rich, timestamped output for follow-up analysis.

## Dependency Installer

Run the interactive installer to verify and install dependencies:

```bash
./install.sh
```

This script checks for available tools, prompts for the enumeration profile you want to install, installs missing packages with `apt`, verifies `seclists` and `rockyou.txt`, and can help configure alternate wordlist paths.

For lightweight Python setup, see `INSTALLATION.md`. To use the shorter command name `kittyenum`, see `CONFIGURATION.md`.

## Features

- Auto-verifies essential tools: `nmap`, `gobuster`, `ffuf`
- Checks popular wordlists and warns if required files are missing
- Performs SYN/UDP scans, host mapping, directory discovery, virtual host enumeration, and parameter fuzzing
- Includes optional HTB Linux enumeration using Nmap scripts, enum4linux, and SSH audit
- Includes SSH-friendly local privilege escalation enumeration that avoids installing root-only tools automatically
- Saves results to a dedicated `recon-<hostname>-<timestamp>/` output directory
- Includes a polished, kitty-themed banner and tool branding

## Usage

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> [options]
```

Run additional Linux-focused enumeration for HTB machines:

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> --linux
```

Run the SSH-friendly privilege escalation helper module after a shell is available:

```bash
python3 autoenum.py <IP> <HOSTNAME> --privesc
```
Run AWS enumeration using AWS CLI credentials or profile:

```bash
python3 autoenum.py <IP> <HOSTNAME> --aws --aws-profile default --aws-region us-east-1
```

Run AWS S3 bucket enumeration with no-sign-request:

```bash
python3 autoenum.py <IP> <HOSTNAME> --aws --aws-region us-east-1 --aws-bucket target-bucket-name
```

Run subdomain enumeration with passive, active, and probing stages:

```bash
python3 autoenum.py <IP> <HOSTNAME> --subdomains --subdomains-wordlist /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt --subdomains-resolvers ./resolvers.txt
```
Generate Active Directory PowerShell enumeration snippets:

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> --ad-ps
```

Download the AD PowerShell tool scripts to the output directory:

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> --ad-ps --ad-ps-download
```

KittyEnum now distributes specialized modules in `kittyenum/`:

- `kittyenum/linux_enum.py` — HTB Linux enumeration scans
- `kittyenum/privesc_enum.py` — privilege escalation helper script launcher
- `kittyenum/ad_enum.py` — Active Directory reconnaissance and credential-based AD recon
- `kittyenum/ad_powershell.py` — PowerShell command snippet generation and optional AD tool download
- `kittyenum/aws_enum.py` — AWS reconnaissance using AWS CLI or boto3
- `kittyenum/subdomain_enum.py` — passive + active subdomain enumeration and HTTP probing

## Active Directory Enumeration

Use the AD module to perform full Active Directory reconnaissance with optional credentials:

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> --ad --ad-user <USER> --ad-pass <PASS> --ad-domain <DOMAIN>
```

When credentials are omitted, KittyEnum will attempt anonymous AD/LDAP enumeration where possible.

## Example

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb -p 8080 --big
```
