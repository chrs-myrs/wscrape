#!/usr/bin/env bash
# Install the wscrape toolkit for local use (symlinks skills + CLI).
# Idempotent: safe to re-run.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.local/bin" "$HOME/.claude/skills"

ln -sfn "$REPO/tools/wscrape" "$HOME/.local/bin/wscrape"
for skill in wscrape hunt research research-brief; do
  ln -sfn "$REPO/skills/$skill" "$HOME/.claude/skills/$skill"
done

if command -v uv >/dev/null 2>&1; then
  uv tool install "crawl4ai>=0.9,<0.10" --python python3.11 || true
  crawl4ai-setup || true
else
  echo "note: install 'uv' (https://docs.astral.sh/uv/) then re-run for crawl4ai." >&2
fi

echo "Installed. Ensure ~/.local/bin is on PATH, then: wscrape search 'hello' --limit 1"
