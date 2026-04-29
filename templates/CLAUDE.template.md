# Personal Job Search Configuration

This file is read by Claude at the start of every session and overrides default skill behavior. Edit it to match your style and preferences.

## User Profile

- **Name**: REPLACE_WITH_YOUR_NAME
- **Target Levels**: e.g. Senior Engineer / Engineering Manager / VP Engineering
- **Background**: 1–2 sentences about your career arc
- **Core Strengths**: 3–5 bullet points
- **Education**: highest degree and institution

## Writing Style Rules

- **NEVER use em-dashes.** Use commas, periods, or restructure the sentence. This applies to ALL generated text: cover letters, hiring manager messages, resume bullets.
- **Voice**: conversational and direct. Specific references to JD content. Short declarative sentences mixed with longer ones. First person, relaxed punctuation.
- **Banned phrases**:
  - "I'd love to" / "I'm excited to" / "I look forward to"
  - "I believe that" / "I'm passionate about"
  - "leveraging" / "synergy" / "champion"
- **Sign-off**: customize this. Default is just first name, no dash prefix, no "Best regards"

## Pipeline Configuration

- **Master resume location**: `master-resumes/`
- **Master resume current version**: `v1` (update when you cut a new master)
- **Default resume filename pattern**: `{firstname-lastname}-{level}-v{N}.docx` where level is generic (manager/director/vp/cto/principal)
- **Cover letter naming**: `cover-letter-{descriptor}-v{N}.md` where descriptor is a 2–4 word slug for the angle

## Per-Tailoring Behavior

- **Always update the KB.** When a tailoring session surfaces new facts about your experience, immediately add them to `experience-kb.json` and append a `tailoring_session_notes` entry.
- **Honest scoring.** ATS scoring is a gatekeeper, not a cheerleader. Don't inflate.
- **No fabrication.** If a JD requires X and you don't have X, ask before tailoring. Either get the gap filled with real experience or acknowledge it in the cover letter.

## Application Tracking

Every application tracks its outcome in `jobs.json` under `interview_progress`. Update after every recruiter screen, hiring manager call, technical round, or final outcome. Use the standardized signal tags so you can see patterns across applications:

- `cultural_fit`, `domain_expertise`, `leadership_depth`, `technical_depth`, `org_design`, `overqualification_concern`, `comp_alignment`, `motivation_clarity`, `startup_vs_enterprise`, `communication`

## Quality Gates

Before marking any application as READY:

- ATS score ≥75/100
- No false claims or fabricated experience
- Cover letter reviewed for human authenticity (no LLM tells)
- Resume maintains your core positioning and identity
- All artifacts logged in `jobs.json`

## Personal Notes

Add free-form notes here that the skill should remember across sessions. Examples:
- Specific stories you've used in cover letters that worked well
- Confidential context about why you left previous roles
- Salary expectations that should be applied to scoring decisions
- Companies you've decided to no longer pursue and why
