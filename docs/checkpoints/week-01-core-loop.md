# Week 1 -- Core loop + synthetic data

## Goal

Prove the foundational loop works end to end: a synthetic IT ticket goes in, a LangGraph agent classifies it and retrieves a relevant runbook through an MCP server it calls (not a hardcoded lookup), and the entire decision is traceable in Langfuse. This week's system is intentionally read-only -- nothing is executed, no memory persists across tickets, no approval flow exists yet. Those come later.

## In scope

- Synthetic data generator producing tickets, runbooks, and a seed incident history
- A LangGraph graph with at least two real nodes: classify -> retrieve runbook (a third "propose response" node is encouraged but not required)
- One custom MCP server exposing runbooks as resources/tools (not a plain Python import)
- One custom MCP server exposing ticket lookups (can be the same server as runbooks, or separate -- your call)
- Langfuse self-hosted via Docker Compose, instrumented on every graph node
- A minimal CLI or script entry point to run a single ticket through the agent and print the result
- Basic tests for the classification and retrieval logic

## Out of scope (do not build yet)

- Any memory beyond the current ticket (no Graphiti, no cross-ticket recall) -- Week 2
- Any code execution / sandboxing -- Week 3
- Any UI beyond a CLI -- Week 3
- Any approval/human-in-the-loop gate -- Week 3
- The audit log table (Langfuse tracing is enough for this week) -- Week 4
- Any second agent or A2A -- Week 5

If something in this list feels easy to add "while you're in there," don't -- note it as a comment instead.

## Concrete tasks

1. **Repo scaffolding**
   - [ ] `uv init`, add core dependencies (`langgraph`, `langchain`, MCP SDK, `langfuse`)
   - [ ] Set up `src/incident_pilot/` layout per `CLAUDE.md`
   - [ ] `.env.example` with placeholders for LLM provider key and Langfuse keys
   - [ ] `docker-compose.yml` with a Langfuse service (Postgres/Clickhouse as Langfuse requires)

2. **Synthetic data generator** (`scripts/seed_data.py`)
   - [x] Generate 30-50 synthetic tickets across 4-5 categories (network, VPN/access, hardware, software, security)
   - [x] Generate 10-15 synthetic runbooks (markdown files), each mapped to one or more ticket categories
   - [x] Generate 15-20 synthetic past-incident entries with timestamps (not used yet, but needed as fixtures for Week 2 -- generate now so the dataset is stable)
   - [x] Write all of the above to `data/synthetic/` (gitignored; regeneratable)

3. **MCP servers** (`src/incident_pilot/mcp_servers/`)
   - [ ] Runbook server: exposes a tool like `search_runbooks(category, keywords)` returning matching runbook content
   - [ ] Ticket server: exposes a tool like `get_ticket(ticket_id)` (mainly useful once the agent needs to look something up mid-reasoning, but implement it now)

4. **LangGraph agent** (`src/incident_pilot/agents/`)
   - [ ] `classify` node: given raw ticket text, output a category + confidence
   - [ ] `retrieve_runbook` node: calls the MCP runbook server with the classified category
   - [ ] (encouraged) `propose_response` node: drafts a suggested first response citing the runbook
   - [ ] Wire nodes into a graph with explicit edges

5. **Observability**
   - [ ] Langfuse running via Docker Compose
   - [ ] Every node instrumented so a full trace shows: input ticket -> classification -> MCP call -> runbook returned -> (optional) proposed response

6. **Entry point + tests**
   - [ ] A script/CLI: `uv run python -m incident_pilot.run --ticket-id <id>` prints classification, runbook cited, and a Langfuse trace URL
   - [ ] Tests covering classification on a few known synthetic tickets and runbook retrieval correctness

## Data needed

- 30-50 synthetic tickets (this week's primary dataset)
- 10-15 synthetic runbooks (this week's knowledge base)
- 15-20 synthetic past incidents (generated now, consumed starting Week 2 -- don't wire them into the agent yet)

## Definition of done

- [ ] All tasks above checked
- [ ] `uv run pytest` passes
- [ ] `uv run ruff check .` passes
- [ ] Running the CLI against 3 different synthetic tickets produces correct-looking classifications and cites a real runbook for each
- [ ] Every run produces a Langfuse trace you can open in the browser and follow node by node
- [ ] A stranger who clones the repo, runs `uv sync`, `docker compose up -d`, `uv run python scripts/seed_data.py`, and the CLI command, gets a working result with no manual intervention
- [ ] `README.md`'s status table updated to mark Week 1 complete

## Demo script (what you actually show someone)

1. `docker compose up -d && uv run python scripts/seed_data.py` -- show the synthetic data being generated
2. Pick a synthetic ticket, run it through the CLI
3. Show the classification + cited runbook in the terminal output
4. Open the Langfuse UI, pull up that trace, and walk through it node by node -- this is the moment that demonstrates "the agent's reasoning is inspectable," which is the whole thesis of the project
5. Run a second, differently-categorized ticket to show it's not hardcoded to one path

## Carried forward

- Nothing yet -- this is the first checkpoint. Anything descoped during the week should be listed here before marking the week done, so it isn't silently dropped.
