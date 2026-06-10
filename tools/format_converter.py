#!/usr/bin/env python3
"""
Convert docx to pdf using LibreOffice (headless).

Usage:
    python format_converter.py --input path/to/file.docx --output-dir path/to/output/

Searches for `soffice` in common locations. On macOS, LibreOffice typically lives
at /Applications/LibreOffice.app/Contents/MacOS/soffice.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


SOFFICE_CANDIDATES = [
    "soffice",
    "libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice",
    "/snap/bin/libreoffice",
]


def find_soffice() -> str | None:
    for candidate in SOFFICE_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
        which = shutil.which(candidate)
        if which:
            return which
    return None


def convert_docx_to_pdf(docx_path: Path, output_dir: Path) -> Path:
    soffice = find_soffice()
    if soffice is None:
        raise RuntimeError(
            "LibreOffice not found. Install it (macOS: `brew install --cask libreoffice`) "
            "or add `soffice` to PATH."
        )
    if not docx_path.exists():
        raise FileNotFoundError(f"Input docx not found: {docx_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            str(docx_path),
            "--outdir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    expected_pdf = output_dir / (docx_path.stem + ".pdf")
    if not expected_pdf.exists():
        raise RuntimeError(f"Expected PDF not produced at {expected_pdf}")
    return expected_pdf


def count_pdf_pages(pdf_path: Path) -> int | None:
    """Best-effort page count: pypdf if available, else a byte-level scan."""
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    try:
        data = pdf_path.read_bytes()
        # Page objects are "/Type /Page"; the page-tree root is "/Type /Pages".
        import re

        return len(re.findall(rb"/Type\s*/Page[^s]", data))
    except OSError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert docx to pdf using LibreOffice")
    parser.add_argument("--input", required=True, type=Path, help="Input docx file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (defaults to input file's directory)",
    )
    args = parser.parse_args()

    output_dir = args.output_dir or args.input.parent

    try:
        pdf = convert_docx_to_pdf(args.input, output_dir)
        pages = count_pdf_pages(pdf)
        if pages is None:
            print(f"Saved: {pdf} (page count unavailable)")
        else:
            print(f"Saved: {pdf} ({pages} page{'s' if pages != 1 else ''})")
            if pages > 2:
                print(
                    f"WARNING: {pages} pages. Resumes should be 1-2 pages; "
                    "trim content or rebalance (see STYLE.md length rules).",
                    file=sys.stderr,
                )
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
