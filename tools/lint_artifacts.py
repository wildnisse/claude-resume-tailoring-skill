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
from collections import Counter
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
    # balanced antithesis openers (workshopped "quotable" line — reads as written, not lived)
    "equally at home", "equal parts", "as much at home", "as comfortable in",
    "as happy in",
]

# Regex rules: (name, pattern, explanation)
BANNED_PATTERNS = [
    ("not-as-x-as-y",
     re.compile(r"\bNot as [^.!?\n]{2,60}[.!?] As [^.!?\n]{2,60}[.!?]"),
     "Contrast-fragment tic ('Not as X. As Y.') — defensive authenticity, see STYLE.md"),
    ("champion-verb",
     re.compile(r"\bchampion(ed|ing|s)?\b", re.IGNORECASE),
     "'champion' family is banned"),
    ("antithesis-part-x-part-y",
     re.compile(r"\bpart\s+\w+,\s*part\s+\w+", re.IGNORECASE),
     "Balanced 'Part X, part Y' antithesis opener — reads as written, not lived (STYLE.md)"),
]

# --- Sentence-level AI tells (STYLE.md "Sentence-level AI tells") ----------
# Heuristic and density-based, so these WARN rather than error.

# Elevated / literary diction that reads as generated in an engineer's resume.
LITERARY_DICTION = re.compile(
    r"\b(estate|tapestry|realm|ethos|crucible|bedrock|linchpin|storied|deftly|"
    r"seamless(?:ly)?|myriad|plethora|pivotal|underpin(?:s|ned|ning)?|"
    r"harness(?:es|ing)?|unlock(?:s|ing)?|elevate(?:s|d)?|elevating)\b",
    re.IGNORECASE)

# "A, B, and C" three-item list (Oxford-comma triple or longer). The tell is
# DENSITY: one or two is human, five in a document is a model.
RULE_OF_THREE = re.compile(r",[^,.;:\n]+,\s+(?:and|or|as well as)\b")
RULE_OF_THREE_LIMIT = 5

# Trailing value-restating coda: "..., the X the business ran on" / "..., with Y".
SENTENCE_SPLIT = re.compile(r"[.\n]+")
APPOSITIVE_LEAD = re.compile(r"^(?:the|with|a|an|\w+ing)\b", re.IGNORECASE)
CLOSING_APPOSITIVE_LIMIT = 2

SUMMARY_WORD_LIMIT = 75
SUMMARY_SENTENCE_LIMIT = 4

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


def prose_from_resume_content(path, include_highlights=True):
    """Human-written prose: summary + experience bullets (+ highlights).

    Excludes titles, company/location, dates, section headers, and education —
    structured fields that legitimately repeat (three 'Director' titles is a
    fact, not a tell) and are not where sentence-level AI tells live.

    The highlights block is a deliberate condensed restatement of the bullets,
    so set include_highlights=False for the repetition/opener checks (otherwise
    every highlight-echoes-a-bullet pair is a false positive). The cadence,
    coda, and diction checks DO include highlights (a florid or triple-stuffed
    highlight is still a tell).
    """
    data = json.loads(path.read_text())
    chunks = []
    summary = data.get("summary")
    if isinstance(summary, str) and summary.strip():
        chunks.append(summary.strip())
    if include_highlights:
        for col in (data.get("highlights") or {}).get("columns", []) or []:
            chunks += [b for b in (col.get("bullets") or []) if isinstance(b, str)]
    for role in data.get("experience", []) or []:
        chunks += [b for b in (role.get("bullets") or []) if isinstance(b, str)]
        sub = role.get("subsection") or {}
        chunks += [b for b in (sub.get("bullets") or []) if isinstance(b, str)]
    return "\n".join(chunks)


def gather_artifacts(app_dir):
    """Return (all_texts, fresh_texts) for one application dir.

    all_texts: everything lintable — used for banned-phrase and JD-echo checks.
    fresh_texts: cover letters + resume summary only — used for the
    cross-application check. Experience bullets, dates, and metrics are
    SUPPOSED to be identical across applications (consistency is what truth
    looks like); only letters and summaries must be written fresh.
    """
    all_texts, fresh_texts, prose_texts, narrative_texts = {}, {}, {}, {}
    for md in sorted(app_dir.glob("cover-letter-*.md")):
        text = md.read_text()
        all_texts[md.name] = fresh_texts[md.name] = text
        prose_texts[md.name] = narrative_texts[md.name] = text
    for rc in sorted(app_dir.glob("resume-content*.json")):
        try:
            all_texts[rc.name] = texts_from_resume_content(rc)
            prose_texts[rc.name] = prose_from_resume_content(rc)
            narrative_texts[rc.name] = prose_from_resume_content(rc, include_highlights=False)
            summary = json.loads(rc.read_text()).get("summary")
            if isinstance(summary, str) and summary.strip():
                fresh_texts[f"{rc.name}:summary"] = summary
        except (json.JSONDecodeError, OSError):
            pass
    return all_texts, fresh_texts, prose_texts, narrative_texts


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


# --- Sentence-level AI-tell checks (warnings) ----------------------------


def split_sentences(text):
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if len(s.split()) >= 4]


def check_rule_of_three(label, text):
    """Relentless three-item lists are the clearest machine cadence."""
    triples = [m.group(0).strip(" ,") for m in RULE_OF_THREE.finditer(text)]
    if len(triples) < RULE_OF_THREE_LIMIT:
        return []
    sample = "; ".join(t[:48] for t in triples[:4])
    return [{"check": "rule-of-three", "artifact": label,
             "detail": f"{len(triples)} three-item lists — the machine cadence; vary list "
                       f"length (cut to two, push to four, restructure). e.g. {sample!r}"}]


def check_closing_appositive(label, text):
    """Trailing comma + value-restating coda: the signature LLM sentence shape."""
    flagged = []
    for s in split_sentences(text):
        if "," not in s:
            continue
        tail = s.rsplit(",", 1)[1].strip().rstrip(".")
        if "," in tail or len(tail.split()) < 4:
            continue
        if tail.split()[0].lower() in ("and", "or", "but", "plus", "including", "so"):
            continue
        if APPOSITIVE_LEAD.match(tail):
            flagged.append(tail)
    if len(flagged) < CLOSING_APPOSITIVE_LIMIT:
        return []
    sample = "; ".join(t[:55] for t in flagged[:3])
    return [{"check": "closing-appositive", "artifact": label,
             "detail": f"{len(flagged)} sentences end with a value-restating coda — "
                       f"state the fact and stop. e.g. {sample!r}"}]


def check_intra_repetition(label, text):
    """A distinctive phrase repeated within one document — say it once."""
    words = normalize_words(text)
    repeated = []
    for n, minct in ((4, 2), (3, 2), (2, 3)):
        counts = Counter(" ".join(words[i:i + n]) for i in range(len(words) - n + 1))
        for gram, ct in counts.items():
            ws = gram.split()
            if ct >= minct and sum(1 for w in ws if w not in STOPWORDS) >= max(2, n // 2):
                repeated.append((gram, ct))
    grams = [g for g, _ in repeated]
    kept = [(g, ct) for g, ct in repeated if not any(g != h and g in h for h in grams)]
    kept.sort(key=lambda x: (-len(x[0].split()), -x[1]))
    if not kept:
        return []
    shown = "; ".join(f"{g!r}×{ct}" for g, ct in kept[:5])
    return [{"check": "intra-repetition", "artifact": label,
             "detail": f"phrase repeated within the document — say it once: {shown}"}]


def check_repeated_openers(label, text):
    """Bullets that all start with the same verb read as templated."""
    firsts = Counter()
    for line in text.split("\n"):
        toks = line.split()
        if len(toks) < 4:
            continue
        w = re.sub(r"[^a-z]", "", toks[0].lower())
        if len(w) >= 3 and w not in STOPWORDS:
            firsts[w] += 1
    rep = sorted([(w, c) for w, c in firsts.items() if c >= 3], key=lambda x: -x[1])
    if not rep:
        return []
    detail = ", ".join(f"{w!r}×{c}" for w, c in rep)
    return [{"check": "repeated-opener", "artifact": label,
             "detail": f"bullets reuse the same opening word — vary them: {detail}"}]


def check_diction(label, text):
    hits = sorted({m.group(0).lower() for m in LITERARY_DICTION.finditer(text)})
    if not hits:
        return []
    return [{"check": "literary-diction", "artifact": label,
             "detail": "elevated/literary diction, use the plain word: "
                       + ", ".join(repr(h) for h in hits)}]


def check_summary(label, summary):
    findings = []
    nwords = len(summary.split())
    nsent = len([s for s in re.split(r"[.!?]+", summary) if s.strip()])
    if nwords > SUMMARY_WORD_LIMIT:
        findings.append({"check": "summary-length", "artifact": label,
                         "detail": f"summary is {nwords} words; keep it under ~{SUMMARY_WORD_LIMIT} — "
                                   "a dense, keyword-stuffed summary reads as generated and gets skipped"})
    if nsent > SUMMARY_SENTENCE_LIMIT:
        findings.append({"check": "summary-density", "artifact": label,
                         "detail": f"summary is {nsent} sentences; keep it to "
                                   f"{SUMMARY_SENTENCE_LIMIT}, identity not catalog"})
    return findings


# Cadence/coda/diction run on full prose (highlights included — a florid or
# triple-stuffed highlight is still a tell). Repetition/opener run on the
# narrative only (highlights deliberately restate bullets; counting that
# overlap would be a false positive on every resume).
CADENCE_CHECKS = (check_rule_of_three, check_closing_appositive, check_diction)
REPETITION_CHECKS = (check_intra_repetition, check_repeated_openers)


# --- Main -----------------------------------------------------------------


def lint_application(repo, slug):
    app_dir = repo / "job-applications" / slug
    if not app_dir.is_dir():
        print(f"error: no such application dir: {app_dir}", file=sys.stderr)
        return None

    artifacts, fresh, prose, narrative = gather_artifacts(app_dir)
    if not artifacts:
        print(f"error: no lintable artifacts in {app_dir}", file=sys.stderr)
        return None

    jd_path = app_dir / "raw-jd.txt"
    jd_text = jd_path.read_text() if jd_path.exists() else ""

    other_apps = {}
    for other in (repo / "job-applications").iterdir():
        if other.is_dir() and other.name != slug:
            _, other_fresh, _, _ = gather_artifacts(other)
            if other_fresh:
                other_apps[other.name] = other_fresh

    errors, warnings = [], []
    for label, text in artifacts.items():
        errors += check_banned(label, text)
        warnings += check_overused(label, text)
        if jd_text:
            errors += check_jd_echo(label, text, jd_text)
    for label, text in prose.items():
        for chk in CADENCE_CHECKS:
            warnings += chk(label, text)
    for label, text in narrative.items():
        for chk in REPETITION_CHECKS:
            warnings += chk(label, text)
    for label, text in fresh.items():
        if label.endswith(":summary"):
            warnings += check_summary(label, text)
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
    summary = ""
    if path.suffix == ".json":
        full = texts_from_resume_content(path)
        prose = prose_from_resume_content(path)
        narrative = prose_from_resume_content(path, include_highlights=False)
        try:
            summary = json.loads(path.read_text()).get("summary") or ""
        except (json.JSONDecodeError, OSError):
            summary = ""
    else:
        full = prose = narrative = path.read_text()
    label = path.name
    errors = check_banned(label, full)
    warnings = check_overused(label, full)
    for chk in CADENCE_CHECKS:
        warnings += chk(label, prose)
    for chk in REPETITION_CHECKS:
        warnings += chk(label, narrative)
    if summary.strip():
        warnings += check_summary(f"{label}:summary", summary)
    if jd_path:
        errors += check_jd_echo(label, full, Path(jd_path).read_text())
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
