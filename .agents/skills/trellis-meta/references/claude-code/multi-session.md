# PR-First Parallel Work Reference

Current Trellis parallel work is PR-first. It uses a parent task plus child tasks, isolated branches/worktrees, and one draft PR per child for human review.

---

## Core Model

```
Parent task
  ├── Child task A -> branch/worktree A -> draft PR A
  ├── Child task B -> branch/worktree B -> draft PR B
  └── Child task C -> branch/worktree C -> draft PR C
```

The parent task coordinates scope, shared contracts, ownership, dependencies, and integration notes. Child tasks are the units that workers implement, check, commit, push, and hand off for review.

---

## When To Use

Use this workflow when:

- the user explicitly asks for parallel work
- work splits into independently reviewable child tasks
- tasks need isolated dependencies or clean working directories
- multiple workers can proceed after a shared contract is defined

Do not refuse parallel work just because shared files could conflict. First write an ownership/dependency plan. Use a prerequisite scaffold child only when workers cannot proceed without one.

---

## Planning Contract

For the parent task, record:

- child task list and review boundaries
- branch/worktree names
- owned files or modules for each child
- shared contracts: APIs, schemas, interfaces, migrations, generated files, templates
- dependencies between children
- integration branch or merge order when relevant
- validation expectations

Create child tasks with a parent link:

```bash
python3 ./.trellis/scripts/task.py create "<child goal>" --slug <child-task> --parent <parent-task>
```

Curate each child task's `implement.jsonl` and `check.jsonl` independently.

---

## Worktree Setup

Preview first:

```bash
python3 ./.trellis/scripts/task.py worktree <child-task> --dry-run
```

Create the branch/worktree:

```bash
python3 ./.trellis/scripts/task.py worktree <child-task>
```

Defaults:

- `base`: explicit `--base`, then `task.base_branch`, then current branch
- `branch`: `task/<task-slug>`
- `path`: `../trellis-worktrees/<task-slug>`

The command stores `branch`, `base_branch`, and `worktree_path` after successful creation. Dry runs do not mutate metadata.

---

## Worker Execution

Each worker runs in its assigned branch/worktree:

1. Start the child task in that worktree.
2. Run the platform's implement flow.
3. Run the platform's check flow and fix findings.
4. Run relevant lint/typecheck/test commands.
5. Commit the child branch.
6. Open or stage a draft PR.

Worker handoff commands:

```bash
git status
git add -A
git commit -m "<child-task>: <summary>"
git push -u origin task/<child-task>
python3 ./.trellis/scripts/task.py create-pr <child-task> --draft
python3 ./.trellis/scripts/task.py sync-pr <child-task>
python3 ./.trellis/scripts/task.py review-pr <child-task>
python3 ./.trellis/scripts/task.py finish-pr <child-task>
```

If a remote, `gh`, or authentication is missing, the worker keeps a local fallback: generated PR body, review artifact, task metadata, branch name, and exact manual push/PR commands.

---

## Review and Integration

Human review happens per child PR. The parent task should stay open until child PRs are reviewed and merged or intentionally abandoned.

Recommended order:

1. Review prerequisite scaffold/contract PRs first.
2. Rebase dependent child branches if shared contracts changed.
3. Merge independent PRs in any safe order.
4. Archive child tasks after merge.
5. Archive the parent task after the parallel effort is complete.

---

## Historical Removed Multi-Session Pipeline

The old script pipeline was removed. These paths are historical only:

| Removed path | Current replacement |
|--------------|---------------------|
| `.trellis/scripts/multi_agent/plan.py` | Parent/child task planning in Phase 1 |
| `.trellis/scripts/multi_agent/start.py` | `task.py worktree <child-task>` |
| `.trellis/scripts/multi_agent/status.py` | `task.py list`, `git worktree list`, platform session status |
| `.trellis/scripts/multi_agent/create_pr.py` | `task.py create-pr <child-task> --draft` |
| `.trellis/scripts/multi_agent/cleanup.py` | archive after merge plus `git worktree remove` |
| `.trellis/worktree.yaml` | command flags and task metadata |
| `common/registry.py`, `common/worktree.py` | `common/task_pr.py`, git state, task metadata |

Do not restore these names as active guidance unless the implementation restores the scripts.
