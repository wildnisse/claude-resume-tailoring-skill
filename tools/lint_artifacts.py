#!/usr/bin/env python3
"""Deterministic authenticity lint for application artifacts.

Enforces the rules in STYLE.md that can be checked mechanically:
  1. Banned phrases and constructions (em-dashes, LLM filler, confessional
     hedging, defensive-authenticity tics, unfalsifiable boost pairs).
  2. JD echo: word sequences shared between an artifact and the raw JD.
  3. Cross-application repetition: word sequences shared with artifacts
     from OTHER applications (the template showing).

Usage:
    python lint_artifacts.py --slug company-role-2026 [--repo /path/to/repo]
    python lint_artifacts.py --file path/to/cover-letter.md [--jd path/to/raw-jd.txt]

Exit code 0 = clean, 1 = violations found, 2 = usage/IO error.
Writes job-applications/{slug}/lint-report.json when run with --slug.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# --- Rule definitions ----------------------------------------------------

EM_DASH = "—"

# Case-insensitive substring matches. Keep in sync with STYLE.md.
BANNED_PHRASES = [
    "i'd love to", "i would love to",
    "i'm excited to", "i am excited to",
    "i look forward to",
    "i believe that",
    "i'm passionate about", "i am passionate about",
    "leveraging", "synergy", "spearheaded", "transformative",
    "i'd be a great fit", "i would be a great fit",
    "i am writing to apply", "i'm writing to apply",
    # confessional hedging
    "the honest stretch", "the honest gap", "to be honest",
    "my honest take", "i'll be straight", "i will be straight",
    "i want to be straight", "full transparency", "if i'm being honest",
    "if i am being honest",
    # defensive authenticity
    "not a slide", "not slides", "not a deck", "not a side experiment",
    "not as a demo",
    # unfalsifiable boost pairs
    "measurable, provable", "real, tangible", "concrete, demonstrable",
]

# Regex rules: (name, pattern, explanation)
BANNED_PATTERNS = [
    ("not-as-x-as-y",
     re.compile(r"\bNot as [^.!?\n]{2,60}[.!?] As [^.!?\n]{2,60}[.!?]"),
     "Contrast-fragment tic ('Not as X. As Y.') — defensive authenticity, see STYLE.md"),
    ("champion-verb",
     re.compile(r"\bchampion(ed|ing|s)?\b", re.IGNORECASE),
     "'champion' family is banned"),
]

# Closers that are worn out across the corpus; warn, don't fail.
OVERUSED_CLOSERS = ["happy to talk", "i would welcome a conversation"]

JD_ECHO_NGRAM = 5          # words; shared sequence with the JD this long is an echo
CROSS_APP_NGRAM = 8        # words; shared sequence with another application's artifact

# NOTE: exact n-gram matching catches verbatim echoes only. Paraphrased echoes
# ("translating technical capabilities into customer value" vs the JD's
# "translate technical capabilities into customer-facing value") are the
# independent ATS scorer's job; it must quote candidate/JD phrase pairs.
STOPWORDS = set("""a an and the of to in for with on at as is are was be been i my
have has had that this it by or from""".split())

# --- Text helpers --------------------------------------------------------


def normalize_words(text):
    """Lowercase word list with punctuation stripped (apostrophes kept)."""
    return re.findall(r"[a-z0-9']+", text.lower())


def ngrams(words, n):
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def content_grams(grams):
    """Drop n-grams made (almost) entirely of stopwords."""
    keep = set()
    for g in grams:
        ws = g.split()
        if sum(1 for w in ws if w not in STOPWORDS) >= max(2, len(ws) // 2):
            keep.add(g)
    return keep


def shared_sequences(text_a, text_b, n):
    a = content_grams(ngrams(normalize_words(text_a), n))
    b = ngrams(normalize_words(text_b), n)
    return sorted(a & b)


def collapse_overlapping(seqs):
    """Drop n-grams fully contained in a longer reported sequence."""
    out = []
    for s in seqs:
        if not any(s != t and s in t for t in seqs):
            out.append(s)
    return out


# --- Artifact extraction --------------------------------------------------


def texts_from_resume_content(path):
    """Pull human-visible prose out of resume-content.json."""
    data = json.loads(path.read_text())
    chunks = []

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str) and len(obj.split()) >= 4:
            chunks.append(obj)

    walk(data)
    return "\n".join(chunks)


def gather_artifacts(app_dir):
    """Return (all_texts, fresh_texts) for one application dir.

    all_texts: everything lintable — used for banned-phrase and JD-echo checks.
    fresh_texts: cover letters + resume summary only — used for the
    cross-application check. Experience bullets, dates, and metrics are
    SUPPOSED to be identical across applications (consistency is what truth
    looks like); only letters and summaries must be written fresh.
    """
    all_texts, fresh_texts = {}, {}
    for md in sorted(app_dir.glob("cover-letter-*.md")):
        all_texts[md.name] = fresh_texts[md.name] = md.read_text()
    for rc in sorted(app_dir.glob("resume-content*.json")):
        try:
            all_texts[rc.name] = texts_from_resume_content(rc)
            summary = json.loads(rc.read_text()).get("summary")
            if isinstance(summary, str) and summary.strip():
                fresh_texts[f"{rc.name}:summary"] = summary
        except (json.JSONDecodeError, OSError):
            pass
    return all_texts, fresh_texts


# --- Checks ---------------------------------------------------------------


def check_banned(label, text):
    findings = []
    low = text.lower()
    if EM_DASH in text:
        findings.append({"check": "em-dash", "artifact": label,
                         "detail": f"{text.count(EM_DASH)} em-dash(es) found"})
    for phrase in BANNED_PHRASES:
        if phrase in low:
            findings.append({"check": "banned-phrase", "artifact": label,
                             "detail": f"banned phrase: {phrase!r}"})
    for name, pat, why in BANNED_PATTERNS:
        m = pat.search(text)
        if m:
            findings.append({"check": name, "artifact": label,
                             "detail": f"{why}: {m.group(0)[:90]!r}"})
    return findings


def check_overused(label, text):
    low = text.lower()
    return [{"check": "overused-closer", "artifact": label,
             "detail": f"worn-out closer: {c!r} — rotate per STYLE.md"}
            for c in OVERUSED_CLOSERS if c in low]


def check_jd_echo(label, text, jd_text):
    seqs = collapse_overlapping(shared_sequences(text, jd_text, JD_ECHO_NGRAM))
    return [{"check": "jd-echo", "artifact": label,
             "detail": f"shared with JD: {s!r}"} for s in seqs]


def check_cross_app(label, text, other_apps):
    findings = []
    for other_slug, other_texts in other_apps.items():
        for other_label, other_text in other_texts.items():
            seqs = collapse_overlapping(
                shared_sequences(text, other_text, CROSS_APP_NGRAM))
            for s in seqs:
                findings.append({
                    "check": "cross-app-repetition", "artifact": label,
                    "detail": f"shared with {other_slug}/{other_label}: {s!r}"})
    return findings


# --- Main -----------------------------------------------------------------


def lint_application(repo, slug):
    app_dir = repo / "job-applications" / slug
    if not app_dir.is_dir():
        print(f"error: no such application dir: {app_dir}", file=sys.stderr)
        return None

    artifacts, fresh = gather_artifacts(app_dir)
    if not artifacts:
        print(f"error: no lintable artifacts in {app_dir}", file=sys.stderr)
        return None

    jd_path = app_dir / "raw-jd.txt"
    jd_text = jd_path.read_text() if jd_path.exists() else ""

    other_apps = {}
    for other in (repo / "job-applications").iterdir():
        if other.is_dir() and other.name != slug:
            _, other_fresh = gather_artifacts(other)
            if other_fresh:
                other_apps[other.name] = other_fresh

    errors, warnings = [], []
    for label, text in artifacts.items():
        errors += check_banned(label, text)
        warnings += check_overused(label, text)
        if jd_text:
            errors += check_jd_echo(label, text, jd_text)
    for label, text in fresh.items():
        warnings += check_cross_app(label, text, other_apps)

    report = {
        "slug": slug,
        "artifacts_checked": sorted(artifacts),
        "pass": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    (app_dir / "lint-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def lint_single_file(path, jd_path):
    text = path.read_text()
    label = path.name
    errors = check_banned(label, text)
    warnings = check_overused(label, text)
    if jd_path:
        errors += check_jd_echo(label, text, Path(jd_path).read_text())
    return {"artifacts_checked": [label], "pass": not errors,
            "errors": errors, "warnings": warnings}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug", help="application slug under job-applications/")
    ap.add_argument("--repo", default=".", help="repo root (default: cwd)")
    ap.add_argument("--file", help="lint a single file instead of a slug")
    ap.add_argument("--jd", help="raw JD text for --file echo checking")
    args = ap.parse_args()

    if args.file:
        report = lint_single_file(Path(args.file), args.jd)
    elif args.slug:
        report = lint_application(Path(args.repo).resolve(), args.slug)
        if report is None:
            return 2
    else:
        ap.print_help()
        return 2

    for e in report["errors"]:
        print(f"ERROR [{e['check']}] {e['artifact']}: {e['detail']}")
    for w in report["warnings"]:
        print(f"warn  [{w['check']}] {w['artifact']}: {w['detail']}")
    n_err, n_warn = len(report["errors"]), len(report["warnings"])
    print(f"{'PASS' if report['pass'] else 'FAIL'}: "
          f"{n_err} error(s), {n_warn} warning(s) "
          f"across {len(report['artifacts_checked'])} artifact(s)")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
