#!/usr/bin/env python3
"""Guard against hardcoded ticket/runbook/incident data or real-looking PII.

Ground rule (CLAUDE.md): all ticket/runbook/incident data must come from
scripts/seed_data.py -- never invented inline in code, so the dataset stays
inspectable and regeneratable, and never real personal/company data. This is
a heuristic check, not a proof: it flags likely violations for a human to
confirm, it doesn't try to be exhaustive.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files allowed to contain data-shaped literals -- the generator itself, and
# this script's own patterns.
ALLOWED_FILES = {
    "scripts/seed_data.py",
    "scripts/check_synthetic_data.py",
}

# Heuristic 1: dict/list literals keyed like ticket/runbook/incident records,
# defined outside the generator -- a sign data was hand-authored inline
# instead of produced by scripts/seed_data.py.
DATA_KEY_PATTERN = re.compile(r'["\'](ticket_id|runbook_id|incident_id)["\']\s*:')

# Heuristic 2: real-looking PII -- email addresses on common public/consumer
# domains, or US-style SSNs. Synthetic data should use placeholder domains
# (e.g. example.com, acme-corp.test) rather than real ones.
REAL_EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com",
    re.IGNORECASE,
)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def tracked_python_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO_ROOT / p for p in result.stdout.splitlines() if p]


def check_file(path: Path) -> list[str]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in ALLOWED_FILES:
        return []

    findings = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if DATA_KEY_PATTERN.search(line):
            findings.append(
                f"{rel}:{lineno}: looks like a hardcoded ticket/runbook/incident "
                "record -- data must come from scripts/seed_data.py"
            )
        if REAL_EMAIL_PATTERN.search(line):
            findings.append(
                f"{rel}:{lineno}: real-looking email domain -- use a placeholder "
                "domain (e.g. example.com) in synthetic data"
            )
        if SSN_PATTERN.search(line):
            findings.append(f"{rel}:{lineno}: looks like a real SSN pattern")
    return findings


def main() -> int:
    files = tracked_python_files()
    if not files:
        print("No Python files yet -- nothing to check.")
        return 0

    all_findings: list[str] = []
    for f in files:
        all_findings.extend(check_file(f))

    if all_findings:
        print("Synthetic-data guard failed:\n")
        for finding in all_findings:
            print(f"  {finding}")
        print(
            "\nIf this is a false positive, adjust the pattern in "
            "scripts/check_synthetic_data.py rather than bypassing the check."
        )
        return 1

    print("Synthetic-data guard passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
