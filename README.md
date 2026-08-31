# incident-pilot

An AI-powered IT operations & incident triage copilot, built as a hands-on tour through the modern GenAI agent stack: orchestration, memory, tool protocols, sandboxed execution, human-in-the-loop governance, and observability.

**All data in this project is synthetic.** Tickets, runbooks, and incident history are generated locally -- no real company or personal data is used.

## The problem

Most GenAI agent demos stop at "the agent does the task." They skip the part that actually determines whether an organization could trust that agent with real work: can anyone say what data it touched, whether an action was approved, or why it made a particular call -- and does that trail survive an audit? That gap, not raw model capability, is the main reason enterprise agent pilots stall before reaching production, and regulation (the EU AI Act's automatic-logging requirements among them) is starting to make that trail a legal requirement rather than a nice-to-have.

## How incident-pilot addresses it

`incident-pilot` picks a genuinely common enterprise pattern -- IT ticket and incident triage -- and builds it the way a platform team focused on governance would, not the way a weekend demo would:

- Every tool the agent uses is exposed over a real protocol (**MCP**), not a hardcoded function call, so tool access is inspectable and swappable
- "Have we seen this before?" is answered with **temporal reasoning** over a knowledge graph, not a flat similarity lookup -- the agent can reason about what's changed since the last time, not just that something looks similar
- Any code the agent wants to run executes in an **isolated sandbox**, never on the host
- Nothing consequential happens without **explicit human approval**
- Every one of those steps -- every tool call, memory read, sandbox execution, and approval -- is written to an inspectable trace and, eventually, an **immutable audit log**

The governance layer isn't bolted on after the fact -- it's the reason the project exists. The ticket-triage agent is the vehicle for demonstrating that pattern properly, not the end goal in itself. This shape mirrors the reference architecture showing up across real 2026 enterprise agent deployments: a governed tool registry, a memory layer, human-in-the-loop approval gates, sandboxed execution, and a cross-cutting observability/audit plane. Full reasoning: [`docs/motivation.md`](docs/motivation.md) (the why) and [`docs/architecture.md`](docs/architecture.md) (the how).

## What happens when a ticket comes in

1. **Classify** -- the agent categorizes the ticket and retrieves the relevant runbook via an MCP tool call
2. **Recall** -- it checks whether something like this has happened before, and what's changed since, using temporal memory (Graphiti)
3. **Propose** -- it drafts a diagnosis or fix, running any diagnostic script inside an isolated sandbox (E2B)
4. **Approve** -- a human reviews and approves the proposed action before anything is considered final
5. **Record** -- every step above is traced end to end and logged to an audit trail

Each of these five steps corresponds to one weekly build checkpoint -- see [Project status](#project-status) below.

## Architecture

| Layer | Technology | Role |
|---|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful agent graph: classify -> retrieve -> reason -> act |
| Tool access | [MCP](https://modelcontextprotocol.io) | Runbooks and ticket data served as MCP servers, not hardcoded calls |
| Memory | [Graphiti](https://github.com/getzep/graphiti) (self-hosted, Neo4j) | Temporal knowledge graph -- "has this happened before, what changed" |
| Sandboxed execution | [E2B](https://e2b.dev) | Any diagnostic/remediation script runs isolated, never on the host |
| Human-in-the-loop UI | Next.js + [CopilotKit](https://www.copilotkit.ai) (AG-UI) | Approval gates before any action is considered final |
| Observability | [Langfuse](https://langfuse.com) (self-hosted) | Full trace of every agent decision |
| Audit trail | Postgres | Immutable log of every tool call, memory access, and approval |
| Multi-agent (stretch) | [A2A](https://a2a-protocol.org) | Router agent delegates security-flagged tickets to a specialist agent |

Full rationale for each choice, including alternatives considered: [`docs/architecture.md`](docs/architecture.md).

## Project status

This is a live, ongoing project built in weekly checkpoints, each adding one real layer on top of a working system from the previous week. See [`docs/checkpoints/`](docs/checkpoints/README.md) for the full roadmap, including scope previews for weeks that haven't started yet.

| Week | Focus | Status |
|---|---|---|
| 1 | Core loop: LangGraph + MCP + Langfuse, synthetic data | In progress |
| 2 | Temporal memory (Graphiti) | Not started |
| 3 | Sandbox (E2B) + human-in-the-loop UI | Not started |
| 4 | Eval suite + audit trail | Not started |
| 5 | Multi-agent handoff via A2A (stretch) | Not started |

## Getting started

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker + Docker Compose (Postgres, Neo4j, Langfuse all run locally)
- An LLM provider API key (Anthropic Claude by default; see `.env.example`)
- An [E2B](https://e2b.dev) API key (free tier is enough) -- needed from Week 3 onward

### Setup
```bash
git clone https://github.com/akshaymal/incident-pilot.git
cd incident-pilot
uv sync
cp .env.example .env   # fill in your API keys
docker compose up -d   # starts Postgres, Neo4j, Langfuse
uv run python scripts/seed_data.py   # generates synthetic tickets, runbooks, incident history
uv run python -m incident_pilot.run  # starts the agent
```

*(Exact commands will be finalized as Week 1 is implemented -- this is the intended shape.)*

## Development workflow

Work is tracked as GitHub Issues and implemented via Claude Code skills (`issue-refiner`, `work-issue`). All changes land via PR — CI runs ruff lint, ruff format check, and pytest. See `CLAUDE.md` for the summary and [`docs/WORKFLOW.md`](docs/WORKFLOW.md) for the full reference.

## Further reading

- [`docs/motivation.md`](docs/motivation.md) -- the full problem statement, guiding priorities, and explicit non-goals
- [`docs/architecture.md`](docs/architecture.md) -- system design, data flow, and the rationale behind every technology choice
- [`docs/checkpoints/`](docs/checkpoints/README.md) -- the weekly build plan and current status
- [`docs/research/`](docs/research/2026-08-genai-agent-market-research.md) -- the market research this project was scoped from
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) -- the issue-driven development process (label taxonomy, the `issue-refiner`/`work-issue` lifecycle, CI gates)
- [`CLAUDE.md`](CLAUDE.md) -- operating conventions for anyone (human or agent) building this

## License

MIT (see [`LICENSE`](LICENSE)).
