## Summary

<!-- What does this PR do and why -->

Closes #

## Acceptance criteria

<!-- Copy the acceptance criteria checklist from the issue and check off as satisfied -->

## Verification

- [ ] `python3 scripts/check_synthetic_data.py` passes
- [ ] `python3 scripts/check_mcp_boundary.py` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run pytest` passes
- [ ] Independent code-review pass completed (fresh subagent, per `docs/WORKFLOW.md`)
- [ ] Docs/artifacts (`README.md`, `docs/WORKFLOW.md`, the relevant `docs/checkpoints/week-NN-*.md`) checked for staleness against this change — updated if needed
