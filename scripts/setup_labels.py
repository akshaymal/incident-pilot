#!/usr/bin/env python3
"""
Create or update all GitHub labels for incident-pilot with distinct colors.

Labels follow a consistent color scheme by category:
  - type:*     blue tones
  - priority:* red/orange/yellow severity gradient
  - area:*     varied hues by domain
  - agent-ready  bright green (signals actionability)

Usage:
    GITHUB_TOKEN=<pat> python3 scripts/setup_labels.py [--owner OWNER] [--repo REPO]

Defaults to akshaymal/incident-pilot; override via flags or env vars
GITHUB_OWNER / GITHUB_REPO.
"""

import argparse
import os
import sys
import time

import requests

LABELS = [
    # ── Type ──────────────────────────────────────────────────────────
    {"name": "type: feature",     "color": "0075ca", "description": "New capability"},
    {"name": "type: bug",         "color": "d73a4a", "description": "Something is broken"},
    {"name": "type: chore",       "color": "e4e669", "description": "Maintenance, tooling, docs"},
    # ── Priority ──────────────────────────────────────────────────────
    {"name": "priority: P1",      "color": "b60205", "description": "Must-fix this sprint"},
    {"name": "priority: P2",      "color": "e99695", "description": "Important but not urgent"},
    {"name": "priority: P3",      "color": "fef2c0", "description": "Nice-to-have"},
    # ── Area ──────────────────────────────────────────────────────────
    {"name": "area: agent",       "color": "1d76db", "description": "LangGraph agent logic"},
    {"name": "area: mcp",         "color": "5319e7", "description": "MCP tool servers"},
    {"name": "area: memory",      "color": "0052cc", "description": "Graphiti / Neo4j memory layer"},
    {"name": "area: sandbox",     "color": "006b75", "description": "E2B sandboxed execution"},
    {"name": "area: observability","color": "0e8a16", "description": "Langfuse instrumentation"},
    {"name": "area: audit",       "color": "d93f0b", "description": "Postgres audit log"},
    {"name": "area: ui",          "color": "c5def5", "description": "Next.js / CopilotKit frontend"},
    {"name": "area: infra",       "color": "bfd4f2", "description": "Docker Compose, CI, tooling"},
    {"name": "area: docs",        "color": "cfd3d7", "description": "Documentation"},
    # ── Special ───────────────────────────────────────────────────────
    {"name": "agent-ready",       "color": "2cbe4e", "description": "Issue has unambiguous acceptance criteria; ready for agent pickup"},
]


def upsert_label(session: requests.Session, base_url: str, label: dict) -> str:
    """Create or update a label; return 'created', 'updated', or 'unchanged'."""
    name = label["name"]
    get_resp = session.get(f"{base_url}/labels/{requests.utils.quote(name)}")

    if get_resp.status_code == 200:
        existing = get_resp.json()
        if existing["color"] == label["color"] and existing.get("description", "") == label.get("description", ""):
            return "unchanged"
        resp = session.patch(
            f"{base_url}/labels/{requests.utils.quote(name)}",
            json={"color": label["color"], "description": label.get("description", "")},
        )
        resp.raise_for_status()
        return "updated"

    if get_resp.status_code == 404:
        resp = session.post(f"{base_url}/labels", json=label)
        resp.raise_for_status()
        return "created"

    get_resp.raise_for_status()
    return "error"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "akshaymal"))
    parser.add_argument("--repo",  default=os.environ.get("GITHUB_REPO",  "incident-pilot"))
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    base_url = f"https://api.github.com/repos/{args.owner}/{args.repo}"
    print(f"Syncing labels → {args.owner}/{args.repo}\n")

    counts = {"created": 0, "updated": 0, "unchanged": 0}
    for label in LABELS:
        result = upsert_label(session, base_url, label)
        counts[result] = counts.get(result, 0) + 1
        icon = {"created": "+", "updated": "~", "unchanged": "·"}.get(result, "?")
        print(f"  [{icon}] {label['name']}")
        time.sleep(0.1)  # stay well under the GitHub API rate limit

    print(f"\nDone — {counts['created']} created, {counts['updated']} updated, {counts['unchanged']} unchanged")


if __name__ == "__main__":
    main()
