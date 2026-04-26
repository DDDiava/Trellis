# Trellis Local Skill Template

Copy this template to create a project-specific `trellis-local` skill.

---

## Template

```markdown
---
name: trellis-local
description: |
  Project-specific Trellis customizations for [PROJECT_NAME].
  This skill documents modifications made to the vanilla Trellis system.
  Use trellis-meta for base architecture documentation.
---

# Trellis Local - [PROJECT_NAME]

## Base Information

| Field | Value |
|-------|-------|
| Trellis Version | X.X.X |
| Date Initialized | YYYY-MM-DD |
| Last Updated | YYYY-MM-DD |

---

## Customizations Summary

- **Commands**: X added, Y modified
- **Agents**: X added, Y modified
- **Hooks**: X modified
- **Specs**: X categories added
- **Workflow**: [summary]
- **PR/Parallel Flow**: [summary]

---

## Commands

### Added Commands

(none yet)

### Modified Commands

(none yet)

---

## Agents

### Added Agents

(none yet)

### Modified Agents

(none yet)

---

## Hooks

### Modified Hooks

(none yet)

---

## Specs

### Added Categories

(none yet)

### Modified Specs

(none yet)

---

## Workflow Changes

### Task and PR Flow

<!-- Example:
#### Parallel PR-first handoff
- **What**: Parent task plus child tasks, separate worktrees, separate draft PRs.
- **Files Affected**: [...]
- **Date**: YYYY-MM-DD
- **Reason**: [...]
-->

(none yet)

### Context JSONL

<!-- Example:
#### implement.jsonl/check.jsonl curation
- **Change**: Added spec/research entries.
- **Date**: YYYY-MM-DD
-->

(none yet)

---

## Local Setup Notes

Document project-specific setup required in branch/worktree workers, such as copying `.env`, installing dependencies, or running migrations. Current Trellis does not use `worktree.yaml`.

(none yet)

---

## Historical Removed References

If this project still contains old customizations for removed Trellis mechanisms, document them here as historical and record the replacement:

- `task.py init-context` -> curated JSONL / `task.py add-context`
- `.trellis/scripts/multi_agent/*.py` -> `task.py worktree` + platform worker + PR commands
- `.trellis/worktree.yaml` -> task metadata and command flags
- `common/registry.py` / `common/worktree.py` -> current helpers under `common/task_pr.py`

---

## Changelog

### YYYY-MM-DD - Initial Setup
- Initialized trellis-local skill
- Base Trellis version: X.X.X

---

## Migration Notes

(none yet)

---

## Known Issues

(none yet)
```

---

## Creation Steps

1. Create `.claude/skills/trellis-local/` or `.agents/skills/trellis-local/`.
2. Add `SKILL.md` from the template above.
3. Fill base information.
4. Record customizations as they happen.
