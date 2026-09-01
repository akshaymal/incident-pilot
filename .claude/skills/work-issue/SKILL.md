---
name: work-issue
description: Implement a GitHub issue that has been marked agent-ready — branch, implement against its acceptance criteria, get an independent code-review pass, and open a PR. Use when asked to work on, pick up, or implement a specific issue number.
---

# Work Issue

Use this skill when asked to "work on issue #N" or equivalent.

## Process

1. **Fetch and verify.** Read the issue using whichever tool is available in this session:
   - **Local session** (`gh` available): `gh issue view <N> --json title,body,labels,state`
   - **Remote session** (`gh` not available): use the `mcp__github__issue_read` tool with `owner: akshaymal`, `repo: incident-pilot`, `issue_number: <N>`

   If the issue isn't open, stop and tell the user. If it does not have the `agent-ready` label, stop and tell the user to run the `issue-refiner` skill on it first — do not attempt to infer missing scope yourself.
2. **Branch.** From an up-to-date `main`: `git checkout main && git pull && git checkout -b issue-<N>-<short-slug>`, where `<short-slug>` is a kebab-case summary of the issue title.
3. **Implement** against the acceptance criteria in the issue body. Follow `CLAUDE.md`'s Ground rules 1-6 in full — see that file for the specifics (this skill doesn't restate them; if this skill's wording of anything ever conflicts with `CLAUDE.md`, `CLAUDE.md` wins). Make focused commits, each referencing the issue: `git commit -m "<summary> (#<N>)"`.

   A few rules for the implementation phase:
   - **One criterion at a time.** Work through the acceptance criteria sequentially, not all at once — it keeps commits focused and makes partial progress reviewable.
   - **Ambiguity mid-implementation → stop and ask.** If an acceptance criterion turns out to be unclear or contradictory once you're in the code, stop and ask the user rather than making a judgment call that silently changes scope. This is preferable to finishing something the user didn't want. **If the user's answer changes the AC** (adds, drops, or redefines a criterion from what the issue currently says), update the issue itself before continuing — same tool as `issue-refiner` (`gh issue edit <N>` locally, or `mcp__github__issue_write` in a remote session) — so the issue body matches what's actually being built. Do this at the point of the decision, not as cleanup later; otherwise the issue and the shipped PR silently diverge and nothing else in the workflow would catch it.
   - **Blocker hit → surface it immediately.** If you hit a technical blocker (a missing dependency, an API constraint, an environmental issue) that you cannot resolve, tell the user what it is and what options exist — don't silently work around it in a way that narrows what the implementation can do.
   - **Scope creep → resist it.** If you notice something adjacent that could be improved, note it for a separate issue rather than fixing it here. A bug fix doesn't need surrounding cleanup; a feature doesn't need extra polish.
4. **Sync with base first.** Implementation (plus any back-and-forth on a tricky fix) can take long enough that `main` moves — a same-session branch going stale isn't a fluke, it's expected on anything nontrivial. Run `git fetch origin main`. If `origin/main` has commits the branch doesn't (`git log <branch>..origin/main` is non-empty), merge it in: `git merge origin/main` (never rebase or force-push — this may not be the only place work is happening, and a merge commit can't destroy anything). Resolve any conflicts. Doing this *before* self-verify means the verify pass below covers the code that will actually ship, instead of verifying a version of the branch that's about to be superseded — merging main in twice (once here, once again after review) is wasted work when once, at the right point, covers it.
5. **Self-verify** before review. Run all of the following in order. Fix any failures before proceeding.

   ```
   python3 scripts/check_synthetic_data.py
   python3 scripts/check_mcp_boundary.py
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest
   ```

   The first two run regardless of whether `pyproject.toml` exists — they're pure-stdlib heuristic guards for Ground rules 1 and 3 (`CLAUDE.md`): the MCP-boundary check fails if anything under `src/incident_pilot/agents/` imports `incident_pilot.mcp_servers` directly instead of calling it as a real MCP tool; the synthetic-data guard fails on hardcoded ticket/runbook/incident-shaped literals outside `scripts/seed_data.py`, or real-looking email domains/SSN patterns anywhere. Both are heuristics, not proofs — a failure is a strong signal to look closer, not necessarily a hard violation; if it's a false positive, say so in the PR rather than silently reshaping the code to dodge the pattern.

   If the issue touches Docker Compose services (Langfuse, Neo4j, Postgres), also confirm `docker compose up -d` brings the stack up healthy and, if the change affects the seed data or CLI entry point, run `uv run python scripts/seed_data.py` and the relevant CLI command end-to-end once.

   Capture each command's output to a log file rather than letting it flood the conversation — most runs pass, and there's no reason to carry hundreds of lines of routine test output through the rest of the session. On failure, grep the log for the tool's actual failure markers with a little context:

   ```bash
   uv run pytest > /tmp/pytest.log 2>&1
   if [ $? -ne 0 ]; then
     grep -n -iE "error|failed|FAILED" /tmp/pytest.log -A 5 -B 2 || tail -100 /tmp/pytest.log
   fi
   ```

   Apply the same pattern — log to file, grep for failure markers on non-zero exit, `tail` only as a last-resort fallback if grep finds nothing — to every command above.

   **If no `pyproject.toml` exists yet** (pre-Week-1 scaffold), the ruff/pytest commands don't apply — run the two guard scripts anyway, then say so and skip straight to step 6.
6. **Independent review gate.** Dispatch a fresh subagent (not a fork — no shared context with this session) with the `code-review` skill. Give it a structured brief — not just the raw diff — so it spends tokens on the actual review rather than re-deriving context from scratch:

   - **Which files changed** (`git diff main...HEAD --name-only`)
   - **The acceptance criteria** from the issue, verbatim
   - **The diff itself** (`git diff main...HEAD`)
   - **Any known risk areas** — files or components that have caused bugs before, or that other parts of the codebase depend on heavily (e.g., the LangGraph graph definition, MCP server tool signatures, the audit-log writer)
   - Instruct it to review for **correctness only**: logic bugs, missed edge cases, runtime misbehavior. Explicitly tell it to skip style, structure, and anything already enforced by ruff — that gate already ran.
   - Explicitly ask it to flag any ground-rule violation it notices in passing: a direct import from `mcp_servers/` instead of a real MCP call, non-synthetic data introduced outside `scripts/seed_data.py`, or a hosted/managed service substituted for a self-hosted one. These are easy to miss in a normal correctness review but are non-negotiable per `CLAUDE.md`.
   - **Require it to verify AC coverage, item by item.** For each line in the acceptance criteria, it must state whether the diff satisfies it, partially satisfies it, or doesn't touch it at all — checking a box in the PR body is not evidence on its own. This is the actual verification step behind the AC checklist in step 9: the implementing session (this one) is not a credible judge of whether its own work meets its own criteria, so the checkmarks below come from this independent pass, not from self-assessment.

   Do not tell it what reasoning produced the changes or what you expected the implementation to look like — the value of the gate is the independent read.

   **Unmet or partially-met AC → fix and re-run this step**, same as a correctness bug (see "Respond to findings by severity" below) — before opening the PR, not noted as a caveat in it.

   **Model selection:** Default to `claude-haiku-4-5-20251001` — the brief is structured and the mandate is narrow, which is exactly the case where a smaller model performs well at a fraction of the cost. Upgrade to `claude-sonnet-4-6` when the diff touches any of these high-blast-radius areas:
   - `src/incident_pilot/agents/` — the LangGraph graph definition, consumed by every downstream node
   - `src/incident_pilot/mcp_servers/` — the tool-protocol boundary; a bug here is invisible to callers until runtime
   - `src/incident_pilot/audit/` — compliance-critical by design; a silent logging gap defeats the point of the project
   - CI config (`.github/workflows/`) or harness scripts (`scripts/`) — failures here block all future work
   - `docker-compose.yml` — affects whether the whole stack is reproducible for a stranger

   **Respond to findings by severity, not uniformly:**
   - **Correctness bug** (wrong logic, missed edge case, data loss risk) or **ground-rule violation**: fix it, then re-run this step — the fix itself might introduce something new.
   - **Nit or low-confidence finding** (rename, minor null-check, stylistic): apply it in place and continue — no re-run needed for changes this small.
7. **Docs & artifacts check.** Dispatch a subagent (Explore, or general-purpose if it needs to reason about scope) to do the reading and comparison, not this session — it's read-heavy investigative work with a small output, the same pattern as the review gate in step 6. Brief it with: the diff (`git diff main...HEAD`), the issue's acceptance criteria, and which docs are in play — `docs/checkpoints/README.md`'s scope table and the current week's `docs/checkpoints/week-NN-*.md` always; `README.md` and `docs/WORKFLOW.md` only if the change touches harness, workflow, or scripts. Ask it to report back, per doc: accurate / describes something now stale (quote the stale line) / has a checkbox this issue completes / silent on something the change introduces that needs documenting.

   Act on what comes back in this session (it has the diff context to write the actual edit, the subagent doesn't need to):
   - Stale line reported → update it in this PR, don't leave known drift for a future pass.
   - Checkbox reported → check it off.
   - Undocumented new thing reported (e.g. a new subsystem) → write a new doc rather than overloading an unrelated one.
   - Everything reported accurate/silent → no action, don't manufacture doc edits for their own sake.
8. **Re-check base before opening the PR.** Review rounds (steps 6-7) can themselves take long enough for `main` to move again. Run `git fetch origin main` and check `git log <branch>..origin/main`. If it's empty, the merge from step 4 still covers what's shipping — go straight to step 9. If it's non-empty, merge it in (same approach as step 4, resolve any conflicts) and re-run *only* step 5 (self-verify) against the newly-merged result — a clean merge can still combine into something that no longer passes tests, and the merged-in commits weren't covered by this issue's own review round. Push, *then* open the PR. This step should be a no-op most of the time; it only does real work when main moved again during review.
9. **Open the PR.** Use whichever tool is available in this session:
   - **Local session** (`gh` available): `gh pr create --title "<summary> (#<N>)" --body "<body>"`
   - **Remote session** (`gh` not available): use the `mcp__github__create_pull_request` tool with `owner: akshaymal`, `repo: incident-pilot`, `head: <branch>`, `base: main`, `title`, and `body`

   Body:

   ```
   Closes #<N>

   ## Acceptance criteria

   <checklist copied from the issue, each item checked or explicitly left unchecked with a reason>
   <the AC coverage verdict from step 6's review pass — not this session's own assessment>

   ## Verification

   - [x] python3 scripts/check_synthetic_data.py (CI-enforced)
   - [x] python3 scripts/check_mcp_boundary.py (CI-enforced)
   - [x] uv run ruff check . (CI-enforced)
   - [x] uv run ruff format --check . (CI-enforced)
   - [x] uv run pytest (CI-enforced)
   - [x] Independent code-review pass, including AC coverage (self-reported — see above)
   - [x] Docs/artifacts checked for staleness against this change (self-reported — see above)
   ```

   The `(CI-enforced)` / `(self-reported)` tags matter: the first five items are re-run by CI on the same commit and will fail the build if untrue, so a reviewer can trust the checkbox on its own. The last two are this session's own claim about work a human can't re-run from the PR — call that out rather than let both kinds of checkbox look equally authoritative.

10. **Report back** the PR URL and a one-line summary. Do not merge — merging is the user's call.

## Guardrails

- Never push directly to `main`.
- Never skip the independent review gate, even for small changes.
- Never skip the docs & artifacts check, even when the answer is "nothing to update."
- Never open a PR without first checking the branch is current with `origin/main` (step 8) — a PR opened against a stale base is a preventable, not occasional, failure mode.
- If the acceptance criteria turn out to be wrong or incomplete once you're implementing, stop and ask the user rather than silently expanding or shrinking scope.
- Never quietly widen an issue's Area/week scope — pulling forward later work is fine (week boundaries are guidance), but it should be visible in the PR description, not buried in the diff.
- Never let the issue's AC text go stale after a user-approved scope change mid-implementation — update the issue itself (step 3), so the issue and the merged PR describe the same thing.
