#!/usr/bin/env python3
"""Generate the synthetic corpus that Week 1+ components depend on.

Writes tickets, runbooks, and past-incident fixtures to data/synthetic/
(gitignored, fully regeneratable). Pure Python + Faker -- no LLM call, so
this runs with no API key. Output is random each run (no fixed seed); tests
assert structure and counts, not exact content. See CLAUDE.md ground rule 3:
this script is the only source of ticket/runbook/incident data.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from faker import Faker

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "synthetic"

CATEGORIES = ["network", "vpn_access", "hardware", "software", "security"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]

fake = Faker()

# Category-specific templates. Each is (title_template, description_template,
# keywords) where the templates take Faker-generated fill-ins -- this keeps
# every record on-topic for its category while staying fully synthetic.
TICKET_TEMPLATES = {
    "network": [
        (
            "Intermittent connectivity from {host}",
            "User on host {host} in {city} reports dropped connections to "
            "internal services every few minutes. Traceroute shows packet "
            "loss at the {vendor} switch on that floor.",
        ),
        (
            "DNS resolution failing for internal domains",
            "Host {host} cannot resolve *.internal hostnames since this "
            "morning. External DNS lookups work fine; suspect a stale "
            "record on the {vendor} resolver.",
        ),
    ],
    "vpn_access": [
        (
            "VPN client won't connect from {city} office",
            "User {username} gets an authentication timeout in the VPN "
            "client when connecting from the {city} office network. "
            "Works fine over their home connection.",
        ),
        (
            "VPN access revoked after password reset",
            "User {username} reset their password via SSO and now the VPN "
            "client rejects their credentials with an MFA error.",
        ),
    ],
    "hardware": [
        (
            "Laptop won't power on after firmware update",
            "User {username}'s {vendor} laptop (asset tag {asset_tag}) "
            "shows no display and no fan spin-up after a scheduled "
            "firmware update last night.",
        ),
        (
            "Docking station not detecting external monitors",
            "User {username} plugged their {vendor} docking station into "
            "two external monitors; neither is detected in Display "
            "Settings after multiple reboots.",
        ),
    ],
    "software": [
        (
            "{app} crashes on launch after update",
            "User {username} reports {app} crashes immediately on launch "
            "since the update pushed this week. Error log points to a "
            "missing dependency.",
        ),
        (
            "License activation failing for {app}",
            "User {username} cannot activate {app}; the license server "
            "returns a generic error code. Other users on the same "
            "license pool are unaffected.",
        ),
    ],
    "security": [
        (
            "Suspicious login attempt flagged for {username}",
            "The SIEM flagged a login attempt for {username} from an "
            "unrecognized location ({city}) outside business hours. "
            "Account has been temporarily locked pending review.",
        ),
        (
            "Phishing email reported by {username}",
            "User {username} reported a phishing email impersonating IT "
            "support, asking them to reset their password via an "
            "external link.",
        ),
    ],
}

RUNBOOK_TEMPLATES = {
    "network": [
        (
            "Diagnosing Intermittent Network Connectivity",
            "## Symptoms\n\nUsers report dropped connections or high "
            "latency reaching internal services.\n\n## Steps\n\n1. Check "
            "switch port counters for errors or packet loss.\n2. Verify "
            "DNS resolution for internal hostnames using `dig` or "
            "`nslookup`.\n3. Escalate to network engineering if packet "
            "loss is confirmed at the switch level.\n\nKeywords: "
            "connectivity, packet loss, dns, switch, latency.",
        ),
        (
            "Resolving Internal DNS Resolution Failures",
            "## Symptoms\n\nHosts cannot resolve internal (*.internal) "
            "domain names while external DNS works normally.\n\n## Steps"
            "\n\n1. Confirm the host's configured resolver matches the "
            "internal DNS server.\n2. Flush the local DNS cache.\n3. Check "
            "the internal DNS server logs for stale or missing "
            "records.\n\nKeywords: dns, resolver, internal domain, cache.",
        ),
    ],
    "vpn_access": [
        (
            "Troubleshooting VPN Authentication Timeouts",
            "## Symptoms\n\nVPN client hangs or times out during "
            "authentication, especially from office networks.\n\n## Steps"
            "\n\n1. Confirm the VPN gateway is reachable from the user's "
            "network (check for port 443/1194 blocks).\n2. Verify the "
            "user's account is not locked in the identity provider.\n3. "
            "Have the user retry from a different network to isolate "
            "firewall issues.\n\nKeywords: vpn, authentication, timeout, "
            "gateway, mfa.",
        ),
        (
            "Restoring VPN Access After Password Reset",
            "## Symptoms\n\nVPN client rejects credentials with an MFA "
            "error immediately after an SSO password reset.\n\n## Steps"
            "\n\n1. Confirm the SSO password reset propagated to the VPN "
            "identity provider (can take up to 15 minutes).\n2. Ask the "
            "user to re-register their MFA device if propagation is "
            "confirmed complete.\n3. Manually sync the account if delay "
            "exceeds 30 minutes.\n\nKeywords: vpn, password reset, mfa, "
            "sso, access.",
        ),
    ],
    "hardware": [
        (
            "Diagnosing a Laptop That Won't Power On",
            "## Symptoms\n\nNo display, no fan activity, often following a "
            "firmware or BIOS update.\n\n## Steps\n\n1. Confirm the "
            "charger and outlet both work with a known-good device.\n2. "
            "Attempt a hard reset (hold power button 15+ seconds).\n3. If "
            "unresponsive, escalate for board-level firmware recovery.\n\n"
            "Keywords: laptop, power, firmware, bios, hardware.",
        ),
        (
            "Fixing External Monitor Detection on Docking Stations",
            "## Symptoms\n\nDocking station is powered but connected "
            "external monitors are not detected.\n\n## Steps\n\n1. Update "
            "the docking station firmware/drivers.\n2. Test each monitor "
            "port individually to isolate a faulty port.\n3. Reseat the "
            "dock connection and reboot.\n\nKeywords: docking station, "
            "monitor, display, hardware, drivers.",
        ),
    ],
    "software": [
        (
            "Resolving Application Crashes on Launch",
            "## Symptoms\n\nAn application crashes immediately after "
            "launch, often following an update.\n\n## Steps\n\n1. Check "
            "the application's crash log for missing dependencies.\n2. "
            "Reinstall the application's runtime dependencies.\n3. Roll "
            "back to the previous version if the issue persists.\n\n"
            "Keywords: application, crash, launch, dependency, update.",
        ),
        (
            "Fixing License Activation Errors",
            "## Symptoms\n\nAn application fails to activate its license, "
            "returning a generic error code.\n\n## Steps\n\n1. Confirm "
            "the license server is reachable from the user's network.\n2. "
            "Check the license pool for available seats.\n3. Re-issue the "
            "license key if the pool has capacity.\n\nKeywords: license, "
            "activation, software, license server.",
        ),
    ],
    "security": [
        (
            "Responding to Suspicious Login Attempts",
            "## Symptoms\n\nSIEM flags a login attempt from an "
            "unrecognized location or outside business hours.\n\n## Steps"
            "\n\n1. Confirm the account is locked pending review.\n2. "
            "Contact the user through a verified channel to confirm "
            "activity.\n3. Force a password reset and MFA re-enrollment "
            "if the login is not confirmed legitimate.\n\nKeywords: "
            "suspicious login, siem, account lock, security.",
        ),
        (
            "Handling Reported Phishing Emails",
            "## Symptoms\n\nA user reports an email impersonating IT "
            "support or another trusted sender.\n\n## Steps\n\n1. "
            "Preserve the original email with headers for analysis.\n2. "
            "Check whether the same sender reached other users and block "
            "the domain.\n3. Confirm the reporting user did not submit "
            "credentials; force a reset if they did.\n\nKeywords: "
            "phishing, email, security, credentials.",
        ),
    ],
}


def _fill(template: str) -> str:
    return template.format(
        host=fake.hostname(),
        city=fake.city(),
        vendor=random.choice(["Cisco", "Netgear", "Dell", "Lenovo", "HP", "Ubiquiti"]),
        username=fake.user_name(),
        asset_tag=f"AST-{fake.unique.random_number(digits=5, fix_len=True)}",
        app=random.choice(["Slack", "VS Code", "Zoom", "Figma", "Docker Desktop", "Outlook"]),
    )


def generate_tickets(count: int) -> list[dict]:
    tickets = []
    now = datetime.now(UTC)
    for i in range(count):
        category = random.choice(CATEGORIES)
        title_tpl, desc_tpl = random.choice(TICKET_TEMPLATES[category])
        created_at = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        tickets.append(
            {
                "id": f"TKT-{i + 1:04d}",
                "title": _fill(title_tpl),
                "description": _fill(desc_tpl),
                "category": category,
                "priority": random.choice(PRIORITIES),
                "status": random.choice(TICKET_STATUSES),
                "created_at": created_at.isoformat(),
            }
        )
    return tickets


def generate_runbooks(out_dir: Path, count: int) -> None:
    if out_dir.exists():
        for stale in out_dir.glob("*.md"):
            stale.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    # Guarantee at least one runbook per category first, then fill the rest
    # from the full template pool at random.
    pool: list[tuple[str, str, str]] = []
    for category, templates in RUNBOOK_TEMPLATES.items():
        for title, body in templates:
            pool.append((category, title, body))

    random.shuffle(pool)
    selected = pool[:count] if count <= len(pool) else pool

    # Ensure every category appears at least once even if count < len(pool)
    # happened to drop one.
    covered = {c for c, _, _ in selected}
    missing = [c for c in CATEGORIES if c not in covered]
    for category in missing:
        selected.append(next(item for item in pool if item[0] == category))

    for i, (category, title, body) in enumerate(selected, start=1):
        frontmatter = f'---\ntitle: "{title}"\ncategories: ["{category}"]\n---\n\n'
        (out_dir / f"runbook-{i:03d}.md").write_text(frontmatter + body, encoding="utf-8")


def generate_incidents(count: int) -> list[dict]:
    incidents = []
    now = datetime.now(UTC)
    for i in range(count):
        category = random.choice(CATEGORIES)
        title_tpl, _ = random.choice(TICKET_TEMPLATES[category])
        occurred_at = now - timedelta(days=random.randint(30, 365))
        resolved_at = occurred_at + timedelta(hours=random.randint(1, 72))
        incidents.append(
            {
                "id": f"INC-{i + 1:04d}",
                "category": category,
                "title": _fill(title_tpl),
                "occurred_at": occurred_at.isoformat(),
                "resolved_at": resolved_at.isoformat(),
                "resolution_summary": fake.sentence(nb_words=12),
                "root_cause": fake.sentence(nb_words=10),
            }
        )
    return incidents


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ticket_count = random.randint(30, 50)
    tickets = generate_tickets(ticket_count)
    (OUTPUT_DIR / "tickets.json").write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    print(f"Wrote {len(tickets)} tickets to {OUTPUT_DIR / 'tickets.json'}")

    runbook_count = random.randint(10, 15)
    runbooks_dir = OUTPUT_DIR / "runbooks"
    generate_runbooks(runbooks_dir, runbook_count)
    print(f"Wrote {len(list(runbooks_dir.glob('*.md')))} runbooks to {runbooks_dir}")

    incident_count = random.randint(15, 20)
    incidents = generate_incidents(incident_count)
    (OUTPUT_DIR / "incidents.json").write_text(json.dumps(incidents, indent=2), encoding="utf-8")
    print(f"Wrote {len(incidents)} incidents to {OUTPUT_DIR / 'incidents.json'}")


if __name__ == "__main__":
    main()
