#!/usr/bin/env python3
"""
Pipeline orchestrator for the resume builder skill.

This script handles the deterministic parts of the pipeline:
- Setting up the application folder with the correct flat structure
- Writing initial files (raw-jd.txt, source.json)
- Invoking the resume builder and format converter
- Auto-committing the final state to git

The agent-driven steps (JD analysis, ATS scoring, tailoring, cover letter) are
expected to be performed by Claude (via the agents in `agents/`). This script
provides the scaffolding around those steps.

Usage:
    # Set up a new application folder from a JD
    python pipeline.py init --jd path/to/raw-jd.txt --slug company-role-year

    # After Claude has produced resume-content.json, build the docx + pdf
    python pipeline.py build --slug company-role-year --resume-name jmonstad-vp-v1

    # Auto-commit the application folder to git
    python pipeline.py commit --slug company-role-year --score 79

    # Check for skill updates
    python pipeline.py check-update
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve the user's data repo as the parent of this skill directory
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_REPO = SKILL_DIR.parent  # the parent dir containing skill/ as a submodule


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def slug_dir(slug: str) -> Path:
    return DATA_REPO / "job-applications" / slug


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new application folder."""
    slug = args.slug
    if not re.match(r"^[a-z0-9][a-z0-9-]+[a-z0-9]$", slug):
        print(
            f"ERROR: slug '{slug}' must be lowercase alphanumeric with hyphens",
            file=sys.stderr,
        )
        return 1

    app_dir = slug_dir(slug)
    if app_dir.exists() and not args.force:
        print(
            f"ERROR: {app_dir} already exists. Use --force to overwrite.", file=sys.stderr
        )
        return 1

    app_dir.mkdir(parents=True, exist_ok=True)

    # Copy raw JD
    if args.jd:
        jd_text = Path(args.jd).read_text()
        (app_dir / "raw-jd.txt").write_text(jd_text)

    # Write source.json
    source = {
        "job_url": args.url,
        "source": args.source or "manual entry",
        "captured_date": utc_now_iso(),
    }
    (app_dir / "source.json").write_text(json.dumps(source, indent=2) + "\n")

    print(f"Initialized {app_dir}")
    print("Next steps:")
    print(f"  1. Run JD analyzer agent against {app_dir}/raw-jd.txt")
    print(f"  2. Run education-requirements-check agent")
    print(f"  3. Run ATS scorer (round 1)")
    print(f"  4. Run resume tailor (writes resume-content.json)")
    print(f"  5. python pipeline.py build --slug {slug} --resume-name <name>")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build the docx and pdf from resume-content.json."""
    slug = args.slug
    resume_name = args.resume_name

    app_dir = slug_dir(slug)
    content_file = app_dir / "resume-content.json"
    if not content_file.exists():
        print(
            f"ERROR: {content_file} not found. The resume tailor agent must produce this first.",
            file=sys.stderr,
        )
        return 1

    docx_path = app_dir / f"{resume_name}.docx"

    # Build docx
    cmd_docx = [
        sys.executable,
        str(SKILL_DIR / "tools" / "resume_builder.py"),
        "--content",
        str(content_file),
        "--output",
        str(docx_path),
    ]
    if args.style:
        cmd_docx.extend(["--style", args.style])

    result = subprocess.run(cmd_docx)
    if result.returncode != 0:
        return result.returncode

    # Convert to pdf
    cmd_pdf = [
        sys.executable,
        str(SKILL_DIR / "tools" / "format_converter.py"),
        "--input",
        str(docx_path),
        "--output-dir",
        str(app_dir),
    ]
    result = subprocess.run(cmd_pdf)
    return result.returncode


def cmd_commit(args: argparse.Namespace) -> int:
    """Auto-commit the application folder to git."""
    slug = args.slug
    app_dir = slug_dir(slug)
    if not app_dir.exists():
        print(f"ERROR: {app_dir} does not exist", file=sys.stderr)
        return 1

    # Build commit message from application metadata
    jd_analysis_file = app_dir / "jd-analysis.json"
    company = "unknown"
    title = "unknown"
    if jd_analysis_file.exists():
        try:
            jd = json.loads(jd_analysis_file.read_text())
            company = jd.get("basic_info", {}).get("company", "unknown")
            title = jd.get("basic_info", {}).get("title", "unknown")
        except Exception:
            pass

    score_part = f" (ATS {args.score})" if args.score else ""
    msg = f"feat: add {company} {title} application{score_part}"

    # Stage application dir + jobs.json + experience-kb.json (any may have changed)
    paths_to_add = [
        str(app_dir.relative_to(DATA_REPO)),
        "jobs.json",
        "experience-kb.json",
    ]
    paths_to_add = [p for p in paths_to_add if (DATA_REPO / p).exists()]

    subprocess.run(["git", "-C", str(DATA_REPO), "add", *paths_to_add], check=True)

    # Check if there's anything to commit
    diff_check = subprocess.run(
        ["git", "-C", str(DATA_REPO), "diff", "--cached", "--quiet"]
    )
    if diff_check.returncode == 0:
        print("Nothing to commit.")
        return 0

    subprocess.run(
        ["git", "-C", str(DATA_REPO), "commit", "-m", msg], check=True
    )

    if args.push:
        subprocess.run(["git", "-C", str(DATA_REPO), "push"], check=True)

    print(f"Committed: {msg}")
    return 0


def get_local_skill_version() -> str | None:
    version_file = SKILL_DIR / "VERSION"
    if not version_file.exists():
        return None
    return version_file.read_text().strip()


def cmd_check_update(args: argparse.Namespace) -> int:
    """Check if a newer skill version exists upstream."""
    local = get_local_skill_version()
    if local is None:
        print("Local VERSION file not found. Skipping update check.")
        return 0

    # Get remote tags via the submodule's origin
    result = subprocess.run(
        ["git", "-C", str(SKILL_DIR), "ls-remote", "--tags", "origin"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Could not fetch remote tags: {result.stderr}", file=sys.stderr)
        return 0  # not fatal

    # Parse tags like "refs/tags/v0.2.0" → "0.2.0"
    tags = []
    for line in result.stdout.splitlines():
        m = re.search(r"refs/tags/v?(\d+\.\d+\.\d+)$", line)
        if m:
            tags.append(m.group(1))

    if not tags:
        print(f"No semver tags found upstream. Local version: {local}")
        return 0

    def parse_version(v: str) -> tuple[int, int, int]:
        return tuple(int(x) for x in v.split("."))  # type: ignore

    latest = max(tags, key=parse_version)
    local_clean = local.lstrip("v")

    if parse_version(latest) > parse_version(local_clean):
        print(f"Skill update available: local v{local_clean} -> upstream v{latest}")
        print("To update: cd skill && git fetch --tags && git checkout v{latest}".format(latest=latest))
        return 2  # non-zero but distinguishable from error
    else:
        print(f"Skill is up to date (v{local_clean})")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume builder pipeline orchestrator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize an application folder")
    p_init.add_argument("--slug", required=True)
    p_init.add_argument("--jd", help="Path to raw JD text file")
    p_init.add_argument("--url", help="Source URL of the JD")
    p_init.add_argument("--source", help="Where the JD came from (e.g. 'LinkedIn')")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_build = sub.add_parser("build", help="Build docx + pdf from resume-content.json")
    p_build.add_argument("--slug", required=True)
    p_build.add_argument("--resume-name", required=True, help="e.g. jmonstad-vp-v1")
    p_build.add_argument("--style", help="Optional style.json path")
    p_build.set_defaults(func=cmd_build)

    p_commit = sub.add_parser("commit", help="Auto-commit application folder")
    p_commit.add_argument("--slug", required=True)
    p_commit.add_argument("--score", type=int, help="Final ATS score for commit message")
    p_commit.add_argument("--push", action="store_true", help="Push after committing")
    p_commit.set_defaults(func=cmd_commit)

    p_check = sub.add_parser("check-update", help="Check for newer skill version")
    p_check.set_defaults(func=cmd_check_update)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
