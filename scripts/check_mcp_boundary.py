#!/usr/bin/env python3
"""Guard against agents importing mcp_servers/ code directly.

Ground rule (CLAUDE.md): "Don't collapse the MCP server layer into a plain
function call 'for simplicity'". Runbooks and ticket data must be reached via
a real MCP tool call from the agent graph, not a Python import of the server
module -- see docs/architecture.md's rationale for why this is a
non-negotiable learning goal of the project, not an implementation detail.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "src" / "incident_pilot" / "agents"

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(from|import)\s+incident_pilot\.mcp_servers\b"
)


def main() -> int:
    if not AGENTS_DIR.exists():
        print("src/incident_pilot/agents/ doesn't exist yet -- nothing to check.")
        return 0

    findings = []
    for path in sorted(AGENTS_DIR.rglob("*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN_IMPORT_PATTERN.match(line):
                findings.append(
                    f"{rel}:{lineno}: imports incident_pilot.mcp_servers directly "
                    "-- call it as a real MCP tool instead (see CLAUDE.md ground "
                    "rule 1 and docs/architecture.md)"
                )

    if findings:
        print("MCP-boundary check failed:\n")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print("MCP-boundary check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
