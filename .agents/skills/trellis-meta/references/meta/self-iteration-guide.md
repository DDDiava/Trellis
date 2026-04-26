# Trellis Self-Iteration Guide

How to maintain skill documentation when customizing Trellis.

---

## Core Principle

Every Trellis modification should be documented in the right skill:

```
Project-specific customization -> trellis-local
Vanilla Trellis documentation fix -> trellis-meta
```

---

## Decision Tree

```
Is this a project-specific Trellis customization?
  yes -> update .claude/skills/trellis-local/ or .agents/skills/trellis-local/
  no
    Is this vanilla Trellis documentation or template behavior?
      yes -> update trellis-meta and installable templates as needed
      no -> no skill update needed
```

---

## Documenting a Change

Record:

- what changed
- why it changed
- files affected
- platform scope
- validation run
- migration or rollback notes

---

## Workflow Change Template

```markdown
#### PR-first child task handoff
- **What**: Added child task branch/worktree + draft PR handoff.
- **Files Affected**:
  - `.trellis/workflow.md`
  - `.claude/commands/trellis/parallel.md`
  - `packages/cli/src/templates/...`
- **Date**: YYYY-MM-DD
- **Reason**: Parallel work should produce separate reviewable PRs.

**Validation**:
- `pnpm test packages/cli/test/templates/pr-first-workflow.test.ts`
```

---

## Agent Change Template

```markdown
#### my-agent
- **File**: `.claude/agents/my-agent.md`
- **Purpose**: What this agent specializes in
- **Context**: `my-agent.jsonl`
- **Added**: YYYY-MM-DD
- **Reason**: Why it was needed
```

---

## Context Manifest Change Template

```markdown
#### Context curation
- **Files**:
  - `.trellis/tasks/<task>/implement.jsonl`
  - `.trellis/tasks/<task>/check.jsonl`
- **Change**: Added spec/research entries for the task.
- **Reason**: Phase 1.3 requires curated context before implementation.
```

Do not document new context by saying `task.py init-context` was modified; that command is removed.

---

## Historical Removed Items

If a customization touches old names, mark them as historical/removed:

- `task.py init-context`
- `.trellis/scripts/multi_agent/*.py`
- `.trellis/worktree.yaml`
- `common/registry.py`
- `common/worktree.py`
- `.claude/hooks/ralph-loop.py`

Do not present these as active extension points.

---

## Upgrade Workflow

When upgrading Trellis:

1. Compare current and new meta-skill references.
2. Check `trellis-local` customizations for conflicts.
3. Merge carefully, preserving local changes.
4. Update `trellis-local` migration notes.
5. Run a stale-reference scan for removed APIs/scripts.

Example scan:

```bash
rg -n "multi_agent|task.py init-context|worktree.yaml|common/(registry|worktree).py" .claude .agents packages/cli/src/templates
```
