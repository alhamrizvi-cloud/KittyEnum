# KittyEnum Command Reference

## Table of Contents

- [Installer](#installer)
  - [Run installer](#run-installer)
  - [Install profiles](#install-profiles)
- [Main enumeration script](#main-enumeration-script)
  - [Usage](#usage)
  - [Standard options](#standard-options)
  - [Scan control options](#scan-control-options)
  - [Advanced modules](#advanced-modules)
- [Examples](#examples)
- [Submodule commands](#submodule-commands)

---

## Installer

### Run installer

Use the interactive installer to install required dependencies for KittyEnum.

```bash
./install.sh
```

This installer:

- detects missing CLI tools and packages
- prompts for an installation profile
- installs packages with `apt`
- verifies `seclists` and `rockyou.txt`
- helps configure alternate wordlist paths

### Install profiles

The installer supports these profiles:

- `basic` — base enumeration packages
- `ad` — Active Directory enumeration tools
- `aws` — AWS enumeration tools
- `subdomain` — subdomain enumeration tools
- `all` — install all supported profiles

---

## Main enumeration script

### Usage

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> [options]
```

Example:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb
```

### Standard options

- `-p`, `--port <port>`
  - Set web port for HTTP scans and fuzzing
  - Default: `80`
- `--no-udp`
  - Skip the UDP scan phase
- `--no-hosts`
  - Skip adding a target entry to `/etc/hosts`
- `--no-rockyou`
  - Skip the Gobuster `rockyou.txt` scan
- `--no-vhost`
  - Skip all virtual-host / subdomain phases
- `--no-enum`
  - Skip extended Gobuster enumeration (phase 7)
- `--no-params`
  - Skip FFUF parameter fuzzing
- `--big`
  - Use `raft-medium` directory wordlist for Gobuster dir scans
- `--param-path <path>`
  - Path to fuzz for parameter discovery
  - Default: `/`
- `--skip-verify`
  - Skip built-in tool and wordlist verification before running scans

### Advanced modules

- `--linux`
  - Run extra HTB Linux enumeration phases
- `--privesc`
  - Run local privilege escalation helper scripts
- `--ad`
  - Run Active Directory enumeration module
- `--ad-user <user>`
  - Username for AD enumeration
- `--ad-pass <pass>`
  - Password for AD enumeration
- `--ad-domain <domain>`
  - Domain name for AD enumeration
- `--ad-ps`
  - Generate Active Directory PowerShell enumeration snippets
- `--ad-ps-download`
  - Download AD PowerShell tool scripts to the output directory
- `--aws`
  - Run AWS enumeration module
- `--aws-profile <profile>`
  - AWS CLI profile to use
- `--aws-region <region>`
  - AWS region for API calls
- `--aws-access-key <key>`
  - AWS access key ID
- `--aws-secret-key <key>`
  - AWS secret access key
- `--aws-session-token <token>`
  - AWS session token
- `--aws-bucket <bucket>`
  - Optional S3 bucket name for bucket-level enumeration
- `--subdomains`
  - Run the subdomain enumeration module
- `--subdomains-github-token <token>`
  - GitHub token for `github-subdomains`
- `--subdomains-wordlist <path>`
  - DNS wordlist for active subdomain brute forcing
- `--subdomains-resolvers <path>`
  - Resolver list for active subdomain tools
- `--subdomains-passive`
  - Run only passive subdomain enumeration
- `--subdomains-active`
  - Run only active subdomain enumeration
- `--subdomains-probe`
  - Run HTTP probing against discovered hosts

---

## Examples

Run the default enumeration workflow:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb
```

Run Linux-focused enumeration:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb --linux
```

Run privilege escalation helper scripts only:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb --privesc
```

Run Active Directory enumeration with credentials:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb --ad --ad-user user --ad-pass password --ad-domain domain.local
```

Run AWS enumeration using a profile and region:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb --aws --aws-profile default --aws-region us-east-1
```

Run subdomain enumeration with custom wordlist and resolvers:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb --subdomains --subdomains-wordlist /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt --subdomains-resolvers ./resolvers.txt
```

Download AD PowerShell snippets and script files:

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb --ad-ps --ad-ps-download
```

---

## Submodule commands

The repository includes specialized modules under `kittyenum/`.

- `kittyenum/linux_enum.py`
  - HTB Linux enumeration scans
- `kittyenum/privesc_enum.py`
  - Privilege escalation helper script launcher
- `kittyenum/ad_enum.py`
  - Active Directory reconnaissance and credential-based AD recon
- `kittyenum/ad_powershell.py`
  - PowerShell enumeration command generation and optional download
- `kittyenum/aws_enum.py`
  - AWS reconnaissance using AWS CLI or boto3
- `kittyenum/subdomain_enum.py`
  - Passive + active subdomain enumeration and HTTP probing

For module-level usage, run each with `python3 kittyenum/<module>.py --help`.
