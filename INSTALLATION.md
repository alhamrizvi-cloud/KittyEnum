# KittyEnum Installation Guide

This project includes two installation paths:

1. `install.sh` — interactive installer for Debian-based systems using `apt`
2. `requirements.txt` — lightweight Python install for optional AWS dependencies

## Option 1: Interactive installer

Run the bundled shell installer:

```bash
./install.sh
```

This installer will:

- detect required CLI tools
- prompt you for an install profile (`basic`, `ad`, `aws`, `subdomain`, `all`)
- install packages with `apt`
- verify `seclists` and `rockyou.txt`
- optionally help configure alternate wordlist paths

## Option 2: Lightweight Python install

KittyEnum itself uses only the Python standard library, so no Python packages
are required for most features.

If you want AWS enumeration support, install the optional dependency:

```bash
python3 -m pip install -r requirements.txt
```

If you prefer to isolate dependencies, use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Run KittyEnum directly

Use the normal entrypoint:

```bash
python3 kittyenum.py <IP> <HOSTNAME> [options]
```

Or use the alias entrypoint:

```bash
python3 kittyenum.py <IP> <HOSTNAME> [options]
```

## Install the `kittyenum` command

To use `kittyenum` directly from the shell, add the repository root to your PATH
or create a global symlink.

### Add the current directory to PATH temporarily

```bash
export PATH="$PWD:$PATH"
```

Then run:

```bash
python3 kittyenum.py 10.10.10.10 target.htb
```

### Install a global command alias

This repository includes a wrapper script at `scripts/kittyenum`.
Create a symlink to `/usr/local/bin/kittyenum` to use the command globally.

```bash
sudo ln -s "$PWD/scripts/kittyenum" /usr/local/bin/kittyenum
sudo chmod +x /usr/local/bin/kittyenum
```

After this, run:

```bash
kittyenum 10.10.10.10 target.htb
```

## Notes

- `requirements.txt` only includes optional AWS support (`boto3`).
- The interactive `install.sh` is still useful for installing underlying CLI tools.
- If you do not need AWS enumeration, you can skip the Python dependency install.
