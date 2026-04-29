# Changelog

All notable changes to this skill will be documented in this file.

## [0.1.0] - 2026-04-29

Initial release.

### Added
- Five core agent prompts: jd-analyzer, ats-scorer, resume-tailor, cover-letter-writer, recruiter-evaluator
- New education-requirements-check agent that flags strong degree signals before tailoring
- Consolidated `resume_builder.py` (replaces per-application Python scripts)
- `format_converter.py` for docx-to-pdf via LibreOffice
- `pipeline.py` orchestrator with init/build/commit/check-update subcommands
- JSON schemas for jd-analysis, ats-score, resume-content, jobs-registry, experience-kb, education-check
- Starter templates for `experience-kb.json`, `jobs.json`, `CLAUDE.md`
- `install.sh` one-line installer with manual fallback documented in README
- Flat per-application output structure (no more 00-jd/01-resume/etc subdirectories)
- Auto-commit with structured commit messages (`feat: add {company} {title} application (ATS {score})`)
- Self-update via submodule tag check at session start
