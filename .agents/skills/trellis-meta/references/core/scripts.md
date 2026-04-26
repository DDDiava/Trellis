# Core Scripts

Platform-independent Python scripts for Trellis automation.

---

## Script Tree

```
.trellis/scripts/
├── add_session.py
├── get_context.py
├── get_developer.py
├── init_developer.py
├── task.py
└── common/
    ├── cli_adapter.py
    ├── config.py
    ├── developer.py
    ├── git.py
    ├── io.py
    ├── log.py
    ├── packages_context.py
    ├── paths.py
    ├── session_context.py
    ├── task_context.py
    ├── task_pr.py
    ├── task_queue.py
    ├── task_store.py
    ├── task_utils.py
    ├── tasks.py
    ├── types.py
    └── workflow_phase.py
```

---

## Developer Scripts

```bash
python3 ./.trellis/scripts/init_developer.py <name>
python3 ./.trellis/scripts/get_developer.py
python3 ./.trellis/scripts/add_session.py "Session summary"
```

---

## Context Script

```bash
python3 ./.trellis/scripts/get_context.py
python3 ./.trellis/scripts/get_context.py --mode packages
python3 ./.trellis/scripts/get_context.py --mode phase --step 2.1
python3 ./.trellis/scripts/get_context.py --json
```

`get_context.py` is the standard read path for session context, package/spec discovery, and phase guidance.

---

## Task Script

### Task Lifecycle

```bash
python3 ./.trellis/scripts/task.py create "Task name" --slug task-slug
python3 ./.trellis/scripts/task.py create "Child task" --slug child --parent <parent-task>
python3 ./.trellis/scripts/task.py start <task>
python3 ./.trellis/scripts/task.py finish
python3 ./.trellis/scripts/task.py list
python3 ./.trellis/scripts/task.py archive <task>
```

### Context JSONL

```bash
python3 ./.trellis/scripts/task.py add-context <task> implement <path> "reason"
python3 ./.trellis/scripts/task.py add-context <task> check <path> "reason"
python3 ./.trellis/scripts/task.py validate <task>
python3 ./.trellis/scripts/task.py list-context <task>
```

`task.py init-context` was removed. Phase 1.3 is now AI-curated: edit JSONL directly or use `add-context`.

### Branch, Worktree, and PR

```bash
python3 ./.trellis/scripts/task.py set-branch <task> <branch>
python3 ./.trellis/scripts/task.py set-base-branch <task> <branch>
python3 ./.trellis/scripts/task.py set-scope <task> <scope>
python3 ./.trellis/scripts/task.py worktree <task> --dry-run
python3 ./.trellis/scripts/task.py worktree <task>
python3 ./.trellis/scripts/task.py create-pr <task> --draft
python3 ./.trellis/scripts/task.py sync-pr <task>
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

---

## PR-First Helpers

`common/task_pr.py` owns:

- worktree planning and metadata update
- PR body generation
- Trellis-managed PR body section replacement
- GitHub CLI integration where available
- local-only fallback artifacts
- `sync-pr`, `review-pr`, and `finish-pr` behavior

---

## Historical Removed Scripts

These names are removed and should only appear in migration notes:

| Removed item | Replacement |
|--------------|-------------|
| `task.py init-context` | Phase 1.3 curated JSONL + `task.py add-context` |
| `.trellis/scripts/multi_agent/*.py` | Parent/child tasks, `task.py worktree`, platform workers |
| `common/registry.py` | Task metadata, git state, platform session UI |
| `common/worktree.py` | `common/task_pr.py` |
| `.trellis/worktree.yaml` | `task.py worktree` flags and task metadata |

---

## Usage Example

```bash
python3 ./.trellis/scripts/task.py create "Add login" --slug add-login
python3 ./.trellis/scripts/task.py add-context add-login implement .trellis/spec/cli/backend/index.md "Backend guidelines"
python3 ./.trellis/scripts/task.py start add-login
python3 ./.trellis/scripts/task.py worktree add-login --dry-run
python3 ./.trellis/scripts/task.py create-pr add-login --draft
```
