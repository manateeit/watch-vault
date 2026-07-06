#!/usr/bin/env bash
# Shared helpers for yt-video-review-eval install/update scripts. Source this file.
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

# Put ~/.local/bin on PATH (for this run + future shells) — used by the no-brew macOS path.
ensure_local_bin_on_path() {
  mkdir -p "$HOME/.local/bin"
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *)
      export PATH="$HOME/.local/bin:$PATH"
      local prof="$HOME/.zprofile"
      grep -qs 'HOME/.local/bin' "$prof" 2>/dev/null || \
        printf '\n# added by yt-video-review-eval installer\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$prof" ;;
  esac
}

# Download a single static binary into ~/.local/bin (no sudo, no brew), then VERIFY it runs.
fetch_static_bin() {
  local name="$1" dst="$HOME/.local/bin/$1" tmp rc
  tmp="$(mktemp -d)"
  case "$name" in
    yt-dlp)
      curl -fsSL "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos" -o "$dst" && chmod +x "$dst" ;;
    ffmpeg|ffprobe)
      curl -fsSL "https://evermeet.cx/ffmpeg/getrelease/$name/zip" -o "$tmp/$name.zip" \
        && unzip -oq "$tmp/$name.zip" -d "$HOME/.local/bin" && chmod +x "$dst" ;;
  esac
  rc=$?; rm -rf "$tmp"
  [ $rc -eq 0 ] && [ -x "$dst" ] || { warn "Could not download $name."; return 1; }
  # verify it actually runs — yt-dlp uses --version, ffmpeg/ffprobe use -version
  local vflag="-version"; [ "$name" = "yt-dlp" ] && vflag="--version"
  if ! "$dst" "$vflag" >/dev/null 2>&1; then
    warn "$name downloaded but won't run here (Apple Silicon likely needs Rosetta 2)."
    warn "Fix with:  softwareupdate --install-rosetta --agree-to-license   — or install Homebrew (https://brew.sh)."
    return 1
  fi
  ok "$name ready (~/.local/bin/$name)"
}

# Install a system package via the platform's package manager (or no-sudo binaries on brew-less macOS).
pkg_install() {
  local pkg="$1"
  case "$(detect_os)" in
    macos)
      if have brew; then brew install "$pkg"
      else
        warn "Homebrew not found — installing $pkg as a no-sudo static binary into ~/.local/bin."
        ensure_local_bin_on_path
        case "$pkg" in
          ffmpeg) fetch_static_bin ffmpeg && fetch_static_bin ffprobe ;;
          *)      fetch_static_bin "$pkg" ;;
        esac || die "Could not install $pkg without Homebrew. Install brew (https://brew.sh) or the binary manually, then re-run."
      fi ;;
    linux|wsl)
      if   have apt-get; then sudo apt-get update -y && sudo apt-get install -y "$pkg"
      elif have dnf;     then sudo dnf install -y "$pkg"
      elif have pacman;  then sudo pacman -S --noconfirm "$pkg"
      else die "No supported package manager (apt/dnf/pacman). Install '$pkg' manually."; fi ;;
    *) die "Unsupported OS. Install '$pkg' manually." ;;
  esac
}
