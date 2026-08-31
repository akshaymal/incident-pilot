# Workflow: Issue-Driven Development

This document is the full reference for how work moves from idea to shipped code on `incident-pilot`. `CLAUDE.md` has the summary; this is the detail, meant to make sense to a session with zero memory of how this was set up.

## One-time repo setup (do these once, in order)

1. Install and authenticate `gh`: `gh auth login`.
2. Create labels: `bash scripts/setup-labels.sh`.
3. Enable branch protection on `main` (requires repo admin). `gh api --field` does not accept nested JSON objects (it treats each value as a literal string, which the API then rejects) — write a payload file and use `--input` instead:
   ```bash
   cat <<'JSON' > /tmp/branch-protection.json
   {
     "required_status_checks": { "strict": true, "contexts": ["verify"] },
     "enforce_admins": true,
     "required_pull_request_reviews": { "required_approving_review_count": 0 },
     "restrictions": null
   }
   JSON
   gh api repos/:owner/:repo/branches/main/protection --method PUT --input /tmp/branch-protection.json
   ```
   `required_approving_review_count` is `0`, not `1`, because this is a solo-maintained repo — GitHub doesn't let a PR author approve their own PR, so a count of `1` combined with `enforce_admins: true` would lock you out of merging your own PRs. The real guardrails here are "no direct pushes to `main`" (this setting) and "CI must pass" (the `required_status_checks` above) — the human-in-the-loop step is you reviewing the diff before clicking merge, not a separate GitHub approval. If this repo ever gets a second maintainer, raise this back to `1`.
4. Local git hook: `git config core.hooksPath scripts/git-hooks`.

## Label taxonomy (fixed — do not add ad-hoc labels)

| Family | Values | Meaning |
|---|---|---|
| Type | `type:feature`, `type:chore`, `type:bug` | What kind of change |
| Priority | `priority:p1`, `priority:p2`, `priority:p3` | Urgency |
| Area | `area:agent`, `area:mcp`, `area:memory`, `area:sandbox`, `area:observability`, `area:audit`, `area:ui`, `area:infra`, `area:docs` | Which layer of the stack it touches — matches the `src/incident_pilot/` layout in `CLAUDE.md` |
| Status | `agent-ready` | Only applied once acceptance criteria/DoD are unambiguous and non-overlapping with other open issues |

Every issue gets exactly one Type, one Priority, one Area label.

## Lifecycle

1. **File the issue** using the `task.yml` form (`.github/ISSUE_TEMPLATE/task.yml`), at any level of roughness.
2. **Refine it**: run the `issue-refiner` skill against the issue number. It always grills for the outcome first — what you're trying to accomplish, and (for this project specifically) which layer of the agent stack it's meant to exercise — before entertaining any implementation, then walks you through recommended implementation options (including your own idea, if you had one) so you can make an informed choice, weighed against this project's ground rules in `CLAUDE.md` (real MCP calls, self-hosted services, synthetic data, audit-mindedness). It interviews you until Type/Priority/Area/acceptance criteria/DoD are all concrete, checks for overlap with other open issues, and applies `agent-ready`.
3. **Work it**: say "work on issue #N". The `work-issue` skill:
   - Verifies `agent-ready` is set (refuses to proceed otherwise).
   - Branches as `issue-<N>-<short-slug>` off up-to-date `main`.
   - Implements against the acceptance criteria, following `CLAUDE.md`'s ground rules.
   - Self-verifies: the synthetic-data guard and MCP-boundary check (always), then `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest` (a no-op until the Week 1 Python scaffold exists — see "Pre-scaffold state" below).
   - Dispatches a **fresh, context-free subagent** to run the `code-review` skill against the diff — independent scrutiny with no exposure to the implementation reasoning, and explicitly asked to flag ground-rule violations (a hardcoded MCP import, non-synthetic data, a managed service swapped in for a self-hosted one) alongside ordinary correctness bugs.
   - Checks docs/artifacts (`README.md`, this file, the current week's checkpoint spec) against what the change actually touches: updates anything now stale, checks off completed spec items, or writes a new doc if the change introduces something that doesn't fit an existing doc's purpose. No-op if nothing changed that any doc describes.
   - Opens a PR: `Closes #N`, acceptance criteria restated as a checklist, verification checklist included.
4. **CI runs** (`.github/workflows/ci.yml`): the synthetic-data guard and MCP-boundary check (always), then ruff lint, ruff format check, and pytest (once the Python scaffold exists — see below). All blocking.
5. **You review and merge.** No autonomous merges, ever — branch protection enforces this at the repo level, not just by convention.

## Ground-rule guard scripts

Two rules from `CLAUDE.md` are easy to violate by accident and hard to catch in a normal review, so they're enforced mechanically instead of relying on memory:

- **`scripts/check_mcp_boundary.py`** — fails if anything under `src/incident_pilot/agents/` imports `incident_pilot.mcp_servers` directly instead of calling it as a real MCP tool. Enforces the MCP-over-hardcoded-calls rule (stated in `CLAUDE.md`'s intro and restated under "What NOT to do": "don't collapse the MCP server layer into a plain function call").
- **`scripts/check_synthetic_data.py`** — fails on hardcoded ticket/runbook/incident-shaped dict literals outside `scripts/seed_data.py`, or real-looking email domains/SSN patterns anywhere in the tree. Enforces Ground rule 2 ("all data is synthetic and must stay that way") and the "don't invent ticket/incident data inline in code" rule under "What NOT to do".

Both are pure-stdlib Python — they run in CI and the pre-commit hook unconditionally, even before `pyproject.toml` exists, unlike the ruff/pytest steps. Both are heuristics, not proofs: they can false-positive on legitimate code that happens to match the pattern (e.g. a docstring mentioning `ticket_id`). A failure means "look closer," not necessarily "this is wrong" — if it's a false positive, say so in the PR rather than restructuring the code just to dodge the pattern. If the pattern itself is too broad, fix the pattern in the script rather than working around it silently.

## Checkpoint scope is guidance, not a hard gate

`docs/checkpoints/week-NN-*.md` files define what each week is *for*, but the week boundaries are not a strict gate the way branch protection or CI are. If Week 1's scope is fully wrapped up — every task checked, definition of done met — there's no reason to wait for a calendar week to turn over before starting Week 2's work. Conversely, don't let "it's technically still Week 1" stop you from pulling in a later week's item if it's genuinely ready and useful.

What matters is that scope changes are **visible, not silent**: the `issue-refiner` skill flags when an issue reaches past the current week's stated scope so it's a deliberate choice, and `work-issue` calls it out in the PR description rather than burying it in the diff. The one thing to actually avoid is the failure mode the checkpoints doc itself warns about — building something "while you're in there" that was never scoped as its own issue at all.

## Pre-scaffold state

As of this writing, `incident-pilot` has no `pyproject.toml` yet — Week 1's "repo scaffolding" task (`uv init`, core dependencies, `src/incident_pilot/` layout) hasn't landed. Both the CI `verify` job and the local pre-commit hook detect this and no-op with a message instead of failing, so the harness itself can be merged before any application code exists. Once the Week 1 scaffold lands (with `pyproject.toml` at the repo root), both activate automatically — no further harness changes needed.

## Spec-scoped work (not yet an issue)

Some work belongs to a checkpoint spec that hasn't been written yet, or research that hasn't turned into a concrete task — e.g. anything past the current week's scope preview in `docs/checkpoints/README.md` that doesn't have a full `week-NN-*.md` spec yet. Work of that kind does **not** get filed as a GitHub issue via `task.yml`/`issue-refiner`, since filing it implies it's actionable now. Log it instead in the relevant week's scope-preview section of `docs/checkpoints/README.md`, or in `docs/research/` if it's still at the research stage.

Once a week's full spec is written (per the "Conventions for spec files" in `docs/checkpoints/README.md`), break it into real GitHub issues through the normal `issue-refiner` path — one issue per concrete, scoped task from that spec's task list.

## Backlog

No issues filed yet — this harness setup is the first PR against the repo.
