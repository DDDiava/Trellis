# Claude Code Script Reference

Claude Code uses the same Trellis task scripts as every other platform. Current PR-first work is coordinated through `task.py` and shared helpers, not through the removed `multi_agent/` directory.

---

## Current Script Surface

```
.trellis/scripts/
├── get_context.py
├── init_developer.py
├── get_developer.py
├── add_session.py
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

## PR-First Commands

### Create or Prepare an Isolated Worktree

```bash
python3 ./.trellis/scripts/task.py worktree <task> --dry-run
python3 ./.trellis/scripts/task.py worktree <task>
```

Defaults:

- base branch: `--base`, then `task.base_branch`, then current branch
- branch: `task/<task-slug>`
- path: `../trellis-worktrees/<task-slug>`

The command updates `branch`, `base_branch`, and `worktree_path` only after successful execution. Dry runs do not mutate task metadata.

### Open or Stage a Draft PR

```bash
python3 ./.trellis/scripts/task.py create-pr <task> --draft
```

This command generates a Trellis PR body from `prd.md`, `info.md`, task metadata, validation evidence, reviewer focus, agent review, and risk/rollback notes. It uses `gh` when available and leaves local fallback artifacts and manual commands when GitHub is unavailable.

### Sync, Review, and Finish PR Handoff

```bash
python3 ./.trellis/scripts/task.py sync-pr <task>
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

- `sync-pr` refreshes PR metadata/body and preserves human-written body content outside Trellis markers.
- `review-pr` writes local review artifacts under the task directory.
- `finish-pr` gates ready-for-human-review status on available review/CI information.

---

## Parallel Worker Handoff

Each parallel child task owns its branch/worktree and draft PR:

```bash
git status
git add -A
git commit -m "<task-slug>: <summary>"
git push -u origin <branch>
python3 ./.trellis/scripts/task.py create-pr <child-task> --draft
python3 ./.trellis/scripts/task.py sync-pr <child-task>
python3 ./.trellis/scripts/task.py review-pr <child-task>
python3 ./.trellis/scripts/task.py finish-pr <child-task>
```

When remote push or `gh` is unavailable, keep the local branch, generated PR body, review artifact, and exact manual commands in the child task directory.

---

## Historical Removed Scripts

The following paths were removed and must not be used as active instructions:

| Removed path | Replacement |
|--------------|-------------|
| `.trellis/scripts/multi_agent/plan.py` | Phase 1 PRD/research/context workflow |
| `.trellis/scripts/multi_agent/start.py` | `task.py worktree <task>` |
| `.trellis/scripts/multi_agent/status.py` | `task.py list`, `git worktree list`, platform UI |
| `.trellis/scripts/multi_agent/create_pr.py` | `task.py create-pr <task> --draft` |
| `.trellis/scripts/multi_agent/cleanup.py` | `git worktree remove` and archive after merge |
| `.trellis/scripts/common/worktree.py` | `common/task_pr.py` worktree helpers |
| `.trellis/scripts/common/registry.py` | Git/platform state and task metadata |
| `.trellis/worktree.yaml` | `task.py worktree` flags and task metadata |

Historical migration notes may mention these names only when clearly labeled as removed.
