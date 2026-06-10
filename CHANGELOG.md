# Changelog

All notable changes to this skill will be documented in this file.

## [0.2.0] - 2026-06-10

Authenticity enforcement and orchestration overhaul, driven by a full-corpus audit that found cross-application AI tells the per-application checks missed.

### Added
- `STYLE.md`: all generic writing, voice, resume-identity, altitude, and freshness rules now live in the skill as defaults; the user's `CLAUDE.md` is personal profile + overrides only
- `tools/lint_artifacts.py`: deterministic gate run before READY — banned phrases/constructions (incl. defensive-authenticity tics like "not a slide" and "Not as X. As Y.", unfalsifiable boost pairs like "measurable, provable"), verbatim JD-echo n-grams, and cross-application repetition in cover letters and resume summaries; writes `lint-report.json`
- Altitude rules: VP+ resumes lead with org/business outcomes, never stack enumeration or IDE plugin names
- Cover letter freshness rules: no fixed skeleton, rotate proof points and closers, read recent letters before drafting
- Echo evidence requirement: the ATS scorer must quote candidate/JD phrase pairs (or the comparisons it ran) before asserting "no echoes"
- Length rules in `STYLE.md`: single-page constraint retired; two pages is the standard for leadership resumes, early-career roles return as a compact "Earlier roles" block, no dangling near-empty second page
- `format_converter.py` reports the PDF page count after conversion (warns above two pages)

### Changed
- Pipeline orchestration: ATS scorer and recruiter evaluator MUST run as fresh subagents that never see the tailoring conversation (a scorer that watched the resume being written cannot be adversarial toward it); JD analysis + education check run in parallel; post-tailor build/score/letter run in parallel; KB gap questions are batched into one ask
- READY now requires: ATS ≥75 from an independent run, lint pass, echo evidence present, and recruiter-evaluator combined recommendation of POSSIBLE+ (level-fit can no longer be papered over by a high ATS score without an explicit recorded user override)
- `CLAUDE.template.md` slimmed to personal-only content (profile, overrides, targeting strategy, notes)
- Quality gates, KB maintenance, application tracking, and commit policy moved from the user template into `SKILL.md`

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
