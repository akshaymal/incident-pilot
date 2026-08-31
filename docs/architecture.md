# Architecture

This document describes how `incident-pilot` is put together and, more importantly, *why* each piece was chosen. Read `docs/motivation.md` first if you haven't -- this document assumes you know the "why" and focuses on the "how."

## System overview

A ticket enters at the top, passes through a governed perimeter, and is handled by an agent core built from the layers below. Every stage is observable and, from Week 4 onward, every meaningful decision is written to an immutable audit log.

```
 Client / CLI or minimal UI
          |
          v
 API gateway  (auth, rate limiting -- Week 3+)
          |
          v
 Orchestrator  (LangGraph agent graph)
          |
   -------+-------+-------
   |             |             |
   v             v             v
 Memory      MCP tool       Sandbox
(Graphiti)   servers        (E2B)
   |         (runbooks,        |
   |          tickets)         |
   -------+-------+-------
          |
          v
 Observability & audit trail
 (Langfuse traces + Postgres audit log)
```

Gray/perimeter concerns (gateway, auth, observability, audit) are infrastructure any enterprise app needs regardless of AI. The agent-specific core (orchestrator, memory, tool servers, sandbox) is where the actual GenAI-stack learning happens. That split is deliberate -- it's meant to make obvious which parts of the system are "AI-specific" and which are "just good engineering," because conflating the two is a common source of confusion when people first study agent architectures.

## Data flow, end to end (target state -- built incrementally across weeks)

1. A ticket (or simulated alert) arrives.
2. The **orchestrator** (LangGraph) runs a `classify` node to determine category and confidence.
3. It calls the **runbook MCP server** to retrieve the relevant runbook for that category -- a real MCP tool call, not an in-process function call. This is deliberate: exposing tools over MCP rather than importing them directly is the single highest-transfer skill in the whole project, since MCP is now the standard every framework and vendor speaks.
4. It queries **memory (Graphiti)** for related past incidents: has something like this happened before, and -- because Graphiti models facts with time-bound validity -- what's changed since then. This is what separates the project from a flat-RAG lookup: the reasoning is temporal, not just similarity-based.
5. If the proposed response involves running a diagnostic or remediation script, it executes inside an **E2B sandbox**, never on the host machine running the orchestrator.
6. Any action beyond "propose a response" (e.g., actually applying a fix) waits for **human approval** through a small Next.js + CopilotKit (AG-UI) interface before it's considered final.
7. Every step above -- the classification, the MCP call, the memory query, the sandbox execution, the approval decision -- is traced in **Langfuse** for debugging, and (from Week 4) written to an **immutable Postgres audit log** as a separate concern from the trace store, because a trace store is for engineers debugging behavior and an audit log is for governance/compliance and needs to be queryable independent of the observability stack.

## Component decisions and rationale

| Component | Choice | Why this and not the alternative |
|---|---|---|
| Orchestration | **LangGraph** | Explicit graph/state-machine model rather than an implicit chain -- makes the reasoning steps inspectable and checkpointable, and it was the clear production-adoption leader in the market research this project was scoped from. CrewAI is faster to prototype with but trades away the fine-grained state control this project wants to exercise. |
| Tool access | **MCP** (custom servers, official Python SDK) | The standard every major framework and vendor now speaks. Building real MCP servers (not importing functions) is a deliberate, non-negotiable learning goal -- see `CLAUDE.md` ground rules. |
| Memory | **Graphiti**, self-hosted against Neo4j Community | Temporal knowledge-graph reasoning ("this changed since last time") is more differentiated and more relevant to an ops/incident domain than flat vector-similarity memory. Zep's hosted product would be less setup effort, but it retired its self-hosted tier -- which conflicts directly with priority #6 (anyone can self-host this). |
| Sandboxed execution | **E2B** | Simplest SDK, generous free tier, good default for a project other people will want to try without a lot of setup friction. Daytona (open-source, self-hostable) is documented as an alternative for anyone who wants zero dependency on a third-party sandbox provider. |
| Human-in-the-loop UI | **Next.js + CopilotKit (AG-UI)** | AG-UI is the protocol specifically built for agent-to-frontend communication (streaming state, approval gates, generative UI) -- the piece that MCP (tools) and A2A (agent-to-agent) don't cover. Next.js was chosen because it reuses skills already built while working on a personal portfolio site, so the new-learning budget stays focused on the AI-specific layers. |
| Observability | **Langfuse**, self-hosted | Open-source, self-hostable, and combines tracing + eval + cost tracking in one tool rather than requiring several -- keeps the Docker Compose footprint manageable. |
| Audit log | **Postgres**, dedicated `audit_events` table | Deliberately separate from Langfuse. A trace store optimized for engineer debugging is not the same artifact as a compliance-grade audit log, and conflating them is a common mistake in real "AI governance" implementations -- this project wants to model the distinction correctly. |
| Multi-agent (stretch) | **A2A** | This is the protocol with the thinnest real hands-on adoption of anything in the research, and specifically the protocol for agent-to-agent delegation (as opposed to MCP's agent-to-tool scope) -- reserved as a stretch goal because it's the least load-bearing piece for the core thesis of the project. |

## What's real vs. simulated

- **Tickets, runbooks, and incident history are synthetic**, generated by `scripts/seed_data.py`. See `docs/motivation.md` for why.
- **The "diagnostic scripts" the agent runs are real code executing in a real sandbox** -- the execution isn't simulated, only the underlying infrastructure it's diagnosing is.
- **The audit log and approval gates are real, functioning governance controls** -- not a mockup of what governance would look like. This is the part of the project that's meant to be taken seriously as a reference pattern, even though the domain data around it is synthetic.

## How this maps to the enterprise reference architecture it's modeled on

This project's shape mirrors the "converged enterprise agent platform" pattern found repeatedly in 2026 industry research: a centralized gateway/governance perimeter, a versioned tool registry (MCP-aligned), a memory layer, human-in-the-loop approval gates for consequential actions, sandboxed execution, and a cross-cutting observability + audit plane. Multi-tenancy and zero-trust agent identity (short-lived scoped tokens, per-tenant isolation) are recognized as part of that reference architecture but are explicitly out of scope here -- this project is a single-tenant reference implementation of the governance and reasoning patterns, not a multi-tenant platform.

## Where to go next

- **`docs/checkpoints/README.md`** -- the weekly build plan that turns this architecture into working code, one layer at a time
- **`CLAUDE.md`** -- concrete conventions (repo layout, tooling, definition of done) for implementing against this architecture
