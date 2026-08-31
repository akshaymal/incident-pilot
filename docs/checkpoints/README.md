# Checkpoints

`incident-pilot` is built in weekly checkpoints, each adding one real layer of the GenAI agent stack on top of a working system from the previous week. Each checkpoint has its own spec file with concrete tasks, a definition of done, and a demo script -- the thing you'd actually show someone.

Detailed specs are written just-in-time, one or two weeks ahead, so they reflect what was actually learned in the prior week rather than guessing too far in advance. This index tracks the full intended arc even where the detailed spec doesn't exist yet.

| Week | Spec | Focus | Adds |
|---|---|---|---|
| 1 | [`week-01-core-loop.md`](week-01-core-loop.md) | Core loop + synthetic data | LangGraph, MCP servers, Langfuse tracing |
| 2 | `week-02-temporal-memory.md` (TBD) | Temporal memory | Graphiti -- "has this happened before, what changed" |
| 3 | `week-03-sandbox-hitl.md` (TBD) | Sandbox + human-in-the-loop | E2B execution, CopilotKit/AG-UI approval gates |
| 4 | `week-04-eval-audit.md` (TBD) | Eval suite + audit trail | Labeled eval set, immutable Postgres audit log |
| 5 (stretch) | `week-05-a2a-handoff.md` (TBD) | Multi-agent handoff | A2A protocol -- router + specialist agent |

## Conventions for spec files

Every week's spec follows the same shape, so both the maintainer and Claude Code always know what to expect:

1. **Goal** -- one or two sentences, what this week proves
2. **In scope / Out of scope** -- explicit, to prevent scope creep into future weeks
3. **Concrete tasks** -- an ordered, checkable task list
4. **Data needed** -- what synthetic data this week requires (new or extended from prior weeks)
5. **Definition of done** -- a checklist; the week isn't complete until every box is checked
6. **Demo script** -- the exact steps to show this week's checkpoint to another person
7. **Carried forward** -- anything deferred from this week to a later one, so it's never silently dropped
