# claude-resume-tailoring-skill

A multi-agent pipeline for tailoring resumes and cover letters to specific job descriptions, designed to run inside Claude (Claude Code, Claude Desktop, or remote agents).

The skill takes a job description, scores your master resume against it, generates a tailored version, runs ATS scoring again, and drafts a cover letter — all while flagging gaps it can't honestly bridge so you don't ship overclaimed content.

## What it does

Given a JD, the pipeline:

1. **Parses the JD** into structured requirements, tone signals, and culture markers
2. **Flags education requirements** when a degree (BS/MS/PhD) is a hard filter
3. **Scores your master resume** on a 100-point ATS rubric (formatting, tone, hard requirements, nice-to-haves, overall fit)
4. **Asks you about gaps** in your experience knowledge base (and updates the KB with anything new you surface)
5. **Tailors the resume** by reordering, reframing, and surfacing relevant experience — without fabricating
6. **Re-scores** the tailored resume
7. **Drafts a cover letter** in your voice (no LLM filler, no em-dashes, no "passionate about")
8. **Records everything** to a job registry so future tailoring sessions can learn from past applications

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/wildnisse/claude-resume-tailoring-skill/main/install.sh | bash
```

The installer will:

1. Ask where you want your private data repo (default `~/Documents/<your-name>-jobsearch/`)
2. Ask for your name (used in resume filenames and templates)
3. Create the private data repo as a fresh git repo
4. Add this skill as a git submodule at `skill/`
5. Copy starter templates so you can fill in your experience knowledge base
6. Set up a Python virtualenv with required dependencies

If you'd rather not pipe `bash`, do it manually:

```bash
# Create your private data repo
mkdir -p ~/Documents/myname-jobsearch
cd ~/Documents/myname-jobsearch
git init

# Add the skill as a submodule
git submodule add https://github.com/wildnisse/claude-resume-tailoring-skill.git skill

# Copy starter templates
cp skill/templates/experience-kb.template.json experience-kb.json
cp skill/templates/jobs.template.json jobs.json
cp skill/templates/CLAUDE.template.md CLAUDE.md

# Set up the Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r skill/requirements.txt
```

## Prerequisites

- **Python 3.10+** (for the resume builder)
- **LibreOffice** (for docx-to-pdf conversion via `soffice`). On macOS: `brew install --cask libreoffice`
- **git** (for the submodule install and auto-commit)
- **Claude Code, Claude Desktop, or another Claude-compatible runtime** to invoke the agents

## After install

1. Edit `experience-kb.json` with your real career history. The template has placeholders and inline guidance.
2. Drop your master resume into `master-resumes/` (docx and pdf).
3. Edit `CLAUDE.md` to adjust the system rules to your style and preferences.
4. From inside Claude (Code or Desktop), say something like *"Add this job: <paste JD>"* and the skill will run the pipeline.

## Updating the skill

The skill is pinned to a specific tag via the submodule. To pull the latest version:

```bash
cd skill
git fetch --tags
git checkout <latest-tag>
cd ..
git add skill
git commit -m "chore: update skill to <tag>"
```

The pipeline orchestrator also auto-checks for newer versions at startup and prompts you to update.

## Architecture

```
your-jobsearch-repo/                    ← your private data
├── CLAUDE.md                           ← personal rules and preferences
├── experience-kb.json                  ← your career facts (canonical source of truth)
├── jobs.json                           ← application registry / history
├── master-resumes/                     ← your evolving master resume(s)
├── job-applications/                   ← per-job output, FLAT structure
│   └── {company-slug}/
│       ├── raw-jd.txt
│       ├── jd-analysis.json
│       ├── education-check.json
│       ├── resume-content.json         ← input to resume_builder
│       ├── ats-score-round-{1,2}.json
│       ├── {name}-{level}-v1.docx
│       ├── {name}-{level}-v1.pdf
│       └── cover-letter-*.md
└── skill/                              ← this skill, as a git submodule
    ├── SKILL.md                        ← Claude entry point
    ├── agents/                         ← prompt files
    ├── tools/                          ← orchestrator, builder, converters
    ├── schemas/                        ← JSON schemas
    ├── templates/                      ← starter files for new users
    └── VERSION
```

## License

MIT (TBD — see LICENSE).
