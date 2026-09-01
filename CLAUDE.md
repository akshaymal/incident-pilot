# CLAUDE.md -- project brief for Claude Code

This file gives Claude Code the standing context it needs to work on `incident-pilot` without re-explaining the project each session.

**Precedence.** This file is the source of truth for ground rules and conventions. Skills under `.claude/skills/` may restate a rule for their own context, but if a skill's wording and this file ever disagree, this file wins -- treat the mismatch as a bug in the skill, worth flagging, not license to pick either.

**What to read, by task.** This file is always loaded; everything else is read on demand, not by default. Reason: not needed -- an already-`agent-ready` issue or a scoped bugfix already carries the context those docs would otherwise supply.

| Task | Read (in order) | Skip |
|---|---|---|
| Scoped issue work (`work-issue` on an `agent-ready` issue) | current week's `docs/checkpoints/week-NN-*.md` | `motivation.md`, `architecture.md` -- the issue body already has the outcome + implementation decision |
| Refining a rough issue / design or scope decision (`issue-refiner`, weighing implementation options) | `docs/motivation.md` -> `docs/architecture.md` | -- |
| New contributor, or asked to explain the project | `docs/motivation.md` -> `docs/architecture.md` | -- |
| Pure bugfix, typo, refactor -- no scope/design change | (none beyond this file + relevant source) | all of the above |
| Checking an issue's scope against other weeks | `docs/checkpoints/README.md` | -- |

When in doubt, don't read a doc defensively "just in case" -- ask the user if something's unclear instead.

## What this project is

An AI IT-ops/incident triage copilot, built to give the maintainer (a software engineer) hands-on experience with the modern GenAI agent stack: LangGraph orchestration, MCP tool servers, temporal memory (Graphiti), sandboxed execution (E2B), human-in-the-loop UI (AG-UI/CopilotKit), observability (Langfuse), and audit logging. See `docs/motivation.md` for the full reasoning.

**This is a learning project first, a product second.** When there's a choice between the fastest way to make it work and the way that teaches the underlying concept, prefer the latter and say so explicitly.

## Ground rules

**IMPORTANT -- rules 1 and 3 are non-negotiable and CI-enforced.** A PR that violates either does not merge, heuristics permitting (see the note below the list). Everything else is a strong convention, not a hard gate.

1. **IMPORTANT: Real MCP tool calls, never hardcoded imports.** Runbooks and ticket data are served via custom MCP servers under `src/incident_pilot/mcp_servers/`. Code under `src/incident_pilot/agents/` must call them as MCP tools, not import the server module directly -- even though that's simpler, exposing them over MCP is the actual learning goal. Enforced mechanically by `scripts/check_mcp_boundary.py`.
2. **Checkpoint scope is guidance, not a hard gate.** `docs/checkpoints/week-NN-*.md` files define what each week is *for*. It's fine to start next week's work early once the current week's definition of done is fully met, or to pull a later week's item forward when it's genuinely ready. What isn't fine is scope drift that isn't visible -- see `docs/WORKFLOW.md`.
3. **IMPORTANT: All data is synthetic and must stay that way.** Never introduce real personal, company, or scraped data. `scripts/seed_data.py` is the only source of ticket/runbook/incident data -- never invent it inline in code. Enforced (heuristically) by `scripts/check_synthetic_data.py`.
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

Working today (repo scaffold has landed -- `pyproject.toml`/`uv.lock` exist):
- `docker compose up -d` -- start Postgres/Neo4j/Langfuse
- `uv sync` -- install dependencies
- `uv run pytest` -- run tests
- `uv run ruff check .` / `uv run ruff format --check .` -- lint / format check

Pending Week 1's remaining concrete tasks (`docs/checkpoints/week-01-core-loop.md`) -- will error until then:
- `uv run python scripts/seed_data.py` -- generate synthetic tickets/runbooks/incidents
- `uv run python -m incident_pilot.run --ticket-id <id>` -- run one ticket through the agent

These don't need `uv sync` first -- pure-stdlib guard scripts, runnable any time:
- `python3 scripts/check_synthetic_data.py` / `python3 scripts/check_mcp_boundary.py` -- ground-rule guard scripts (Rules 1 and 3 above)

**Environment setup:** copy `.env.example` to `.env`. It needs an `ANTHROPIC_API_KEY` (or uncomment the `OPENAI_API_KEY` line to use OpenAI instead) and, after `docker compose up -d`, a Langfuse project's keys (Langfuse UI -- Settings -> API Keys) for `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY`.

## Workflow: issues drive the work

All planned work -- features, chores, bugs -- is tracked as a GitHub Issue, not a TODO file. Full detail in `docs/WORKFLOW.md`; summary:

1. Issues get filed at any level of roughness.
2. The `issue-refiner` skill turns a rough issue into `agent-ready` (unambiguous acceptance criteria, one Type/Priority/Area label each).
3. Say "work on issue #N" to start -- the `work-issue` skill branches, implements, self-verifies, gets an independent code-review pass, and opens a PR.
4. **Never push directly to `main`.** All changes land via PR, and CI (synthetic-data guard, MCP-boundary check, ruff lint, ruff format, pytest) must pass.

**Issue creation rule:** Never create a GitHub issue directly via the API or MCP tools. Always invoke the `issue-refiner` skill -- it enforces the required Type/Priority/Area labels and acceptance criteria before filing. The `.github/ISSUE_TEMPLATE/task.yml` form and the `issue-refiner` skill are the only two sanctioned paths for creating issues.

**Spec-scoped work exception:** work that doesn't have a concrete `week-NN-*.md` spec yet (or research that hasn't turned into a task) does not get filed as a GitHub issue -- log it in `docs/checkpoints/README.md`'s scope preview or `docs/research/` instead. See `docs/WORKFLOW.md`'s "Spec-scoped work" section.

## One-time local setup

- `git config core.hooksPath scripts/git-hooks` -- enables the pre-commit checks: the ground-rule guards always run, plus `ruff check`/`ruff format --check` now that the scaffold exists (`pyproject.toml`). The hook does not run `pytest` -- that's CI's and `work-issue`'s self-verify step's job, not pre-commit's.
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

Each of these is the specific shortcut that's tempting in the moment, not a restatement of the ground rule it violates:

- Don't wire up Graphiti, E2B, or a UI early because a task "just needs a little bit of memory/sandboxing/UI to work properly" -- that's scope drift wearing a quick-win costume (Ground rule 2)
- Don't reach for a managed service (e.g. Zep Cloud, a hosted Postgres) to skip local Docker setup, even temporarily "just to unblock this one task" (Ground rule 4)
- Don't hardcode a "realistic-looking" example ticket/runbook into a test fixture instead of pulling from `scripts/seed_data.py`'s output, even for a quick one-off test (Ground rule 3)
- Don't import `incident_pilot.mcp_servers` directly from a script or agent node "just for this one debugging call" -- the MCP boundary has no carve-out for one-offs (Ground rule 1)

## Keeping this file current

**Last reviewed:** Week 1 (2026-09-01), against the state of the repo right after scaffolding landed. If a section here describes something that's since changed (a command that now works, a rule that's been superseded), fix it in the same PR that causes the drift -- don't leave it for a future pass, and update this line when you do. Ground rules and conventions belong here; anything tied to a specific week's progress (like the Commands section above) belongs in that week's checkpoint doc first, with only a pointer here.
