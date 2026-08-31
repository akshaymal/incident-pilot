#!/usr/bin/env bash
set -euo pipefail

# One-time setup. Requires `gh auth login` first (see docs/WORKFLOW.md).

declare -A LABELS=(
  ["type:feature"]="0E8A16"
  ["type:chore"]="C5DEF5"
  ["type:bug"]="D93F0B"
  ["priority:p1"]="B60205"
  ["priority:p2"]="D93F0B"
  ["priority:p3"]="FBCA04"
  ["area:agent"]="5319E7"
  ["area:mcp"]="0052CC"
  ["area:memory"]="006B75"
  ["area:sandbox"]="B60205"
  ["area:observability"]="1D76DB"
  ["area:audit"]="5C2D91"
  ["area:ui"]="0E8A16"
  ["area:infra"]="795548"
  ["area:docs"]="BFD4F2"
  ["agent-ready"]="0E8A16"
)

for name in "${!LABELS[@]}"; do
  color="${LABELS[$name]}"
  gh label create "$name" --color "$color" --force
done

echo "Labels created/updated."
