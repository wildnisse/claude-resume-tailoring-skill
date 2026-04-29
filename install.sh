#!/usr/bin/env bash
# claude-resume-tailoring-skill installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/wildnisse/claude-resume-tailoring-skill/main/install.sh | bash
#
# Or, with environment overrides for non-interactive use:
#   SKILL_USER_NAME="Jane Doe" SKILL_DATA_DIR="$HOME/Documents/jane-jobsearch" bash install.sh

set -euo pipefail

SKILL_REPO_URL="${SKILL_REPO_URL:-https://github.com/wildnisse/claude-resume-tailoring-skill.git}"
SKILL_REPO_BRANCH="${SKILL_REPO_BRANCH:-main}"

# ── colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; BLUE=$'\033[34m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
  RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; RESET=""
fi

info()  { echo "${BLUE}info:${RESET} $*"; }
ok()    { echo "${GREEN}ok:${RESET} $*"; }
warn()  { echo "${YELLOW}warn:${RESET} $*"; }
die()   { echo "${RED}error:${RESET} $*" >&2; exit 1; }

# ── prompts (work even when piped from curl) ──────────────────────────────────
# When `curl ... | bash`, stdin is the script body. Read from /dev/tty for prompts.
prompt() {
  local label="$1"
  local default="$2"
  local var
  if [ -t 0 ]; then
    read -r -p "${label} [${default}]: " var
  else
    read -r -p "${label} [${default}]: " var </dev/tty
  fi
  if [ -z "$var" ]; then
    var="$default"
  fi
  echo "$var"
}

# ── checks ────────────────────────────────────────────────────────────────────
need() {
  command -v "$1" >/dev/null 2>&1 || die "missing required tool: $1"
}

info "checking prerequisites"
need git
need python3
need bash
ok "prerequisites present"

# Optional: LibreOffice (for pdf conversion). Warn if missing.
if ! command -v soffice >/dev/null 2>&1 && ! [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
  warn "LibreOffice (soffice) not found. PDF conversion will fail until you install it."
  warn "  macOS: brew install --cask libreoffice"
  warn "  Ubuntu: sudo apt install libreoffice"
fi

# ── inputs ────────────────────────────────────────────────────────────────────
echo ""
echo "${BOLD}claude-resume-tailoring-skill installer${RESET}"
echo ""

USER_NAME="${SKILL_USER_NAME:-}"
if [ -z "$USER_NAME" ]; then
  USER_NAME=$(prompt "Your name (used in resume filenames and templates)" "Jane Doe")
fi

# slugify name for default dir: lowercase, single hyphens. Portable across BSD and GNU sed.
NAME_SLUG=$(echo "$USER_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed -e 's/^-//' -e 's/-$//')

DEFAULT_DATA_DIR="$HOME/Documents/${NAME_SLUG}-jobsearch"
DATA_DIR="${SKILL_DATA_DIR:-}"
if [ -z "$DATA_DIR" ]; then
  DATA_DIR=$(prompt "Where do you want your private data repo" "$DEFAULT_DATA_DIR")
fi

# Expand tilde
DATA_DIR="${DATA_DIR/#\~/$HOME}"

if [ -e "$DATA_DIR" ]; then
  if [ -d "$DATA_DIR" ] && [ -d "$DATA_DIR/.git" ]; then
    warn "$DATA_DIR already exists and is a git repo. Cannot install on top of an existing repo."
    die "Pick a different directory, or remove the existing one first."
  elif [ -d "$DATA_DIR" ] && [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
    info "$DATA_DIR exists but is empty, proceeding"
  else
    die "$DATA_DIR exists and is not empty. Pick a different directory."
  fi
fi

echo ""
info "name:     $USER_NAME"
info "data dir: $DATA_DIR"
info "skill:    $SKILL_REPO_URL @ $SKILL_REPO_BRANCH"
echo ""

# ── create the data repo ──────────────────────────────────────────────────────
info "creating data repo at $DATA_DIR"
mkdir -p "$DATA_DIR"
cd "$DATA_DIR"
git init --initial-branch=main >/dev/null

mkdir -p master-resumes job-applications

# ── add the skill as a submodule ──────────────────────────────────────────────
info "adding skill submodule at skill/"
git submodule add -b "$SKILL_REPO_BRANCH" "$SKILL_REPO_URL" skill >/dev/null

# ── copy templates ────────────────────────────────────────────────────────────
info "copying starter templates"

today_iso=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# experience-kb.json (with name and date substituted)
sed -e "s|REPLACE_WITH_TODAY|$today_iso|g" \
    -e "s|\"Your Full Name\"|\"$USER_NAME\"|" \
    skill/templates/experience-kb.template.json > experience-kb.json

# jobs.json
sed -e "s|REPLACE_WITH_TODAY|$today_iso|g" \
    skill/templates/jobs.template.json > jobs.json

# CLAUDE.md
sed -e "s|REPLACE_WITH_YOUR_NAME|$USER_NAME|g" \
    skill/templates/CLAUDE.template.md > CLAUDE.md

# ── set up python venv ────────────────────────────────────────────────────────
info "setting up Python virtualenv at .venv/"
python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r skill/requirements.txt
deactivate

# ── .gitignore ────────────────────────────────────────────────────────────────
cat > .gitignore <<'EOF'
.venv/
__pycache__/
*.pyc
.DS_Store
EOF

# ── initial commit ────────────────────────────────────────────────────────────
info "creating initial commit"
git add .
git commit --quiet -m "feat: initial setup with claude-resume-tailoring-skill"

# ── done ──────────────────────────────────────────────────────────────────────
echo ""
ok "installation complete"
echo ""
echo "${BOLD}Next steps:${RESET}"
echo ""
echo "  1. cd $DATA_DIR"
echo "  2. Edit experience-kb.json with your real career history"
echo "  3. Drop your master resume(s) into master-resumes/"
echo "  4. Edit CLAUDE.md to adjust style and preferences"
echo "  5. Open this directory in Claude Code (or in a Claude Desktop project)"
echo "     and the skill will activate when you paste a JD."
echo ""
echo "  To create a GitHub remote later:"
echo "     gh repo create ${NAME_SLUG}-jobsearch --private --source=. --push"
echo ""
