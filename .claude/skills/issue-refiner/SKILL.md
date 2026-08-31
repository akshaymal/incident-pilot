---
name: issue-refiner
description: Turn a rough GitHub issue into an agent-ready one by grilling the user until acceptance criteria, definition of done, area, and priority are all unambiguous and non-overlapping with other open issues. Use when asked to refine, groom, or make an issue agent-ready.
---

# Issue Refiner

Use this skill when the user asks to refine, groom, or prepare a GitHub issue for agent pickup (e.g., "refine issue #12", "make this issue agent-ready").

## Process

1. **Fetch the issue.** Run `gh issue view <N> --json title,body,labels` to read its current state.
2. **Fetch open issues for overlap check.** Run `gh issue list --state open --json number,title,labels` and compare scope against the issue being refined. Flag any apparent overlap to the user before proceeding.
3. **Check it against checkpoint scope.** Skim `docs/checkpoints/README.md`'s scope previews (and the current week's full spec, if one exists) for the area this issue touches. Week boundaries here are guidance, not a hard gate — it's fine to pull forward a later week's item if the current week is otherwise done. If the issue clearly belongs to a later week, just note that to the user so it's a deliberate choice, not silently missed scope.
4. **Grill for the outcome first, always** — even if the issue already names an implementation ("add a `check_memory` node," "cache runbook lookups"). Ask what the user is trying to accomplish and why it matters — for this project that often means asking which layer of the agent stack this is meant to exercise (see `docs/architecture.md`), since the point is usually the learning, not just the shipped behavior. If the conversation drifts to implementation before the outcome is established, steer it back to the outcome before continuing.
5. **Present implementation options once the outcome is clear.** Come up with your own recommended approaches for achieving that outcome, and include the user's originally proposed implementation (if they gave one) as one of the candidates. Walk the user through the trade-offs of each so they can make an informed choice — don't let the first idea mentioned win by default. Weigh options against this project's ground rules in `CLAUDE.md` (real MCP calls over hardcoded functions, self-hosted over managed services, synthetic data only, audit-mindedness) — flag an option that would violate one of them even if it's the fastest path.
6. **Grill the user** using the round-based interview pattern (see the `grilling` skill if installed) until each of the following is concretely filled in, not vague:
   - **Type**: `feature` / `chore` / `bug`
   - **Priority**: `P1` / `P2` / `P3`
   - **Area**: `agent` / `mcp` / `memory` / `sandbox` / `observability` / `audit` / `ui` / `infra` / `docs`
   - **Acceptance criteria**: a checklist of specific, verifiable conditions covering *both* the outcome (what must be true, and why it matters) and the implementation chosen in step 5 (the specific mechanism to build) — never one without the other. Not "add memory recall," but e.g. "the agent surfaces past incidents in the same category (outcome), via a new `check_memory` LangGraph node that queries Graphiti over the ingested incident history (implementation)."
   - **Definition of done**: `uv run pytest` and `uv run ruff check .`/`ruff format --check .` pass, plus anything issue-specific. Each issue-specific item must name **how it will be checked**, not just what should be true — a command to run, a specific file/log/trace to inspect, or a manual step to perform, so `work-issue` has something concrete to execute rather than eyeball at PR time. "Langfuse trace shows the new node" is not done until it also says *how*: e.g. "run `uv run python -m incident_pilot.run --ticket-id <id>`, open the Langfuse UI, confirm a span named `check_memory` appears under the run's trace." If the user can't say how an item would be checked, treat that the same as unclear acceptance criteria — keep grilling rather than accepting a DoD item nobody can actually execute.
7. **Check for ambiguity against other open issues.** If two open issues could both plausibly claim the same file, node, or behavior, stop and ask the user to either merge them or redraw the boundary before continuing.
8. **Update the issue** via `gh issue edit <N>`:
   - Set the body to the filled-in template (Type/Priority/Area/Description/Acceptance criteria/DoD).
   - Apply exactly one label from each of Type, Priority, Area.
   - Apply the `agent-ready` label only once all of the above is unambiguous.
9. **Confirm with the user**: report the final issue body and labels before ending.

## Guardrails

- Never apply `agent-ready` on your own judgment alone — the user must explicitly confirm the acceptance criteria are correct and complete.
- If the user can't answer a question about scope precisely, that itself is a signal the issue isn't ready — keep grilling rather than filling in a plausible-sounding guess.
- Never write acceptance criteria with only an outcome or only an implementation — always both.
