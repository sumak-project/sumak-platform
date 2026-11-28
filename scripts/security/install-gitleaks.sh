#!/usr/bin/env bash
set -euo pipefail

readonly GITLEAKS_VERSION="8.30.1"
readonly GITLEAKS_LINUX_X64_SHA256="551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"

destination="${1:-$HOME/.local/bin}"
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "Unsupported platform: this installer currently verifies Linux x86_64 only" >&2
  exit 1
fi

archive="gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${archive}"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

curl --fail --location --silent --show-error "$url" --output "$temporary_directory/$archive"
printf '%s  %s\n' "$GITLEAKS_LINUX_X64_SHA256" "$temporary_directory/$archive" \
  | sha256sum --check --status

mkdir -p "$destination"
tar -xzf "$temporary_directory/$archive" -C "$temporary_directory" gitleaks
install -m 0755 "$temporary_directory/gitleaks" "$destination/gitleaks"
"$destination/gitleaks" version
