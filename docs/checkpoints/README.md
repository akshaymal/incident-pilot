# Checkpoints

`incident-pilot` is built in weekly checkpoints, each adding one real layer of the GenAI agent stack on top of a working system from the previous week.

## How this index works

Every week gets two levels of detail, on different timelines:

- **A scope preview, written now, for every week.** Goal, what it adds, and -- critically -- what's explicitly *out* of scope, so the boundary between this week and the next is never ambiguous, even before the full spec exists. This is what's below.
- **A full detailed spec** (`week-NN-*.md`), written just-in-time, one or two weeks ahead of when it's actually built. It expands the preview into concrete tasks, a definition of done, and a demo script -- see "Conventions for spec files" below. This is deferred because task-level detail (exact function signatures, integration patterns) should reflect what was actually learned in the prior week, not a guess made weeks earlier.

If you're Claude Code and you're looking for what to build *right now*, go to the current week's full spec. If you're deciding whether something belongs in the current week or should wait, the scope previews below are the source of truth for that boundary even for weeks that don't have a full spec yet.

| Week | Spec | Status |
|---|---|---|
| 1 | [`week-01-core-loop.md`](week-01-core-loop.md) | In progress -- full spec exists |
| 2 | `week-02-temporal-memory.md` (not yet written) | Not started -- scope preview below |
| 3 | `week-03-sandbox-hitl.md` (not yet written) | Not started -- scope preview below |
| 4 | `week-04-eval-audit.md` (not yet written) | Not started -- scope preview below |
| 5 (stretch) | `week-05-a2a-handoff.md` (not yet written) | Not started -- scope preview below |

## Week 1 -- Core loop + synthetic data

Full spec: [`week-01-core-loop.md`](week-01-core-loop.md). Summary: a synthetic ticket is classified and matched to a runbook via a real MCP tool call, with every step traced in Langfuse. Read-only -- nothing executes, nothing persists across tickets.

## Week 2 -- Temporal memory

**Goal:** Before responding, the agent checks whether something like this ticket has happened before -- and, because memory is temporal rather than a flat similarity lookup, *what's changed* since then (e.g., "this alert fired in March, root cause was X, we patched Y -- but it's back, so something else changed").

**Adds:** Graphiti, self-hosted against Neo4j (via Docker Compose). The synthetic incident-history fixtures generated in Week 1 get ingested into the graph. A new `check_memory` node is added to the Week 1 LangGraph graph -- extending it, not replacing the classify/retrieve nodes.

**Explicitly out of scope for Week 2:**
- No sandboxed execution, no code running anywhere (Week 3)
- No UI beyond the Week 1 CLI (Week 3)
- No approval/human-in-the-loop gate (Week 3)
- No formal audit log table -- Langfuse tracing remains sufficient this week (Week 4)
- No changes to how tickets are classified or how runbooks are retrieved -- Week 2 only adds a new capability alongside Week 1's, it doesn't touch that logic

## Week 3 -- Sandbox + human-in-the-loop UI

**Goal:** Any diagnostic or remediation script the agent proposes actually executes -- in an isolated E2B sandbox, never on the host -- and nothing is considered "done" until a human explicitly approves it through a real UI, not just a CLI print statement.

**Adds:** E2B SDK integration. A new `propose_action -> execute_in_sandbox -> await_approval` sequence in the graph. A `web/` directory: Next.js + CopilotKit (AG-UI) frontend that surfaces the proposed action and blocks on human approval before the flow is marked complete.

**Explicitly out of scope for Week 3:**
- No formal audit log table yet -- still Langfuse tracing plus whatever approval record the UI itself needs to function (Week 4 formalizes this into a real `audit_events` table)
- No eval suite / scoring against labeled data (Week 4)
- No second agent, no A2A (Week 5)
- Sandboxed execution here means *running the specific diagnostic scripts the agent proposes* -- not a general-purpose code sandbox for arbitrary tasks

## Week 4 -- Eval suite + audit trail

**Goal:** Prove the system built in Weeks 1-3 is actually correct and governable: score classification/response quality against a small labeled synthetic eval set, and write every meaningful decision (classification, tool call, memory query, sandbox execution, approval) to an immutable Postgres audit log -- deliberately separate from Langfuse traces, since a trace store is for debugging and an audit log is for governance/compliance.

**Adds:** A labeled eval dataset (a subset of synthetic tickets with known-correct categories/runbooks) and a scoring script (Langfuse's built-in eval feature, or a simple custom scorer). A Postgres `audit_events` table and a writer that hooks into every node from Weeks 1-3.

**Explicitly out of scope for Week 4:**
- No new agent capability -- this week instruments and validates what already exists, it doesn't add new behavior to the graph
- No second agent, no A2A (Week 5)
- The eval set only needs to be large enough to be meaningful (a handful of labeled tickets), not comprehensive -- this isn't a benchmark-building exercise

## Week 5 (stretch) -- Multi-agent handoff via A2A

**Goal:** Split the single agent into a router and a specialist sub-agent -- e.g., a security-specialist agent that takes over anything flagged as a potential security incident -- with the handoff implemented over the A2A protocol rather than an in-process function call.

**Adds:** The A2A Python SDK, a second agent process, an Agent Card definition, and an explicit delegation flow between router and specialist.

**Explicitly out of scope / notes:**
- This is a stretch goal. Weeks 1-4 are a complete, coherent, demoable system on their own -- if time runs out, stopping after Week 4 is a legitimate finish, not an incomplete one.
- Scope for the specialist agent should stay narrow (one clear delegation trigger, e.g. "security-flagged tickets") rather than trying to generalize the router to many specialist types -- the point is to exercise the A2A handoff pattern once, correctly, not to build a general multi-agent framework.

## Conventions for spec files

When a week's full spec is written (one or two weeks ahead of building it), it follows this shape:

1. **Goal** -- one or two sentences, what this week proves
2. **In scope / Out of scope** -- explicit, expanding on the scope preview above
3. **Concrete tasks** -- an ordered, checkable task list
4. **Data needed** -- what synthetic data this week requires (new or extended from prior weeks)
5. **Definition of done** -- a checklist; the week isn't complete until every box is checked
6. **Demo script** -- the exact steps to show this week's checkpoint to another person
7. **Carried forward** -- anything deferred from this week to a later one, so it's never silently dropped
