# Changelog

All notable changes to this skill will be documented in this file.

## [0.4.0] - 2026-07-02

ATS scorer slimmed for token cost, runtime, and score discrimination. Funnel data showed the score was not predicting responses while each run burned ~30k input tokens on the full KB and produced 20-30KB score files.

### Added
- `tools/kb_view.py`: independence-safe KB view for the scorer and evaluator. Drops `tailoring_session_notes` and `gap_presentation_strategy` (tailoring rationale an independent judge must not see, and ~half the file's tokens).
- Round types in the scorer: round 1 against the untailored master skips echo/pandering analysis (the master predates the JD) and spends effort on requirements coverage, red flags, and gap questions.
- Full-range scoring guidance: a competent-but-unremarkable fit is 55-65, not 75; 80+ reserved for near-lock fits; identical scores across different JDs means the scoring failed.
- Overall-fit now explicitly weighs recent scope vs role altitude (the strongest observed response predictor) instead of leaving level fit entirely to the evaluator.
- Schema legitimizes the fields the prompt already demanded (`independence`, `echo_check`, `consistency_checks`, `lint_reconciliation`, `gap_questions`).

### Changed
- `agents/ats-scorer.md` rewritten at a third the size; AI-tell taxonomy no longer duplicated from `STYLE.md` (the scorer reads STYLE.md anyway).
- Hard output caps: assessments ≤2 sentences, per-requirement evidence ≤25 words (one quote fragment + role/year), max 3 priority fixes, `tailoring_suggestions` omitted at ≥75, whole score file targeted under 6KB.
- Schema sets `additionalProperties: false` and array caps — no more freelance fields (`bottom_line`, `delta_from_round_1`, `tailoring_ceiling`).
- Rubric weights unchanged (20/20/30/20/10) so historical scores stay roughly comparable, but round-1 baselines will read a few points different now that echo penalties no longer apply to the master.
- `recruiter-evaluator.md` and `SKILL.md` point at the KB view instead of the raw KB.

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
