# Parallel PR Workflow Orchestrator

You are the parallel-work orchestrator in the main repository. Your job is to turn a multi-part request into multiple reviewable Trellis child tasks, each with its own branch, worktree, worker, and draft PR.

Use your platform Python command (`python` on Windows, `python3` elsewhere). Examples below use `python3`.

---

## Core Contract

- Model parallel development like multiple employees working at the same time.
- Create one parent coordination task when useful, then one child task per independently reviewable work item.
- Give every child task a distinct branch, worktree path, worker, and draft PR.
- Dispatch workers concurrently when their ownership/dependency plan allows it.
- Do not refuse or silently serialize just because shared scaffolding, interfaces, logging, generated files, or templates could conflict.
- Resolve possible conflicts with explicit ownership and contracts: name the shared contract, assign one writer, list consumers, and record dependencies.
- Use a short prerequisite scaffold task only when no child worker can make progress independently.
- Do not use removed context-initialization commands.
- Do not call removed pipeline helper scripts.

---

## Startup Flow

Read the current project state and workflow:

```bash
python3 ./.trellis/scripts/get_context.py
python3 ./.trellis/scripts/get_context.py --mode phase
python3 ./.trellis/scripts/get_context.py --mode packages
```

Read `.trellis/workflow.md` on demand for step detail. If requirements are unclear, use the normal brainstorm flow and persist decisions to `prd.md`.

---

## Planning Flow

### 1. Create Or Select The Parent Task

Use an existing task if one already represents the overall effort. Otherwise create a parent task:

```bash
python3 ./.trellis/scripts/task.py create "<overall goal>" --slug <parent-task>
```

The parent task should hold the coordination PRD, the decomposition, and the ownership/dependency plan.

### 2. Decompose Into Child Tasks

Create one child task per independently reviewable work item:

```bash
python3 ./.trellis/scripts/task.py create "<child goal>" --slug <child-task> --parent <parent-task>
```

Each child PRD must include:

- Goal and acceptance criteria.
- Owned files or modules.
- Explicit non-owned files/modules.
- Shared contracts consumed or produced.
- Dependencies on other child tasks, if any.
- Validation commands expected from the worker.
- Reviewer focus for the child PR.

### 3. Write The Ownership/Dependency Plan

Record the plan in the parent `prd.md` or `info.md` before dispatch:

| Child task | Branch | Worktree | Owner | Write scope | Shared contract | Depends on | PR focus |
|---|---|---|---|---|---|---|---|
| `<child-a>` | `task/<child-a>` | `../trellis-worktrees/<child-a>` | worker A | files/modules | interface/schema | none | review focus |

The default outcome is still multiple child branches and PRs. If a shared scaffold must be created first, make that scaffold its own child task with the smallest viable contract and mark dependent children explicitly.

### 4. Curate Context For Each Child

`implement.jsonl` and `check.jsonl` are seeded by `task.py create`. Add real spec/research entries for each child:

```bash
python3 ./.trellis/scripts/task.py add-context <child-task> implement "<path>" "<reason>"
python3 ./.trellis/scripts/task.py add-context <child-task> check "<path>" "<reason>"
python3 ./.trellis/scripts/task.py validate <child-task>
```

Skip seed rows without a `file` field. Do not run the removed context initializer.

### 5. Prepare Branches And Worktrees

Dry-run first, then create one isolated worktree per child:

```bash
python3 ./.trellis/scripts/task.py worktree <child-task> --base <base-branch> --branch task/<child-task> --path ../trellis-worktrees/<child-task> --dry-run
python3 ./.trellis/scripts/task.py worktree <child-task> --base <base-branch> --branch task/<child-task> --path ../trellis-worktrees/<child-task>
```

If task scaffolding was created only in the main worktree, make sure the child task directory and curated context are present in the worker worktree before dispatch. Do this deliberately as part of that child branch, not by sharing one mutable task directory across workers.

---

## Worker Dispatch

Dispatch one worker per child task. The worker prompt must include:

```text
You own <child-task> in <worktree-path> on branch task/<child-task>.

1. Work only in that worktree and branch.
2. Read <child-task>/prd.md, info.md if present, implement.jsonl, check.jsonl, and referenced files.
3. Run the implement flow, then the check flow.
4. Respect the ownership/dependency plan. Do not edit non-owned files unless you update the plan and explain why.
5. Run the child task's validation commands.
6. Commit your changes on task/<child-task>.
7. Push the branch when a remote is configured.
8. Run:
   python3 ./.trellis/scripts/task.py create-pr <child-task> --draft
   python3 ./.trellis/scripts/task.py sync-pr <child-task>
   python3 ./.trellis/scripts/task.py review-pr <child-task>
   python3 ./.trellis/scripts/task.py finish-pr <child-task>
9. If gh or authentication is unavailable, keep going in local-only mode and leave pr-body.md, review/pr-review-*.md, updated task metadata, and exact manual push/PR commands.
10. Stop with the child PR ready for human review, not just with local implementation complete.
```

Do not replace these handoff steps with a vague "finish later" instruction.

---

## Worker Handoff Checklist

Every parallel worker must finish with these commands or a clear local fallback:

```bash
git status
git add -A
git commit -m "<child-task>: <summary>"
git push -u origin task/<child-task>   # when a remote is configured
python3 ./.trellis/scripts/task.py create-pr <child-task> --draft
python3 ./.trellis/scripts/task.py sync-pr <child-task>
python3 ./.trellis/scripts/task.py review-pr <child-task>
python3 ./.trellis/scripts/task.py finish-pr <child-task>
```

Expected artifacts per child:

- Branch `task/<child-task>`.
- Worktree path recorded in `task.json`.
- Local commit on that branch.
- Draft PR or local-only PR body fallback.
- `pr-body.md` when GitHub is unavailable or a body file was generated.
- `review/pr-review-*.md` from `review-pr`.
- Task metadata showing PR/review status.

---

## Parent Post-Merge Reconcile

After all child PRs are merged, reconcile the parent/main workspace before archiving tasks or cleaning up worker state:

```bash
git fetch origin
git branch --show-current
git status --short --branch
```

Confirm the current workspace is on `<base-branch>` (usually `main`). Inspect `git status --short --branch` before pulling. Local untracked or dirty files are a blocker requiring backup, commit, stash, or a user decision before pull.

Only when the parent/main workspace is on the base branch and clean:

```bash
git pull --ff-only origin <base-branch>
git status --short --branch
git rev-parse <base-branch>
git rev-parse origin/<base-branch>
```

Verify both `git rev-parse` commands print the same commit SHA, then verify every child PR merge commit is present locally:

```bash
git merge-base --is-ancestor <child-merge-sha> <base-branch>
```

Clean up merged child worktrees and branches only after the local base is current and clean:

```bash
git worktree remove <worktree-path>
git branch -d task/<child-task>
git rev-parse --show-toplevel
git branch --show-current
```

Report the directory and branch that now contain the final current state.

---

## Monitoring And Reporting

Use normal git and task status commands; there is no legacy pipeline status script:

```bash
git worktree list
git branch --list "task/*"
python3 ./.trellis/scripts/task.py list
```

Report progress by child task:

- Running: worker, branch, worktree, owned scope.
- Blocked: dependency or contract question.
- Ready for review: PR URL or local fallback artifact path.
- Post-merge reconciled: final current-state directory and branch.
- Needs attention: conflict, failed validation, missing auth, or dependency change.

Human review should happen per child PR. Merge/archive only after the PR is merged or the user explicitly confirms local-only completion, and archive only after the parent/main workspace has completed post-merge reconcile.
