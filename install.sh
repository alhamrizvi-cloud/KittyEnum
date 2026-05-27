#!/usr/bin/env bash
set -euo pipefail

RED="\033[91m"
GREEN="\033[92m"
YELLOW="\033[93m"
BLUE="\033[94m"
MAGENTA="\033[95m"
RESET="\033[0m"
BOLD="\033[1m"

function info() { printf "%s%s[INFO] %s%s\n" "${BLUE}" "${BOLD}" "$1" "${RESET}"; }
function ok() { printf "%s%s[ OK ] %s%s\n" "${GREEN}" "${BOLD}" "$1" "${RESET}"; }
function warn() { printf "%s%s[WARN] %s%s\n" "${YELLOW}" "${BOLD}" "$1" "${RESET}"; }
function fail() { printf "%s%s[FAIL] %s%s\n" "${RED}" "${BOLD}" "$1" "${RESET}"; exit 1; }

function run_as_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      info "Running command as root via sudo"
      sudo "$@"
    else
      fail "Root privileges are required. Re-run this script as root or install sudo."
    fi
  else
    "$@"
  fi
}

function ensure_apt() {
  if command -v apt-get >/dev/null 2>&1; then
    APT_CMD="apt-get"
  elif command -v apt >/dev/null 2>&1; then
    APT_CMD="apt"
  else
    fail "This installer supports Debian-based systems only. No apt/apt-get found."
  fi
}

function command_exists() {
  command -v "$1" >/dev/null 2>&1
}

function pkg_installed() {
  dpkg -s "$1" >/dev/null 2>&1
}

function package_available() {
  apt-cache show "$1" >/dev/null 2>&1
}

function apt_install() {
  local pkg="$1"
  info "Installing package: ${pkg}"
  run_as_root "$APT_CMD" install -y "$pkg"
}

function prompt_yes_no() {
  local prompt="$1"
  local default="$2"
  local answer

  while true; do
    read -rp "$prompt" answer
    answer="${answer,,}"
    if [[ -z "$answer" ]]; then
      answer="$default"
    fi
    case "$answer" in
      y|yes) return 0 ;; 
      n|no) return 1 ;; 
      *) echo "Please answer yes or no." ;; 
    esac
  done
}

function prompt_choice() {
  local prompt="$1"
  local input
  read -rp "$prompt" input
  echo "${input,,}" | tr -d ' ' | tr ',' ' '
}

function unique_items() {
  declare -A seen=()
  for item in "$@"; do
    if [[ -n "$item" && -z "${seen[$item]:-}" ]]; then
      seen[$item]=1
      printf "%s\n" "$item"
    fi
  done
}

function list_missing_commands() {
  local missing=()
  for cmd in "$@"; do
    if ! command_exists "$cmd"; then
      missing+=("$cmd")
    fi
  done
  printf "%s\n" "${missing[@]:-}" | sort -u
}

function check_wordlist_path() {
  local path="$1"
  if [[ -e "$path" ]]; then
    ok "Found required path: $path"
    return 0
  fi
  warn "Missing required path: $path"
  return 1
}

function install_selected_packages() {
  local pkgs=($@)
  for pkg in "${pkgs[@]}"; do
    if pkg_installed "$pkg"; then
      ok "Package already installed: $pkg"
      continue
    fi
    if package_available "$pkg"; then
      apt_install "$pkg"
    else
      warn "Package not available in apt cache: $pkg"
    fi
  done
}

function ask_seclists_path() {
  local default_path="/usr/share/seclists"
  if check_wordlist_path "$default_path"; then
    SECLISTS_PATH="$default_path"
    return 0
  fi

  warn "The default seclists path is missing. KittyEnum expects /usr/share/seclists."

  if pkg_installed seclists; then
    ok "seclists package is installed and should provide /usr/share/seclists."
  elif package_available seclists; then
    if prompt_yes_no "Install seclists package now? [Y/n]: " y; then
      apt_install seclists
      if check_wordlist_path "$default_path"; then
        SECLISTS_PATH="$default_path"
        return 0
      fi
    fi
  fi

  if prompt_yes_no "Do you have an alternative seclists directory to use? [y/N]: " n; then
    read -rp "Enter the full alternative seclists path: " alt_path
    if [[ -d "$alt_path" ]]; then
      if check_wordlist_path "$alt_path"; then
        SECLISTS_PATH="$alt_path"
        if [[ ! -e "$default_path" ]]; then
          if prompt_yes_no "Create a symlink from $default_path -> $alt_path? [Y/n]: " y; then
            run_as_root mkdir -p "$(dirname "$default_path")"
            run_as_root ln -sfn "$alt_path" "$default_path"
            ok "Created symlink $default_path -> $alt_path"
          fi
        fi
        return 0
      fi
    fi
    warn "Alternative path does not exist or is invalid: $alt_path"
  fi

  warn "Seclists path is not configured correctly. Some KittyEnum features may fail."
  return 1
}

function ask_rockyou() {
  local rockyou_path="/usr/share/wordlists/rockyou.txt"
  local gz_path="/usr/share/wordlists/rockyou.txt.gz"

  if [[ -f "$rockyou_path" ]]; then
    ok "Found rockyou.txt"
    return 0
  fi

  if [[ -f "$gz_path" ]]; then
    info "Found compressed rockyou.txt.gz. Extracting..."
    run_as_root gunzip -kf "$gz_path"
    if [[ -f "$rockyou_path" ]]; then
      ok "Extracted rockyou.txt"
      return 0
    fi
  fi

  warn "rockyou.txt is missing."
  if pkg_installed wordlists || pkg_installed seclists; then
    warn "The wordlists/seclists package is already installed but rockyou.txt is still missing."
  elif package_available wordlists; then
    if prompt_yes_no "Install wordlists package to obtain rockyou.txt? [Y/n]: " y; then
      apt_install wordlists
      if [[ -f "$rockyou_path" ]]; then
        ok "Installed rockyou.txt"
        return 0
      fi
    fi
  fi

  if prompt_yes_no "Do you have rockyou.txt at another path? [y/N]: " n; then
    read -rp "Enter the full path to rockyou.txt: " custom_rockyou
    if [[ -f "$custom_rockyou" ]]; then
      if prompt_yes_no "Create a symlink to /usr/share/wordlists/rockyou.txt? [Y/n]: " y; then
        run_as_root mkdir -p "$(dirname "$rockyou_path")"
        run_as_root ln -sfn "$custom_rockyou" "$rockyou_path"
        ok "Created symlink $rockyou_path -> $custom_rockyou"
        return 0
      fi
    else
      warn "File does not exist: $custom_rockyou"
    fi
  fi

  warn "rockyou.txt is not available. Some KittyEnum scans may be skipped."
  return 1
}

function show_welcome() {
  cat <<'EOF'

  ==============================================
  KittyEnum interactive dependency installer
  ==============================================

EOF
}

ensure_apt

declare -A CATEGORY_LABEL=(
  [basic]="Basic enumeration (nmap, gobuster, ffuf, enum4linux, seclists, wordlists)"
  [ad]="Active Directory enumeration tools"
  [aws]="AWS enumeration tools"
  [subdomain]="Subdomain enumeration tools"
  [all]="Install all supported dependency groups"
)

declare -A CATEGORY_PACKAGES=(
  [basic]="python3 nmap gobuster ffuf enum4linux ssh-audit seclists wordlists curl jq"
  [ad]="crackmapexec ldapdomaindump python3-impacket bloodhound powershell pwsh"
  [aws]="awscli python3-boto3"
  [subdomain]="subfinder amass assetfinder findomain chaos github-subdomains dnsx puredns massdns shuffledns httpx curl jq"
)

show_welcome

printf "Available install profiles:\n"
for key in basic ad aws subdomain all; do
  printf "  %-10s %s\n" "$key" "${CATEGORY_LABEL[$key]}"
 done

read -rp $'Select an install profile (basic/ad/aws/subdomain/all) [all]: ' profile
profile="${profile,,}"
profile="${profile:-all}"

selected_profiles=()
if [[ "$profile" == "all" ]]; then
  selected_profiles=(basic ad aws subdomain)
else
  for item in $profile; do
    case "$item" in
      basic|ad|aws|subdomain) selected_profiles+=("$item") ;;
      1) selected_profiles+=(basic) ;;
      2) selected_profiles+=(ad) ;;
      3) selected_profiles+=(aws) ;;
      4) selected_profiles+=(subdomain) ;;
      *) warn "Unknown profile: $item" ;;
    esac
  done
fi

if [[ ${#selected_profiles[@]} -eq 0 ]]; then
  fail "No valid profile selected. Exiting."
fi

info "Selected profiles: ${selected_profiles[*]}"

selected_packages=()
for profile_name in "${selected_profiles[@]}"; do
  selected_packages+=( ${CATEGORY_PACKAGES[$profile_name]} )
done

selected_packages=( $(unique_items "${selected_packages[@]}") )

all_commands=(python3 nmap gobuster ffuf enum4linux ssh-audit crackmapexec ldapdomaindump bloodhound-python pwsh powershell aws subfinder amass assetfinder findomain chaos github-subdomains dnsx puredns massdns shuffledns httpx curl jq)

missing_commands=($(list_missing_commands "${all_commands[@]}"))

if [[ ${#missing_commands[@]} -gt 0 ]]; then
  warn "Detected missing commands: ${missing_commands[*]}"
else
  ok "All common commands are already installed"
fi

if prompt_yes_no "Install required packages for the selected profiles? [Y/n]: " y; then
  install_selected_packages "${selected_packages[@]}"
else
  info "Skipping package installation as requested."
fi

info "Verifying seclists and wordlist paths"
SECLISTS_PATH="/usr/share/seclists"
ask_seclists_path
ask_rockyou

info "Final check of selected tools"
for profile_name in "${selected_profiles[@]}"; do
  case "$profile_name" in
    basic)
      for cmd in nmap gobuster ffuf enum4linux ssh-audit curl jq; do
        if command_exists "$cmd"; then ok "Found $cmd"; else warn "Missing $cmd"; fi
      done
      ;;
    ad)
      for cmd in crackmapexec ldapdomaindump bloodhound-python pwsh powershell; do
        if command_exists "$cmd"; then ok "Found $cmd"; else warn "Missing $cmd"; fi
      done
      ;;
    aws)
      if command_exists aws; then ok "Found aws"; else warn "Missing aws"; fi
      ;;
    subdomain)
      for cmd in subfinder amass assetfinder findomain chaos github-subdomains dnsx puredns massdns shuffledns httpx; do
        if command_exists "$cmd"; then ok "Found $cmd"; else warn "Missing $cmd"; fi
      done
      ;;
  esac
done

ok "Interactive install complete. Review any warnings above for missing tools or paths."
info "If you need custom seclists or rockyou paths, set them before running KittyEnum or create symlinks to /usr/share/seclists and /usr/share/wordlists/rockyou.txt."
