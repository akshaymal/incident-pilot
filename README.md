# incident-pilot

An AI-powered IT operations & incident triage copilot, built as a hands-on tour through the modern GenAI agent stack: orchestration, memory, tool protocols, sandboxed execution, human-in-the-loop governance, and observability.

**All data in this project is synthetic.** Tickets, runbooks, and incident history are generated locally -- no real company or personal data is used.

## Start here

- **New to this project?** Read [`docs/motivation.md`](docs/motivation.md) first -- the problem this solves and why it's built this way.
- **Want the technical design?** [`docs/architecture.md`](docs/architecture.md) covers the full system and the reasoning behind every technology choice.
- **Building it (human or Claude Code)?** [`CLAUDE.md`](CLAUDE.md) has the operating conventions, repo layout, and definition of done.
- **What's being built when?** [`docs/checkpoints/`](docs/checkpoints/README.md) is the weekly roadmap and current status.

## What this is

When a support ticket or an alert comes in, `incident-pilot`:
1. Classifies it and retrieves the relevant runbook
2. Checks whether something like this has happened before, and what's changed since
3. Proposes a diagnosis or fix, running any diagnostic script in an isolated sandbox
4. Waits for human approval before anything irreversible happens
5. Logs every step -- every tool call, every memory read, every approval -- to an audit trail

It's not trying to be a polished product. It's a reference implementation of what an enterprise "agent platform" looks like when governance is a first-class requirement, not an afterthought -- built one weekly checkpoint at a time. See [`docs/motivation.md`](docs/motivation.md) for the full reasoning.

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

Full rationale for each choice: [`docs/architecture.md`](docs/architecture.md).

## Project status

This is a live, ongoing project built in weekly checkpoints. See [`docs/checkpoints/`](docs/checkpoints/README.md) for the roadmap and what's done so far.

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

## License

MIT (see [`LICENSE`](LICENSE)).
