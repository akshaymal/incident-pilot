## Summary

<!-- What does this PR do and why -->

Closes #

## Acceptance criteria

<!-- Copy the acceptance criteria checklist from the issue and check off as satisfied -->

## Verification

<!-- (CI-enforced) items are re-checked by CI on this same commit — a false checkbox fails the build. (self-reported) items are this session's own claim; nothing re-runs them from the PR. -->

- [ ] `python3 scripts/check_synthetic_data.py` passes (CI-enforced)
- [ ] `python3 scripts/check_mcp_boundary.py` passes (CI-enforced)
- [ ] `uv run ruff check .` passes (CI-enforced)
- [ ] `uv run ruff format --check .` passes (CI-enforced)
- [ ] `uv run pytest` passes (CI-enforced)
- [ ] Independent code-review pass completed, including acceptance-criteria coverage (fresh subagent, per `docs/WORKFLOW.md`) (self-reported)
- [ ] Docs/artifacts (`README.md`, `docs/WORKFLOW.md`, the relevant `docs/checkpoints/week-NN-*.md`) checked for staleness against this change — updated if needed (self-reported)
