# Historical worktree.yaml Reference

`worktree.yaml` is historical. Current Trellis worktree behavior is configured through `task.py worktree` flags and task metadata, not through `.trellis/worktree.yaml`.

Do not add `worktree.yaml` to new guidance unless the implementation restores a reader for it.

---

## Current Worktree Configuration

Use command flags when creating a task worktree:

```bash
python3 ./.trellis/scripts/task.py worktree <task> \
  --base <base-branch> \
  --branch task/<task-slug> \
  --path ../trellis-worktrees/<task-slug>
```

Defaults:

| Value | Source order |
|-------|--------------|
| Base branch | `--base`, then `task.base_branch`, then current branch |
| Branch | `--branch`, then `task/<task-slug>` |
| Path | `--path`, then `../trellis-worktrees/<task-slug>` |

After successful execution, Trellis records:

- `branch`
- `base_branch`
- `worktree_path`

Dry runs print the planned git command and do not mutate metadata.

---

## Current Parallel Setup Pattern

```bash
python3 ./.trellis/scripts/task.py create "<child goal>" --slug <child-task> --parent <parent-task>
python3 ./.trellis/scripts/task.py worktree <child-task> --dry-run
python3 ./.trellis/scripts/task.py worktree <child-task>
```

For local files such as `.env`, copy them manually or document setup steps in the child task's `info.md`. Trellis no longer reads a `copy` list or `post_create` list from `worktree.yaml`.

---

## Current Validation Pattern

Validation commands are explicit workflow steps, agent instructions, CI, or evidence stored in task metadata/PR body. Common commands:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Record results in the task's validation evidence and keep the PR body updated:

```bash
python3 ./.trellis/scripts/task.py sync-pr <task>
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

---

## Removed Configuration Mapping

| Historical key | Current replacement |
|----------------|---------------------|
| `worktree_dir` | `task.py worktree --path` |
| `copy` | Manual setup notes in `info.md` or repo-specific scripts |
| `post_create` | Manual setup commands in the worker plan |
| `verify` | Explicit validation commands, check agent instructions, CI evidence |

---

## Historical Context

Old documentation described `.trellis/worktree.yaml` as shared configuration for multi-session worktrees and Ralph Loop. That architecture was removed with the legacy multi-agent pipeline. The active PR-first workflow uses task metadata and command flags instead.
