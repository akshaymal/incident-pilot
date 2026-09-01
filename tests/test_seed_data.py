"""Tests for scripts/seed_data.py's generated synthetic corpus.

Output is randomized per run (no fixed seed -- see the script's docstring),
so these assert structure and counts, not exact content. Runs the generator
once in a session-scoped fixture so all tests share one generated corpus.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "synthetic"

REQUIRED_TICKET_FIELDS = {
    "id",
    "title",
    "description",
    "category",
    "priority",
    "status",
    "created_at",
}
REQUIRED_INCIDENT_FIELDS = {
    "id",
    "category",
    "title",
    "occurred_at",
    "resolved_at",
    "resolution_summary",
    "root_cause",
}
VALID_CATEGORIES = {"network", "vpn_access", "hardware", "software", "security"}


@pytest.fixture(scope="session")
def seeded_data():
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "seed_data.py")],
        cwd=REPO_ROOT,
        check=True,
    )
    tickets = json.loads((DATA_DIR / "tickets.json").read_text())
    incidents = json.loads((DATA_DIR / "incidents.json").read_text())
    runbook_paths = sorted((DATA_DIR / "runbooks").glob("*.md"))
    return tickets, incidents, runbook_paths


def _runbook_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} missing YAML frontmatter"
    _, frontmatter, _ = text.split("---\n", 2)
    return yaml.safe_load(frontmatter)


def test_files_exist(seeded_data):
    tickets, incidents, runbook_paths = seeded_data
    assert tickets
    assert incidents
    assert runbook_paths


def test_ticket_count_in_range(seeded_data):
    tickets, _, _ = seeded_data
    assert 30 <= len(tickets) <= 50


def test_incident_count_in_range(seeded_data):
    _, incidents, _ = seeded_data
    assert 15 <= len(incidents) <= 20


def test_runbook_count_in_range(seeded_data):
    _, _, runbook_paths = seeded_data
    assert 10 <= len(runbook_paths) <= 15


def test_ticket_required_fields(seeded_data):
    tickets, _, _ = seeded_data
    for ticket in tickets:
        assert REQUIRED_TICKET_FIELDS.issubset(ticket.keys())
        assert ticket["category"] in VALID_CATEGORIES


def test_incident_required_fields(seeded_data):
    _, incidents, _ = seeded_data
    for incident in incidents:
        assert REQUIRED_INCIDENT_FIELDS.issubset(incident.keys())
        assert incident["category"] in VALID_CATEGORIES


def test_at_least_four_categories_covered(seeded_data):
    tickets, _, _ = seeded_data
    categories = {t["category"] for t in tickets}
    assert len(categories) >= 4


def test_runbook_frontmatter_has_title_and_categories(seeded_data):
    _, _, runbook_paths = seeded_data
    for path in runbook_paths:
        frontmatter = _runbook_frontmatter(path)
        assert "title" in frontmatter
        assert "categories" in frontmatter
        assert isinstance(frontmatter["categories"], list)


def test_category_coverage(seeded_data):
    tickets, _, runbook_paths = seeded_data
    ticket_categories = {t["category"] for t in tickets}
    runbook_categories: set[str] = set()
    for path in runbook_paths:
        frontmatter = _runbook_frontmatter(path)
        runbook_categories.update(frontmatter["categories"])
    assert ticket_categories.issubset(runbook_categories)
