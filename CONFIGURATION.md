# KittyEnum Configuration Guide

This document explains how to configure the tool name, aliases, and wordlist paths.

## Use `kittyenum` as the command

A new wrapper script named `kittyenum` is included with the repository.

### Run locally from the repo root

```bash
python3 kittyenum.py 10.10.10.10 target.htb
```

### Run via wrapper script

```bash
./scripts/kittyenum 10.10.10.10 target.htb
```

### Add the repository root to your PATH

```bash
export PATH="$PWD:$PATH"
```

Then you can run:

```bash
kittyenum 10.10.10.10 target.htb
```

## Create a system-wide command

If you want the shortcut to work everywhere:

```bash
sudo ln -s "$PWD/kittyenum" /usr/local/bin/kittyenum
sudo chmod +x /usr/local/bin/kittyenum
```

If you want the `kittyenum.py` alias available globally as well:

```bash
sudo ln -s "$PWD/kittyenum.py" /usr/local/bin/kittyenum.py
sudo chmod +x /usr/local/bin/kittyenum.py
```

## Custom wordlist and seclists paths

By default, KittyEnum expects the following paths:

- `seclists` at `/usr/share/seclists`
- `rockyou.txt` at `/usr/share/wordlists/rockyou.txt`

If these paths are missing, the installer and verification code may warn or skip
some scans.

### Use a custom Seclists directory

If you already have Seclists installed elsewhere, create a symlink:

```bash
sudo mkdir -p /usr/share
sudo ln -s /path/to/your/seclists /usr/share/seclists
```

### Use a custom rockyou.txt location

If your `rockyou.txt` file is stored elsewhere:

```bash
sudo mkdir -p /usr/share/wordlists
sudo ln -s /path/to/rockyou.txt /usr/share/wordlists/rockyou.txt
```

## Change the tool name in documentation

The project now supports both:

- `kittyenum.py`
- `autoenum.py` (compatibility wrapper)
- `kittyenum`

If you want to update your local docs or scripts, use `kittyenum` for the shortcut command.

## Confirm the command is available

```bash
which kittyenum
kittyenum --help
```

If `kittyenum --help` fails, ensure the wrapper script is executable and in your PATH.
