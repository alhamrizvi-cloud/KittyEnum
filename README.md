# KittyEnum

KittyEnum is a smart reconnaissance and enumeration toolkit built for pentesters, red teamers, and Capture The Flag players.
It automates the discovery workflow by validating required tools and wordlists, running TCP/UDP scans, mapping hostnames, and discovering
web directories, virtual hosts, and hidden parameters with fuzzing.

KittyEnum is designed to be fast, repeatable, and easy to use while giving you rich, timestamped output for follow-up analysis.

## Features

- Auto-verifies essential tools: `nmap`, `gobuster`, `ffuf`
- Checks popular wordlists and warns if required files are missing
- Performs SYN/UDP scans, host mapping, directory discovery, virtual host enumeration, and parameter fuzzing
- Saves results to a dedicated `recon-<hostname>-<timestamp>/` output directory
- Includes a polished, kitty-themed banner and tool branding

## Usage

```bash
sudo python3 autoenum.py <IP> <HOSTNAME> [options]
```

## Example

```bash
sudo python3 autoenum.py 10.10.10.10 target.htb -p 8080 --big
```
