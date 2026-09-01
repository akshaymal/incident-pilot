"""Tests for scripts/seed_data.py's generated synthetic corpus.

Output is randomized per run (no fixed seed -- see the script's docstring),
so these assert structure, counts, and distribution shape, not exact
content. Runs the generator once in a session-scoped fixture so all tests
share one generated corpus.
"""

import json
import subprocess
import sys
from collections import Counter
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
    assert 60 <= len(tickets) <= 100


def test_incident_count_in_range(seeded_data):
    _, incidents, _ = seeded_data
    assert 15 <= len(incidents) <= 20


def test_runbook_count_in_range(seeded_data):
    _, _, runbook_paths = seeded_data
    assert 20 <= len(runbook_paths) <= 30


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


def test_ticket_category_distribution_is_skewed(seeded_data):
    """Category weighting is intentionally non-uniform (see CATEGORY_WEIGHTS
    in seed_data.py) -- assert the generated data actually reflects that
    rather than accidentally landing close to a 20% uniform split."""
    tickets, _, _ = seeded_data
    counts = Counter(t["category"] for t in tickets)
    total = len(tickets)
    shares = {cat: n / total for cat, n in counts.items()}
    assert max(shares.values()) - min(shares.values()) > 0.05


def test_ticket_text_length_varies(seeded_data):
    """Writer-quality variation should produce both short and long
    descriptions, not a uniform shape."""
    tickets, _, _ = seeded_data
    lengths = [len(t["description"]) for t in tickets]
    assert min(lengths) < 120
    assert max(lengths) > 150


def test_runbook_frontmatter_has_required_fields(seeded_data):
    _, _, runbook_paths = seeded_data
    for path in runbook_paths:
        frontmatter = _runbook_frontmatter(path)
        assert "title" in frontmatter
        assert "categories" in frontmatter
        assert isinstance(frontmatter["categories"], list)
        assert frontmatter.get("status") in {"current", "outdated"}


def test_runbook_category_minimums(seeded_data):
    _, _, runbook_paths = seeded_data
    frontmatters = [_runbook_frontmatter(p) for p in runbook_paths]
    for category in VALID_CATEGORIES:
        current_count = sum(
            1
            for fm in frontmatters
            if category in fm["categories"] and fm.get("status") == "current"
        )
        assert current_count >= 3, f"{category} has only {current_count} current runbooks"


def test_at_least_one_multi_category_runbook(seeded_data):
    _, _, runbook_paths = seeded_data
    frontmatters = [_runbook_frontmatter(p) for p in runbook_paths]
    assert any(len(fm["categories"]) >= 2 for fm in frontmatters)


def test_at_least_one_outdated_runbook(seeded_data):
    _, _, runbook_paths = seeded_data
    frontmatters = [_runbook_frontmatter(p) for p in runbook_paths]
    assert any(fm.get("status") == "outdated" for fm in frontmatters)


def test_category_coverage(seeded_data):
    """Every ticket category must have at least one *current* runbook."""
    tickets, _, runbook_paths = seeded_data
    ticket_categories = {t["category"] for t in tickets}
    current_runbook_categories: set[str] = set()
    for path in runbook_paths:
        frontmatter = _runbook_frontmatter(path)
        if frontmatter.get("status") == "current":
            current_runbook_categories.update(frontmatter["categories"])
    assert ticket_categories.issubset(current_runbook_categories)
