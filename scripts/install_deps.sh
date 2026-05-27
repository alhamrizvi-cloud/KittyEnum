#!/usr/bin/env bash
set -euo pipefail

# KittyEnum dependency installer
# Checks Python, required CLI tools, and wordlist packages.

RED="\033[91m"
GREEN="\033[92m"
YELLOW="\033[93m"
BLUE="\033[94m"
MAGENTA="\033[95m"
RESET="\033[0m"
BOLD="\033[1m"

function info() {
  printf "%s%s[INFO] %s%s\n" "${BLUE}" "${BOLD}" "$1" "${RESET}"
}

function ok() {
  printf "%s%s[ OK ] %s%s\n" "${GREEN}" "${BOLD}" "$1" "${RESET}"
}

function warn() {
  printf "%s%s[WARN] %s%s\n" "${YELLOW}" "${BOLD}" "$1" "${RESET}"
}

function fail() {
  printf "%s%s[FAIL] %s%s\n" "${RED}" "${BOLD}" "$1" "${RESET}"
  exit 1
}

function run_as_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      info "Running install commands via sudo"
      sudo "$@"
    else
      fail "Root privileges required. Re-run this script as root or install sudo."
    fi
  else
    "$@"
  fi
}

function apt_install() {
  local pkg="$1"
  info "Installing package: ${pkg}"
  run_as_root "$APT_CMD" install -y "$pkg"
}

function ensure_apt() {
  if command -v apt-get >/dev/null 2>&1; then
    APT_CMD="apt-get"
  elif command -v apt >/dev/null 2>&1; then
    APT_CMD="apt"
  else
    fail "No apt package manager found. KittyEnum installer supports Debian-based systems only."
  fi
}

function check_command() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "Found $cmd"
    return 0
  fi
  warn "Missing $cmd"
  return 1
}

function check_wordlist_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    ok "Found wordlist: $path"
    return 0
  fi
  warn "Missing wordlist: $path"
  return 1
}

function maybe_gunzip_rockyou() {
  local gz_path="/usr/share/wordlists/rockyou.txt.gz"
  local txt_path="/usr/share/wordlists/rockyou.txt"

  if [[ -f "$txt_path" ]]; then
    ok "rockyou.txt is already extracted"
    return
  fi

  if [[ -f "$gz_path" ]]; then
    info "Found rockyou.txt.gz — extracting to rockyou.txt"
    run_as_root gunzip -kf "$gz_path"
    if [[ -f "$txt_path" ]]; then
      ok "Extracted rockyou.txt"
    else
      warn "Extraction failed; rockyou.txt still missing"
    fi
  fi
}

info "KittyEnum dependency installer started"

ensure_apt

REQUIRED_COMMANDS=(python3 nmap gobuster ffuf enum4linux ssh-audit)
REQUIRED_PACKAGES=(nmap gobuster ffuf enum4linux ssh-audit seclists wordlists)
AD_COMMANDS=(crackmapexec ldapdomaindump bloodhound-python pwsh powershell)
AD_PACKAGES=(crackmapexec ldapdomaindump python3-impacket bloodhound powershell)
REQUIRED_WORDLISTS=("/usr/share/seclists" "/usr/share/wordlists/rockyou.txt")

missing_tools=()
for cmd in "${REQUIRED_COMMANDS[@]}"; do
  if ! check_command "$cmd"; then
    missing_tools+=("$cmd")
  fi
done

missing_wordlists=()
for wordlist in "${REQUIRED_WORDLISTS[@]}"; do
  if ! check_wordlist_file "$wordlist"; then
    missing_wordlists+=("$wordlist")
  fi
done

if [[ ${#missing_tools[@]} -eq 0 ]] && [[ ${#missing_wordlists[@]} -eq 0 ]]; then
  ok "All required tools and wordlists are already installed"
  maybe_gunzip_rockyou
  ok "KittyEnum dependencies are ready"
  exit 0
fi

if [[ ${#missing_tools[@]} -gt 0 ]]; then
  info "Missing tools: ${missing_tools[*]}"
fi

if [[ ${#missing_wordlists[@]} -gt 0 ]]; then
  info "Missing wordlists or wordlist packages: ${missing_wordlists[*]}"
fi

info "Updating package cache"
run_as_root "$APT_CMD" update

for pkg in "${REQUIRED_PACKAGES[@]}"; do
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    apt_install "$pkg"
  else
    ok "Package already installed: $pkg"
  fi
done

info "Checking Active Directory tool packages"
for pkg in "${AD_PACKAGES[@]}"; do
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    ok "Package already installed: $pkg"
  elif apt-cache show "$pkg" >/dev/null 2>&1; then
    apt_install "$pkg"
  else
    warn "AD package not available in package cache: $pkg"
  fi
done

info "Checking Active Directory command availability"
for cmd in "${AD_COMMANDS[@]}"; do
  if check_command "$cmd"; then
    ok "AD command available: $cmd"
  else
    warn "AD command missing: $cmd"
  fi
done

maybe_gunzip_rockyou

info "Re-checking installed tools and wordlists"
for cmd in "${REQUIRED_COMMANDS[@]}"; do
  check_command "$cmd"
done
for wordlist in "${REQUIRED_WORDLISTS[@]}"; do
  check_wordlist_file "$wordlist"
done

ok "KittyEnum dependency installation complete"
info "You can now run: sudo python3 autoenum.py <IP> <HOSTNAME> [options]"
