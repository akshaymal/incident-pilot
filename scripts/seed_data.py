#!/usr/bin/env python3
"""Generate the synthetic corpus that Week 1+ components depend on.

Writes tickets, runbooks, and past-incident fixtures to data/synthetic/
(gitignored, fully regeneratable). Pure Python + Faker -- no LLM call, so
this runs with no API key. Output is random each run (no fixed seed); tests
assert structure and counts, not exact content. See CLAUDE.md ground rule 3:
this script is the only source of ticket/runbook/incident data.

The corpus is deliberately noisy rather than uniform: real enterprise ticket
queues and knowledge bases have skewed category distributions, inconsistent
writer quality, multi-issue and ambiguous tickets, near-duplicate reports of
the same incident, and a knowledge base with uneven depth and some outdated
content. That variety is what makes classification/retrieval a meaningful
test later, instead of a rubber stamp.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from faker import Faker

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "synthetic"

CATEGORIES = ["network", "vpn_access", "hardware", "software", "security"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]

# Skewed like a real IT queue: software/network dominate, security is rare.
CATEGORY_WEIGHTS = {
    "software": 0.30,
    "network": 0.25,
    "hardware": 0.20,
    "vpn_access": 0.15,
    "security": 0.10,
}

fake = Faker()


def _weighted_category() -> str:
    return random.choices(
        list(CATEGORY_WEIGHTS.keys()), weights=list(CATEGORY_WEIGHTS.values()), k=1
    )[0]


def _fill(template: str) -> str:
    return template.format(
        host=fake.hostname(),
        city=fake.city(),
        vendor=random.choice(["Cisco", "Netgear", "Dell", "Lenovo", "HP", "Ubiquiti"]),
        username=fake.user_name(),
        asset_tag=f"AST-{fake.unique.random_number(digits=5, fix_len=True)}",
        app=random.choice(["Slack", "VS Code", "Zoom", "Figma", "Docker Desktop", "Outlook"]),
        floor=random.randint(1, 12),
        minutes=random.randint(5, 45),
    )


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

# Four scenarios per category (up from two), written with different framing
# and terminology on purpose -- one calls it "the VPN", another "remote
# access", so retrieval can't rely on exact vocabulary matching.
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
        (
            "Wi-Fi keeps dropping on floor {floor}",
            "Multiple people on floor {floor} say their wireless connection "
            "drops every {minutes} minutes or so, wired connections seem "
            "unaffected. Might be an access point issue.",
        ),
        (
            "Can't reach the internal wiki from {city} site",
            "Nobody at the {city} site can load the internal wiki or file "
            "shares this morning, but internet browsing works normally. "
            "Looks like it's isolated to that site's link.",
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
        (
            "Remote access tool disconnects every {minutes} minutes",
            "User {username} says the remote-access client boots them off "
            "roughly every {minutes} minutes while working from home, "
            "forcing a re-login each time.",
        ),
        (
            "New hire {username} has no VPN profile",
            "New hire {username} was never issued a VPN profile during "
            "onboarding and can't reach any internal tools from home.",
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
        (
            "Battery draining fast on {vendor} laptop",
            "User {username}'s {vendor} laptop (asset tag {asset_tag}) "
            "goes from full charge to under 20% in about two hours even "
            "when mostly idle.",
        ),
        (
            "Keyboard keys sticking on loaner machine",
            "User {username} says several keys on their loaner {vendor} "
            "machine (asset tag {asset_tag}) are sticking or double-typing, "
            "making it hard to work.",
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
        (
            "{app} won't save files to shared drive",
            "User {username} gets a permissions error whenever {app} tries "
            "to save to the shared drive, though the same folder works "
            "fine from File Explorer.",
        ),
        (
            "Need {app} installed for new project",
            "User {username} is starting a new project and needs {app} "
            "installed; not sure which internal request queue this goes "
            "through.",
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
        (
            "USB drive found in parking lot, plugged in by {username}",
            "User {username} found an unlabeled USB drive in the parking "
            "lot and plugged it into their workstation before thinking "
            "twice. Wants to know what to do now.",
        ),
        (
            "Repeated MFA push notifications for {username}",
            "User {username} is getting repeated MFA push notifications "
            "they didn't initiate, several times over the last hour.",
        ),
    ],
}

# A few tickets that legitimately straddle two categories -- the category
# field below is the "correct" ground-truth answer, but the text alone
# doesn't make it obvious, the way a real triage queue often isn't.
AMBIGUOUS_TEMPLATES = [
    (
        "network",
        "Can't reach anything, VPN or otherwise",
        "User {username} says nothing loads -- internal sites, the VPN "
        "client, even the status page. Not clear yet if this is their "
        "laptop, their network, or the VPN gateway.",
    ),
    (
        "hardware",
        "New laptop won't join the VPN",
        "User {username} just got a replacement {vendor} laptop (asset tag "
        "{asset_tag}) and the VPN client fails to connect. Could be a "
        "provisioning issue on the new machine or a VPN account problem.",
    ),
    (
        "software",
        "{app} won't launch, maybe a license or an update issue",
        "User {username} can't open {app} -- it either says the license "
        "is invalid or hangs on launch, inconsistent between attempts. "
        "Unclear if this is licensing or a bad update.",
    ),
    (
        "security",
        "Account locked after failed VPN logins",
        "User {username}'s account got locked after several failed VPN "
        "login attempts. Could be a forgotten password or a compromised "
        "credential attempt -- flagging for review either way.",
    ),
]

REWORD_PREFIXES = [
    "Following up on what sounds like the same issue -- ",
    "+1, seeing this too: ",
    "Another report of what might be the same thing: ",
    "Same problem here, different user: ",
    "",
]

RAMBLE_FILLERS = [
    " Not sure if it's related, but the printer on that floor has also been acting up lately.",
    " This has happened a couple of times before but usually goes away on its own after a while.",
    " Sorry for the long message, just want to give as much context as "
    "possible since it's been a frustrating week.",
    " Happy to hop on a call if that's faster than going back and forth over the ticket.",
]


def _inject_typo(text: str) -> str:
    words = text.split(" ")
    candidates = [i for i, w in enumerate(words) if len(w) > 4]
    if not candidates:
        return text
    idx = random.choice(candidates)
    word = words[idx]
    pos = random.randrange(1, len(word) - 1)
    words[idx] = word[:pos] + word[pos] + word[pos:]
    return " ".join(words)


def _apply_style(title: str, description: str) -> tuple[str, str]:
    """Vary writer quality: terse, rambling, urgent, or typo-laden."""
    style = random.choices(
        ["normal", "terse", "rambling", "urgent", "typo"],
        weights=[0.4, 0.2, 0.15, 0.15, 0.1],
        k=1,
    )[0]
    if style == "terse":
        description = description.split(". ")[0].rstrip(".") + "."
    elif style == "rambling":
        description = description + random.choice(RAMBLE_FILLERS)
    elif style == "urgent":
        title = "URGENT: " + title
        description = description + " Need this resolved ASAP, blocking work."
    elif style == "typo":
        description = _inject_typo(description)
    return title, description


def _make_ticket(ticket_id: str, category: str, created_at: datetime) -> dict:
    title_tpl, desc_tpl = random.choice(TICKET_TEMPLATES[category])
    title, description = _fill(title_tpl), _fill(desc_tpl)
    title, description = _apply_style(title, description)

    # ~12% chance of a second, unrelated problem mentioned in the same
    # ticket -- category stays the first (primary) issue.
    if random.random() < 0.12:
        other_category = random.choice([c for c in CATEGORIES if c != category])
        _, other_desc_tpl = random.choice(TICKET_TEMPLATES[other_category])
        description += " Also, separately: " + _fill(other_desc_tpl)

    return {
        "id": ticket_id,
        "title": title,
        "description": description,
        "category": category,
        "priority": random.choice(PRIORITIES),
        "status": random.choice(TICKET_STATUSES),
        "created_at": created_at.isoformat(),
    }


def generate_tickets(count: int) -> list[dict]:
    now = datetime.now(UTC)
    tickets: list[dict] = []
    next_id = 1

    ambiguous_count = max(1, round(count * 0.08))
    duplicate_count = max(1, round(count * 0.10))
    base_count = count - ambiguous_count - duplicate_count

    for _ in range(base_count):
        category = _weighted_category()
        created_at = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        tickets.append(_make_ticket(f"TKT-{next_id:04d}", category, created_at))
        next_id += 1

    for _ in range(ambiguous_count):
        category, title_tpl, desc_tpl = random.choice(AMBIGUOUS_TEMPLATES)
        title, description = _fill(title_tpl), _fill(desc_tpl)
        created_at = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        tickets.append(
            {
                "id": f"TKT-{next_id:04d}",
                "title": title,
                "description": description,
                "category": category,
                "priority": random.choice(PRIORITIES),
                "status": random.choice(TICKET_STATUSES),
                "created_at": created_at.isoformat(),
            }
        )
        next_id += 1

    # Near-duplicates: a second person reporting what reads like the same
    # underlying incident, close in time, lightly reworded -- implicit only,
    # no linking field, the way an untriaged real queue looks.
    for _ in range(duplicate_count):
        original = random.choice(tickets)
        original_created = datetime.fromisoformat(original["created_at"])
        dup_created = original_created + timedelta(
            hours=random.randint(0, 6), minutes=random.randint(0, 59)
        )
        tickets.append(
            {
                "id": f"TKT-{next_id:04d}",
                "title": original["title"],
                "description": random.choice(REWORD_PREFIXES) + original["description"],
                "category": original["category"],
                "priority": random.choice(PRIORITIES),
                "status": random.choice(TICKET_STATUSES),
                "created_at": dup_created.isoformat(),
            }
        )
        next_id += 1

    random.shuffle(tickets)

    # Guarantee at least 2 tickets per category regardless of how the
    # weighted draws landed -- keeps category coverage deterministic-safe
    # rather than merely likely. Converts tickets from the most-represented
    # category in place rather than appending, so the total count stays
    # exactly `count`.
    counts = Counter(t["category"] for t in tickets)
    for category in CATEGORIES:
        while counts[category] < 2:
            donor_category = max(counts, key=lambda c: counts[c])
            donor_idx = next(i for i, t in enumerate(tickets) if t["category"] == donor_category)
            created_at = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
            tickets[donor_idx] = _make_ticket(tickets[donor_idx]["id"], category, created_at)
            counts[donor_category] -= 1
            counts[category] += 1

    return tickets


# ---------------------------------------------------------------------------
# Runbooks
# ---------------------------------------------------------------------------

# Each entry: (categories, status, title, body). "guaranteed" entries are
# always included so category/status/multi-category minimums hold no matter
# what the random target count comes out to; "filler" entries are sampled in
# on top, up to the target, purely for extra variety between runs.
RUNBOOK_GUARANTEED: list[tuple[list[str], str, str, str]] = [
    (
        ["network"],
        "current",
        "Diagnosing Intermittent Network Connectivity",
        "## Symptoms\n\nUsers report dropped connections or high latency "
        "reaching internal services.\n\n## Steps\n\n1. Check switch port "
        "counters for errors or packet loss.\n2. Verify DNS resolution for "
        "internal hostnames using `dig` or `nslookup`.\n3. Escalate to "
        "network engineering if packet loss is confirmed at the switch "
        "level.\n\nKeywords: connectivity, packet loss, dns, switch, "
        "latency.",
    ),
    (
        ["network"],
        "current",
        "Resolving Internal DNS Resolution Failures",
        "## Symptoms\n\nHosts cannot resolve internal (*.internal) domain "
        "names while external DNS works normally.\n\n## Steps\n\n1. "
        "Confirm the host's configured resolver matches the internal DNS "
        "server.\n2. Flush the local DNS cache.\n3. Check the internal DNS "
        "server logs for stale or missing records.\n\nKeywords: dns, "
        "resolver, internal domain, cache.",
    ),
    (
        ["network"],
        "current",
        "Isolating Wi-Fi Drops on a Single Floor",
        "## Symptoms\n\nMultiple users on one floor report periodic "
        "wireless disconnects while wired connections stay stable.\n\n"
        "## Steps\n\n1. Check access point logs for that floor for "
        "repeated de-auth events.\n2. Compare client counts against the "
        "AP's rated capacity -- overcrowding is a common cause.\n3. Have "
        "affected users switch to the 5GHz band as a mitigation while "
        "investigating.\n4. If the AP is over capacity, file a request "
        "for an additional access point on that floor.\n\nKeywords: "
        "wifi, wireless, access point, drops, floor.",
    ),
    (
        ["vpn_access"],
        "current",
        "Troubleshooting VPN Authentication Timeouts",
        "## Symptoms\n\nVPN client hangs or times out during "
        "authentication, especially from office networks.\n\n## Steps\n\n"
        "1. Confirm the VPN gateway is reachable from the user's network "
        "(check for port 443/1194 blocks).\n2. Verify the user's account "
        "is not locked in the identity provider.\n3. Have the user retry "
        "from a different network to isolate firewall issues.\n\n"
        "Keywords: vpn, authentication, timeout, gateway, mfa.",
    ),
    (
        ["vpn_access"],
        "current",
        "Restoring VPN Access After Password Reset",
        "## Symptoms\n\nVPN client rejects credentials with an MFA error "
        "immediately after an SSO password reset.\n\n## Steps\n\n1. "
        "Confirm the SSO password reset propagated to the VPN identity "
        "provider (can take up to 15 minutes).\n2. Ask the user to "
        "re-register their MFA device if propagation is confirmed "
        "complete.\n3. Manually sync the account if delay exceeds 30 "
        "minutes.\n\nKeywords: vpn, password reset, mfa, sso, access.",
    ),
    (
        ["vpn_access"],
        "current",
        "Provisioning VPN Access for New Hires",
        "## Symptoms\n\nA new hire has no VPN profile and cannot reach "
        "internal tools remotely.\n\n## Steps\n\n1. Confirm the new hire's "
        "account exists in the identity provider and is active.\n2. "
        "Issue a VPN profile through the access-provisioning tool, "
        "scoped to their team's default policy.\n3. Have the new hire "
        "install the VPN client and confirm connectivity before their "
        "first remote day.\n\nKeywords: vpn, new hire, onboarding, "
        "provisioning, profile.",
    ),
    (
        ["hardware"],
        "current",
        "Diagnosing a Laptop That Won't Power On",
        "## Symptoms\n\nNo display, no fan activity, often following a "
        "firmware or BIOS update.\n\n## Steps\n\n1. Confirm the charger "
        "and outlet both work with a known-good device.\n2. Attempt a "
        "hard reset (hold power button 15+ seconds).\n3. If unresponsive, "
        "escalate for board-level firmware recovery.\n\nKeywords: laptop, "
        "power, firmware, bios, hardware.",
    ),
    (
        ["hardware"],
        "current",
        "Fixing External Monitor Detection on Docking Stations",
        "## Symptoms\n\nDocking station is powered but connected external "
        "monitors are not detected.\n\n## Steps\n\n1. Update the docking "
        "station firmware/drivers.\n2. Test each monitor port "
        "individually to isolate a faulty port.\n3. Reseat the dock "
        "connection and reboot.\n\nKeywords: docking station, monitor, "
        "display, hardware, drivers.",
    ),
    (
        ["hardware"],
        "current",
        "Investigating Rapid Battery Drain",
        "## Symptoms\n\nA laptop drains from full charge to under 20% in "
        "a couple of hours, even mostly idle.\n\n## Steps\n\n1. Check "
        "for a runaway background process in the OS task manager.\n2. "
        "Run the vendor's battery diagnostic utility to check for a "
        "hardware degradation flag.\n3. If the battery reports healthy "
        "but drain persists, check for a misbehaving peripheral draining "
        "power over USB.\n4. Escalate for battery replacement if "
        "diagnostics confirm degradation below 60% design capacity.\n\n"
        "Keywords: battery, drain, laptop, power, diagnostics.",
    ),
    (
        ["software"],
        "current",
        "Resolving Application Crashes on Launch",
        "## Symptoms\n\nAn application crashes immediately after launch, "
        "often following an update.\n\n## Steps\n\n1. Check the "
        "application's crash log for missing dependencies.\n2. Reinstall "
        "the application's runtime dependencies.\n3. Roll back to the "
        "previous version if the issue persists.\n\nKeywords: "
        "application, crash, launch, dependency, update.",
    ),
    (
        ["software"],
        "current",
        "Fixing License Activation Errors",
        "## Symptoms\n\nAn application fails to activate its license, "
        "returning a generic error code.\n\n## Steps\n\n1. Confirm the "
        "license server is reachable from the user's network.\n2. Check "
        "the license pool for available seats.\n3. Re-issue the license "
        "key if the pool has capacity.\n\nKeywords: license, activation, "
        "software, license server.",
    ),
    (
        ["software"],
        "current",
        "Fixing Shared-Drive Save Permissions",
        "## Symptoms\n\nAn application gets a permissions error saving to "
        "a shared drive that other tools (like File Explorer) can write "
        "to fine.\n\n## Steps\n\n1. Confirm the application is using the "
        "same mapped drive letter/path as File Explorer, not a cached "
        "UNC path.\n2. Check whether the application runs with different "
        "effective permissions (e.g. as administrator).\n3. Clear the "
        "application's cached credentials for the share and reconnect.\n"
        "\nKeywords: shared drive, permissions, save, application.",
    ),
    (
        ["security"],
        "current",
        "Responding to Suspicious Login Attempts",
        "## Symptoms\n\nSIEM flags a login attempt from an unrecognized "
        "location or outside business hours.\n\n## Steps\n\n1. Confirm "
        "the account is locked pending review.\n2. Contact the user "
        "through a verified channel to confirm activity.\n3. Force a "
        "password reset and MFA re-enrollment if the login is not "
        "confirmed legitimate.\n\nKeywords: suspicious login, siem, "
        "account lock, security.",
    ),
    (
        ["security"],
        "current",
        "Handling Reported Phishing Emails",
        "## Symptoms\n\nA user reports an email impersonating IT support "
        "or another trusted sender.\n\n## Steps\n\n1. Preserve the "
        "original email with headers for analysis.\n2. Check whether the "
        "same sender reached other users and block the domain.\n3. "
        "Confirm the reporting user did not submit credentials; force a "
        "reset if they did.\n\nKeywords: phishing, email, security, "
        "credentials.",
    ),
    (
        ["security"],
        "current",
        "Handling Found or Unknown USB Media",
        "## Symptoms\n\nA user plugged in an unlabeled or found USB "
        "drive, or found one and wants guidance before plugging it in.\n\n"
        "## Steps\n\n1. If already plugged in, disconnect the network "
        "and run a full malware scan before doing anything else.\n2. "
        "Preserve the device for security review rather than reusing "
        "or discarding it.\n3. Remind the user (without blaming them) "
        "that unknown media should never be plugged into a work "
        "machine.\n\nKeywords: usb, malware, security, unknown device.",
    ),
    (
        ["network"],
        "outdated",
        "Resetting the Legacy VPN Concentrator (Deprecated Hardware)",
        "## Symptoms\n\nConnectivity issues attributed to the old "
        "hardware VPN concentrator.\n\n## Steps\n\n1. Power-cycle the "
        "concentrator via the rack PDU.\n\n**Note: this hardware was "
        "decommissioned when the network moved to the cloud gateway. "
        "Kept here for historical reference only -- do not action.**\n\n"
        "Keywords: concentrator, legacy, deprecated.",
    ),
    (
        ["hardware", "vpn_access"],
        "current",
        "Diagnosing VPN Failures on Newly Provisioned Laptops",
        "## Symptoms\n\nA freshly imaged or replacement laptop fails to "
        "connect to the VPN, where the same user's old laptop worked "
        "fine.\n\n## Steps\n\n1. Confirm the new device's VPN client "
        "certificate was issued as part of imaging -- a missed step in "
        "provisioning is the most common cause.\n2. Check the device is "
        "enrolled in the MDM/device-trust system the VPN gateway checks "
        "against.\n3. If the certificate is missing, re-run the imaging "
        "profile's VPN enrollment step rather than debugging the client "
        "itself.\n\nKeywords: vpn, laptop, provisioning, certificate, "
        "new device.",
    ),
]

# Extra filler entries sampled in on top of the guaranteed set, purely to
# vary the exact runbook count and content between runs.
RUNBOOK_FILLER: list[tuple[list[str], str, str, str]] = [
    (
        ["network"],
        "current",
        "Restoring Site Connectivity After a WAN Link Drop",
        "## Symptoms\n\nAn entire site loses access to internal tools "
        "and file shares while general internet access still works.\n\n"
        "## Steps\n\n1. Check the WAN circuit status with the ISP/SD-WAN "
        "provider for that site.\n2. Confirm whether a backup/failover "
        "link exists and whether it activated.\n3. If no failover "
        "exists, escalate to network engineering with the circuit ID "
        "and estimate an ETA for the user-facing status page.\n\n"
        "Keywords: wan, site outage, failover, sd-wan, connectivity.",
    ),
    (
        ["vpn_access"],
        "outdated",
        "Manually Editing the Old VPN Config File (Deprecated Client)",
        "## Symptoms\n\nApplies to the VPN client version retired last "
        "year.\n\n## Steps\n\n1. Locate `vpn.conf` and edit the gateway "
        "IP by hand.\n\n**Note: the current client no longer uses a "
        "local config file -- this only applies to installs that were "
        "never upgraded. Verify client version before following this.**"
        "\n\nKeywords: vpn, config file, legacy client.",
    ),
    (
        ["vpn_access", "security"],
        "current",
        "Handling Repeated Unsolicited MFA Prompts",
        "## Symptoms\n\nA user reports repeated MFA push notifications "
        "they did not initiate.\n\n## Steps\n\n1. Instruct the user to "
        "deny all prompts and not approve anything they didn't request.\n"
        "2. Force a password reset immediately -- unsolicited MFA "
        "prompts usually mean the password is already compromised.\n3. "
        "Review recent sign-in logs for the account for any successful "
        "logins from unfamiliar locations.\n4. Re-issue MFA enrollment "
        "once the password reset is confirmed.\n\nKeywords: mfa, push "
        "notification, security, vpn, compromised credential.",
    ),
    (
        ["hardware"],
        "outdated",
        "Replacing CMOS Batteries on Retired Desktop Model",
        "## Symptoms\n\nBIOS clock resets on the old tower desktops.\n\n"
        "## Steps\n\n1. Open the case and replace the CR2032 battery.\n\n"
        "**Note: this desktop model was retired two refresh cycles ago. "
        "Current fleet is laptop-only; keep for reference if a legacy "
        "unit surfaces.**\n\nKeywords: cmos, battery, desktop, legacy.",
    ),
    (
        ["hardware"],
        "current",
        "Fixing Sticking or Double-Typing Keys",
        "## Symptoms\n\nOne or more keys stick, repeat, or double-type "
        "on a laptop keyboard.\n\n## Steps\n\n1. Rule out a software "
        "cause first -- check for a stuck accessibility/sticky-keys "
        "setting.\n2. Clean under the affected keys with compressed air.\n"
        "3. If the issue persists after cleaning, especially on a "
        "specific key cluster, file a hardware repair request rather "
        "than continuing to troubleshoot in place.\n\nKeywords: "
        "keyboard, sticking keys, laptop, hardware.",
    ),
    (
        ["software"],
        "current",
        "Triaging New Software Install Requests",
        "## Symptoms\n\nA user requests a new application be installed "
        "for a project.\n\n## Steps\n\n1. Check whether the application "
        "is already on the approved software list.\n2. If approved, "
        "push via the standard software deployment tool.\n3. If not on "
        "the list, route to security/procurement for review before "
        "installing.\n\nKeywords: install request, new software, "
        "approved list, procurement.",
    ),
    (
        ["software"],
        "outdated",
        "Reinstalling the Old Ticketing Client Plugin (Deprecated)",
        "## Symptoms\n\nErrors referencing the legacy desktop ticketing "
        "plugin.\n\n## Steps\n\n1. Reinstall the plugin from the old "
        "internal file share.\n\n**Note: this plugin was replaced by the "
        "web ticketing portal; the file share it references may no "
        "longer exist. Confirm the user isn't just looking for the new "
        "portal before following this.**\n\nKeywords: plugin, ticketing, "
        "legacy, deprecated.",
    ),
    (
        ["security"],
        "current",
        "Escalating Confirmed Phishing Campaigns",
        "## Symptoms\n\nMultiple users report near-identical phishing "
        "emails within a short window.\n\n## Steps\n\n1. Confirm the "
        "reports share the same sender/subject pattern.\n2. Block the "
        "sending domain at the mail gateway.\n3. Send an organization-"
        "wide alert describing the pattern so users can self-identify "
        "if they clicked.\n4. Force a password reset for anyone who "
        "reports having entered credentials.\n\nKeywords: phishing, "
        "campaign, escalation, mail gateway.",
    ),
    (
        ["security", "software"],
        "current",
        "Reviewing Software Requests That Touch Sensitive Data",
        "## Symptoms\n\nA requested application needs access to "
        "customer or financial data.\n\n## Steps\n\n1. Confirm the "
        "application has completed a security review before granting "
        "data access.\n2. Scope access to the minimum data set the "
        "requester actually needs.\n3. Log the approval decision for "
        "audit purposes.\n\nKeywords: security review, data access, "
        "software request, approval.",
    ),
    (
        ["network", "hardware"],
        "current",
        "Diagnosing Switch Port Flapping Affecting One Desk",
        "## Symptoms\n\nA single desk or small cluster of desks loses "
        "connectivity repeatedly while the rest of the floor is fine.\n\n"
        "## Steps\n\n1. Check the switch port's error/flap counters for "
        "that specific port.\n2. Swap the patch cable before assuming a "
        "switch hardware fault.\n3. If flapping continues on a known-"
        "good cable, move the port assignment and flag the original "
        "port for hardware inspection.\n\nKeywords: switch, port "
        "flapping, cable, desk, connectivity.",
    ),
    (
        ["vpn_access"],
        "current",
        "Diagnosing Repeated Remote-Access Disconnects",
        "## Symptoms\n\nA remote user's VPN session drops on a "
        "consistent interval (e.g. every 20-30 minutes) rather than "
        "randomly.\n\n## Steps\n\n1. Check for an idle-timeout or "
        "session-length policy on the VPN gateway matching the "
        "interval.\n2. Rule out a home-network issue by having the user "
        "test from a different network.\n3. If the interval matches a "
        "known gateway policy, this may be expected behavior -- confirm "
        "with the user before treating as a bug.\n\nKeywords: vpn, "
        "disconnect, session timeout, remote access.",
    ),
]


def generate_runbooks(out_dir: Path, target_count: int) -> None:
    if out_dir.exists():
        for stale in out_dir.glob("*.md"):
            stale.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = list(RUNBOOK_GUARANTEED)
    filler = list(RUNBOOK_FILLER)
    random.shuffle(filler)
    needed = max(0, target_count - len(selected))
    selected.extend(filler[:needed])
    random.shuffle(selected)

    for i, (categories, status, title, body) in enumerate(selected, start=1):
        categories_yaml = ", ".join(f'"{c}"' for c in categories)
        frontmatter = (
            f'---\ntitle: "{title}"\ncategories: [{categories_yaml}]\nstatus: "{status}"\n---\n\n'
        )
        (out_dir / f"runbook-{i:03d}.md").write_text(frontmatter + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


def _make_incident(incident_id: str, category: str, now: datetime) -> dict:
    title_tpl, _ = random.choice(TICKET_TEMPLATES[category])
    occurred_at = now - timedelta(days=random.randint(30, 365))
    resolved_at = occurred_at + timedelta(hours=random.randint(1, 72))

    # Vary depth: some incidents get a one-line summary, others a
    # multi-sentence writeup with more root-cause detail.
    if random.random() < 0.4:
        resolution_summary = fake.sentence(nb_words=8)
        root_cause = fake.sentence(nb_words=6)
    else:
        resolution_summary = " ".join(fake.sentences(nb=random.randint(2, 3)))
        root_cause = " ".join(fake.sentences(nb=random.randint(2, 3)))

    return {
        "id": incident_id,
        "category": category,
        "title": _fill(title_tpl),
        "occurred_at": occurred_at.isoformat(),
        "resolved_at": resolved_at.isoformat(),
        "resolution_summary": resolution_summary,
        "root_cause": root_cause,
    }


def generate_incidents(count: int) -> list[dict]:
    now = datetime.now(UTC)
    incidents = [
        _make_incident(f"INC-{i + 1:04d}", _weighted_category(), now) for i in range(count)
    ]

    # Guarantee every category appears at least once, converting an incident
    # from the most-represented category in place rather than appending, so
    # the total count stays exactly `count`.
    counts = Counter(inc["category"] for inc in incidents)
    for category in CATEGORIES:
        if counts[category] >= 1:
            continue
        donor_category = max(counts, key=lambda c: counts[c])
        donor_idx = next(i for i, inc in enumerate(incidents) if inc["category"] == donor_category)
        incidents[donor_idx] = _make_incident(incidents[donor_idx]["id"], category, now)
        counts[donor_category] -= 1
        counts[category] += 1

    return incidents


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ticket_count = random.randint(60, 100)
    tickets = generate_tickets(ticket_count)
    (OUTPUT_DIR / "tickets.json").write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    print(f"Wrote {len(tickets)} tickets to {OUTPUT_DIR / 'tickets.json'}")

    runbook_count = random.randint(20, 30)
    runbooks_dir = OUTPUT_DIR / "runbooks"
    generate_runbooks(runbooks_dir, runbook_count)
    print(f"Wrote {len(list(runbooks_dir.glob('*.md')))} runbooks to {runbooks_dir}")

    incident_count = random.randint(15, 20)
    incidents = generate_incidents(incident_count)
    (OUTPUT_DIR / "incidents.json").write_text(json.dumps(incidents, indent=2), encoding="utf-8")
    print(f"Wrote {len(incidents)} incidents to {OUTPUT_DIR / 'incidents.json'}")


if __name__ == "__main__":
    main()
