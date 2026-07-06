#!/usr/bin/env bash
# Shared helpers for watch-vault install/update scripts. Source this file.
set -euo pipefail

if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
  RED=$'\033[31m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
else
  BOLD=; DIM=; GREEN=; YELLOW=; RED=; CYAN=; RESET=
fi

say()  { printf '%s\n' "${CYAN}▸${RESET} $*"; }
ok()   { printf '%s\n' "${GREEN}✓${RESET} $*"; }
warn() { printf '%s\n' "${YELLOW}!${RESET} $*" >&2; }
die()  { printf '%s\n' "${RED}✗ $*${RESET}" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# ask "Question?" "default"  -> echoes the answer (default if non-interactive)
ask() {
  local q="$1" def="${2:-}"
  if [ ! -t 0 ]; then printf '%s' "$def"; return; fi
  local ans; read -r -p "${BOLD}$q${RESET} ${DIM}[$def]${RESET} " ans || true
  printf '%s' "${ans:-$def}"
}

# ask_yes_no "Question?" "y|n" -> returns 0 for yes
ask_yes_no() {
  local ans; ans="$(ask "$1 (y/n)" "${2:-y}")"
  case "$ans" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

detect_os() {
  case "$(uname -s)" in
    Darwin) echo macos ;;
    Linux)  grep -qi microsoft /proc/version 2>/dev/null && echo wsl || echo linux ;;
    *)      echo other ;;
  esac
}

detect_open_cmd() {
  case "$(detect_os)" in
    macos) echo open ;;
    wsl)   echo explorer.exe ;;
    *)     echo xdg-open ;;
  esac
}

# Install a system package via the platform's package manager.
pkg_install() {
  local pkg="$1"
  case "$(detect_os)" in
    macos) have brew && brew install "$pkg" || die "Homebrew not found — install from https://brew.sh then re-run." ;;
    linux|wsl)
      if   have apt-get; then sudo apt-get update -y && sudo apt-get install -y "$pkg"
      elif have dnf;     then sudo dnf install -y "$pkg"
      elif have pacman;  then sudo pacman -S --noconfirm "$pkg"
      else die "No supported package manager (apt/dnf/pacman). Install '$pkg' manually."; fi ;;
    *) die "Unsupported OS. Install '$pkg' manually." ;;
  esac
}
