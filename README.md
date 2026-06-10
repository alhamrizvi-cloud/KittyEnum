<img width="306" height="220" alt="image" src="https://github.com/user-attachments/assets/ffa7fdc7-71ac-42c9-a5a6-76f0e848a08f" />

# KittyEnum

KittyEnum is a fast, opinionated reconnaissance and enumeration toolkit designed for penetration testers, red teamers, and CTF players. It combines multiple scanning and fuzzing tools into one streamlined Python script, providing a single terminal workflow for network scanning, directory discovery, virtual-host enumeration, and parameter fuzzing.

## Features

- `nmap` TCP and UDP scanning
- `/etc/hosts` entry automation for target hostname resolution
- `gobuster` directory brute forcing with common and large wordlists
- `gobuster` virtual host enumeration
- `gobuster` API endpoint and large directory enumeration
- `ffuf` directory fuzzing
- `ffuf` virtual host discovery
- `ffuf` parameter fuzzing
- Optional Linux, privesc, AD, AWS, and subdomain enumeration modules
- Concurrent multitasking of web enumeration phases in the same terminal

## Installation

1. Clone the repository:

```bash
git clone https://github.com/alhamrizvi-cloud/KittyEnum.git
cd KittyEnum
```

2. Run the included installer script to set up tools, requirements, and wordlists:

```bash
sudo ./install.sh
```

3. If you need additional dependencies, run:

```bash
./scripts/install_deps.sh
```

The installer script handles the full setup for KittyEnum, including required Python packages, tool checks, and wordlists.

## Usage

Run KittyEnum with a target IP and hostname:

```bash
sudo python3 kittyenum.py 10.10.10.10 target.htb
```

### Common options

- `-p`, `--port` : Web port (default: `80`)
- `--big` : Use the medium-sized Gobuster wordlist
- `--no-udp` : Skip UDP scanning
- `--no-hosts` : Skip writing to `/etc/hosts`
- `--no-rockyou` : Skip rockyou directory brute forcing
- `--no-vhost` : Skip all vhost/subdomain phases
- `--no-enum` : Skip extended Gobuster enumeration
- `--no-params` : Skip FFUF parameter fuzzing
- `--skip-verify` : Skip tool and wordlist verification
- `--no-multitask` : Disable concurrent web enumeration and run sequentially
- `--linux` : Run extra HTB Linux enumeration phases

## Output

KittyEnum saves all results under `./recon-<hostname>-<timestamp>/` and prints a summary at the end.

## Notes

- Run the script with `sudo` for SYN scans and `/etc/hosts` updates.
- Use `sudo ./install.sh` to prepare the environment and install required dependencies.

---

Made by Alham Rizvi
