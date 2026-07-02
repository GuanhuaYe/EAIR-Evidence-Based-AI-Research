#!/usr/bin/env bash
# Install skills by symlinking them into ~/.claude/skills.
# Usage:
#   ./install.sh            install (symlink) all skills
#   ./install.sh --check    verify installation
#   ./install.sh --copy     copy instead of symlink (survives repo deletion)
#   ./install.sh --remove   remove installed links/copies
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
MODE="${1:-install}"

[ -d "$SKILLS_SRC" ] || { echo "error: $SKILLS_SRC not found"; exit 1; }
mkdir -p "$SKILLS_DST"

case "$MODE" in
  install|--copy)
    for src in "$SKILLS_SRC"/*/; do
      name="$(basename "$src")"
      dst="$SKILLS_DST/$name"
      if [ -e "$dst" ] && [ ! -L "$dst" ]; then
        echo "skip  $name (already exists and is not ours — remove manually to replace)"
        continue
      fi
      rm -rf "$dst"
      if [ "$MODE" = "--copy" ]; then
        cp -r "$src" "$dst"; echo "copy  $name"
      else
        ln -s "${src%/}" "$dst"; echo "link  $name"
      fi
    done
    echo
    echo "Done. Start Claude Code and try: \"grill this experiment design\""
    ;;
  --check)
    fail=0
    for src in "$SKILLS_SRC"/*/; do
      name="$(basename "$src")"
      if [ -f "$SKILLS_DST/$name/SKILL.md" ] || [ -d "$SKILLS_DST/$name" ]; then
        echo "ok    $name"
      else
        echo "MISS  $name"; fail=1
      fi
    done
    exit $fail
    ;;
  --remove)
    for src in "$SKILLS_SRC"/*/; do
      name="$(basename "$src")"
      dst="$SKILLS_DST/$name"
      if [ -L "$dst" ] || { [ -d "$dst" ] && [ -f "$dst/SKILL.md" ]; }; then
        rm -rf "$dst"; echo "rm    $name"
      fi
    done
    ;;
  *)
    echo "usage: $0 [--check|--copy|--remove]"; exit 1
    ;;
esac
