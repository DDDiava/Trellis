# Task System

Trellis tracks work in task directories under `.trellis/tasks/`.

---

## Directory Structure

```
.trellis/tasks/
├── {MM-DD-slug}/
│   ├── task.json
│   ├── prd.md
│   ├── info.md
│   ├── implement.jsonl
│   ├── check.jsonl
│   └── research/
└── archive/
    └── {YYYY-MM}/
```

---

## Task JSON

Canonical fields include:

```json
{
  "id": "add-login",
  "name": "add-login",
  "title": "Add login",
  "description": "",
  "status": "planning",
  "dev_type": null,
  "scope": null,
  "package": null,
  "priority": "P2",
  "creator": "taosu",
  "assignee": "taosu",
  "createdAt": "2026-04-26",
  "completedAt": null,
  "branch": null,
  "base_branch": null,
  "worktree_path": null,
  "commit": null,
  "pr_url": null,
  "pr_number": null,
  "pr_status": "none",
  "review_status": "none",
  "ci_status": "unknown",
  "issue_url": "",
  "milestone": "",
  "labels": [],
  "reviewers": [],
  "merge_strategy": "squash",
  "integration_branch": "",
  "last_pr_sync_at": "",
  "last_agent_review_at": "",
  "validation": {
    "lint": "unknown",
    "typecheck": "unknown",
    "test": "unknown",
    "build": "unknown"
  },
  "subtasks": [],
  "children": [],
  "parent": null,
  "relatedFiles": [],
  "notes": "",
  "meta": {}
}
```

Readers must preserve unknown fields when writing task metadata.

---

## Requirements Files

| File | Purpose |
|------|---------|
| `prd.md` | Requirements, acceptance criteria, decisions, non-goals |
| `info.md` | Optional technical design notes |
| `research/*.md` | Persisted research artifacts |

---

## JSONL Context Files

JSONL manifests list files that sub-agents or main-session workflows must read before writing/checking code.

```jsonl
{"file": ".trellis/spec/cli/backend/index.md", "reason": "Backend guidelines"}
{"file": ".trellis/tasks/04-25-example/research/api.md", "reason": "API research"}
```

Rows without a `file` field are seed/example rows and are skipped.

Use:

```bash
python3 ./.trellis/scripts/task.py add-context <task> implement <path> "reason"
python3 ./.trellis/scripts/task.py validate <task>
python3 ./.trellis/scripts/task.py list-context <task>
```

`task.py init-context` is removed. Phase 1.3 requires AI-curated JSONL entries.

---

## Parent and Child Tasks

Parallel work uses parent/child relationships:

```bash
python3 ./.trellis/scripts/task.py create "Parent effort" --slug parent
python3 ./.trellis/scripts/task.py create "Child work item" --slug child --parent parent
```

The parent records shared contracts, ownership, dependencies, and integration notes. Each child owns its implementation branch/worktree and draft PR.

---

## PR-First Commands

```bash
python3 ./.trellis/scripts/task.py worktree <task> --dry-run
python3 ./.trellis/scripts/task.py worktree <task>
python3 ./.trellis/scripts/task.py create-pr <task> --draft
python3 ./.trellis/scripts/task.py sync-pr <task>
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

Archive tasks after the PR is merged or after the user explicitly confirms local-only completion.

---

## Best Practices

- Keep PRDs specific and testable.
- Keep JSONL entries to specs and research, not implementation code files.
- Use child tasks for parallel work and review boundaries.
- Use separate branches/worktrees for independent workers.
- Do not archive before merge by default.
