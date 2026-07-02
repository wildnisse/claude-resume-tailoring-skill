#!/usr/bin/env python3
"""Print the independence-safe scorer/evaluator view of experience-kb.json.

The full KB accumulates tailoring_session_notes and gap_presentation_strategy.
Both are tailoring rationale: an independent scorer that reads them has seen
how the resume was positioned, and they are roughly half the file's tokens.
This view drops them and keeps the verifiable facts (roles, dates, figures,
skills, known gaps).

Usage:
    python kb_view.py [--kb path/to/experience-kb.json]

Exit code 0 on success, 2 on IO/parse error.
"""

import argparse
import json
import sys
from pathlib import Path

EXCLUDE = {"tailoring_session_notes", "gap_presentation_strategy"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kb", default="experience-kb.json",
                    help="path to experience-kb.json (default: ./experience-kb.json)")
    args = ap.parse_args()

    path = Path(args.kb)
    try:
        kb = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return 2

    view = {k: v for k, v in kb.items() if k not in EXCLUDE}
    print(json.dumps(view, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
