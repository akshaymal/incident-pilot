# CLAUDE.md -- project brief for Claude Code

This file gives Claude Code the standing context it needs to work on `incident-pilot` without re-explaining the project each session.

**What to read, by task -- this file is always loaded; the rest are read on demand, not by default:**

- **Scoped issue work** (`work-issue` on an `agent-ready` issue): read only the current week's `docs/checkpoints/week-NN-*.md` for the acceptance-criteria context. The issue body already carries the outcome and implementation decision from `issue-refiner` -- you don't need `motivation.md`/`architecture.md` to execute against a checklist that's already been made unambiguous.
- **Refining a rough issue, or any design/scope decision** (`issue-refiner`, choosing between implementation options, deciding whether something belongs in this project at all): read `docs/motivation.md` first, then `docs/architecture.md` -- the trade-offs in Ground rules and Tech stack below only make sense against the reasoning in those two docs.
- **New contributor / first session on this repo, or asked to explain the project**: read `docs/motivation.md`, then `docs/architecture.md`, in that order -- this is the one case where both are worth reading up front.
- **Pure bugfix, typo, refactor, or anything that doesn't change scope or design**: skip all of the above; this file plus the relevant source is enough.
- `docs/checkpoints/README.md` -- read only when checking whether an issue overlaps another week's scope, or during `issue-refiner`'s scope check. Not needed for routine implementation once an issue is already `agent-ready`.

When in doubt about whether a doc is needed, prefer not reading it and asking the user if something's unclear, over reading it defensively "just in case."

## What this project is

An AI IT-ops/incident triage copilot, built to give the maintainer (a software engineer) hands-on experience with the modern GenAI agent stack: LangGraph orchestration, MCP tool servers, temporal memory (Graphiti), sandboxed execution (E2B), human-in-the-loop UI (AG-UI/CopilotKit), observability (Langfuse), and audit logging. See `docs/motivation.md` for the full reasoning.

**This is a learning project first, a product second.** When there's a choice between the fastest way to make it work and the way that teaches the underlying concept, prefer the latter and say so explicitly.

## Ground rules

1. **Real MCP tool calls, never hardcoded imports.** Runbooks and ticket data are served via custom MCP servers under `src/incident_pilot/mcp_servers/`. Code under `src/incident_pilot/agents/` must call them as MCP tools, not import the server module directly -- even though that's simpler, exposing them over MCP is the actual learning goal. Enforced mechanically by `scripts/check_mcp_boundary.py`.
2. **Checkpoint scope is guidance, not a hard gate.** `docs/checkpoints/week-NN-*.md` files define what each week is *for*. It's fine to start next week's work early once the current week's definition of done is fully met, or to pull a later week's item forward when it's genuinely ready. What isn't fine is scope drift that isn't visible -- see `docs/WORKFLOW.md`.
3. **All data is synthetic and must stay that way.** Never introduce real personal, company, or scraped data. `scripts/seed_data.py` is the only source of ticket/runbook/incident data -- never invent it inline in code. Enforced (heuristically) by `scripts/check_synthetic_data.py`.
4. **Everything must be runnable by a stranger.** No hardcoded paths, no dependency on the maintainer's personal accounts or cloud subscriptions. `docker compose up` + `uv sync` + `.env` should be the entire setup story. If a task requires a paid API (E2B, an LLM provider), document the free-tier path.
5. **Audit-mindedness from day one.** Even in Week 1, before there's a formal audit-log table, log agent decisions (classification, tool calls, reasoning) somewhere inspectable -- this habit is the point of the whole project, not a Week 4 add-on.
6. **When a task is ambiguous, prefer the choice that's more educational to implement**, and note the alternative briefly in a comment or the PR description.

Rules 1 and 3 are checked mechanically in CI and the pre-commit hook. See `docs/WORKFLOW.md`'s "Ground-rule guard scripts" section for exactly what they check and their limits -- they're heuristics, not proof of compliance; the rules still apply in full even where a script can't catch a violation.

## Tech stack & conventions

- **Language:** Python 3.12+, managed with `uv` (not pip/poetry -- keep `uv.lock` committed)
- **Orchestration:** LangGraph -- model the flow as an explicit graph with named nodes, not an implicit chain of function calls
- **Tool protocol:** Official MCP Python SDK (see Ground rule 1)
- **Memory (from Week 2):** Graphiti, self-hosted against Neo4j Community (via Docker Compose) -- not Zep Cloud, so the project stays fully self-hostable
- **Sandbox (from Week 3):** E2B SDK for any code execution the agent proposes -- never `subprocess`/`exec` on the host
- **UI (from Week 3):** Next.js + CopilotKit (implements AG-UI) under a `web/` directory, talking to the Python backend over its API
- **Observability:** Langfuse, self-hosted via Docker Compose; instrument every LangGraph node
- **Audit log:** Postgres, a dedicated `audit_events` table -- deliberately separate from Langfuse traces, since traces are for debugging and the audit log is for governance/compliance and should be queryable independent of the observability stack
- **Testing:** `pytest`, tests live under `tests/`, mirroring the `src/incident_pilot/` structure
- **Linting/formatting:** `ruff` (both lint and format)
- **Repo layout:**
  ```
  src/incident_pilot/
    agents/          # LangGraph graph definitions and nodes
    mcp_servers/      # Runbook + ticket-data MCP servers
    memory/           # Graphiti integration (Week 2+)
    sandbox/          # E2B integration (Week 3+)
    observability/    # Langfuse instrumentation
    audit/            # Audit log writer
  data/synthetic/      # Generated fixtures (tickets, runbooks, incidents) -- gitignored, regenerated by seed script
  scripts/seed_data.py # Synthetic data generator
  web/                 # Next.js + CopilotKit frontend (Week 3+)
  docs/checkpoints/    # Weekly specs -- the source of truth for scope
  ```

## Commands

Not yet runnable -- Week 1's repo-scaffolding task (`uv init`, `pyproject.toml`) hasn't landed. Once it has, these are the commands to use:

- `docker compose up -d` -- start Postgres/Neo4j/Langfuse
- `uv sync` -- install dependencies
- `uv run python scripts/seed_data.py` -- generate synthetic tickets/runbooks/incidents
- `uv run python -m incident_pilot.run --ticket-id <id>` -- run one ticket through the agent
- `uv run pytest` -- run tests
- `uv run ruff check .` / `uv run ruff format --check .` -- lint / format check

These run today, regardless of scaffold state:
- `python3 scripts/check_synthetic_data.py` / `python3 scripts/check_mcp_boundary.py` -- ground-rule guard scripts (Rules 1 and 3 above)

## Workflow: issues drive the work

All planned work -- features, chores, bugs -- is tracked as a GitHub Issue, not a TODO file. Full detail in `docs/WORKFLOW.md`; summary:

1. Issues get filed at any level of roughness.
2. The `issue-refiner` skill turns a rough issue into `agent-ready` (unambiguous acceptance criteria, one Type/Priority/Area label each).
3. Say "work on issue #N" to start -- the `work-issue` skill branches, implements, self-verifies, gets an independent code-review pass, and opens a PR.
4. **Never push directly to `main`.** All changes land via PR, and CI (synthetic-data guard, MCP-boundary check, ruff lint, ruff format, pytest) must pass.

**Issue creation rule:** Never create a GitHub issue directly via the API or MCP tools. Always invoke the `issue-refiner` skill -- it enforces the required Type/Priority/Area labels and acceptance criteria before filing. The `.github/ISSUE_TEMPLATE/task.yml` form and the `issue-refiner` skill are the only two sanctioned paths for creating issues.

**Spec-scoped work exception:** work that doesn't have a concrete `week-NN-*.md` spec yet (or research that hasn't turned into a task) does not get filed as a GitHub issue -- log it in `docs/checkpoints/README.md`'s scope preview or `docs/research/` instead. See `docs/WORKFLOW.md`'s "Spec-scoped work" section.

## One-time local setup

- `git config core.hooksPath scripts/git-hooks` -- enables the pre-commit checks (ground-rule guards always run; ruff/pytest once the scaffold exists).
- `gh auth login` -- required before any skill that creates/reads issues or PRs.

## Branch/commit/PR conventions

- Branch: `issue-<N>-<short-slug>`
- Commits reference the issue: `<summary> (#<N>)`
- PRs: `Closes #<N>`, body restates acceptance criteria as a checklist, plus a verification checklist

## Definition of done (applies every week, not just Week 1)

- [ ] The week's "Definition of done" checklist in its spec file is fully checked
- [ ] `uv run pytest` and `uv run ruff check .` pass
- [ ] The demo script in that week's spec runs end-to-end for someone who just cloned the repo
- [ ] `README.md`'s status table is updated
- [ ] Anything explicitly deferred is noted in the week's spec under "Carried forward," not silently dropped

## What NOT to do

- Don't add a memory layer, sandbox, or UI before its designated week, even as a "quick win" (Ground rule 2)
- Don't reach for a hosted/managed service where a self-hosted Docker option exists (Ground rule 4)
- Don't invent ticket/incident data inline in code (Ground rule 3)
- Don't collapse the MCP server layer into a plain function call "for simplicity" (Ground rule 1)
