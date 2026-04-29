# Finish Work

Prepare or complete the current Trellis task's PR-first handoff. Code commits are handled in workflow Phase 3.4 before this command archives anything.

## Step 1: Survey Current State

```bash
{{PYTHON_CMD}} ./.trellis/scripts/get_context.py --mode record
```

This prints active tasks, git status, and recent commits. Use the recent work-commit hashes later for `add_session.py --commit`.

If other completed-but-unarchived tasks appear, ask once whether to include them in this cleanup round. Default is no.

## Step 2: Sanity Check Code Is Committed

Run:

```bash
git status --porcelain
```

Filter out paths under `.trellis/workspace/` and `.trellis/tasks/`; those are managed by archive/journal scripts. If anything else is dirty, stop with:

> "Working tree has uncommitted code changes. Return to workflow Phase 3.4 to commit them before running `{{CMD_REF:finish-work}}`."

Do not run `git commit` here. Do not prompt for an ad hoc commit from this command.

## Step 3: Prepare Or Update The PR

If the task PR is not ready for human review yet, prepare it now:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py create-pr <task-name> --draft
{{PYTHON_CMD}} ./.trellis/scripts/task.py sync-pr <task-name>
{{PYTHON_CMD}} ./.trellis/scripts/task.py review-pr <task-name>
{{PYTHON_CMD}} ./.trellis/scripts/task.py finish-pr <task-name>
```

If GitHub CLI or authentication is unavailable, keep the local fallback artifacts (`pr-body.md`, `review/pr-review-*.md`, task metadata, and manual push/PR commands) and report them to the user.

If the PR is prepared but not merged, stop here and tell the user:

> "The PR is ready for human review. Merge it, then run `{{CMD_REF:finish-work}}` again so I can reconcile the local base branch before archiving or journaling."

Do not archive by default before merge. Do not archive before merge unless the user explicitly confirms local-only completion.

## Step 4: Post-Merge Reconcile

Run this only after the user says the PR was merged, or explicitly confirms local-only completion. Use the PR base branch or `task.json.base_branch`; this is usually `main`.

```bash
git fetch origin
git branch --show-current
git status --short --branch
```

Confirm the current workspace is on `<base-branch>`. Local untracked or dirty files are a blocker; ask the user whether to back up, commit, stash, or stop.

Only when the base workspace is clean and on the base branch:

```bash
git pull --ff-only origin <base-branch>
git status --short --branch
git rev-parse <base-branch>
git rev-parse origin/<base-branch>
```

Verify the local and origin SHAs match. Do not archive or record the session until the local base branch matches `origin/<base-branch>`. For parallel child PRs, verify each child merge commit is an ancestor of the base branch before cleaning up child worktrees or branches.

## Step 5: Archive Task(s)

After post-merge reconcile is clean and current:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py archive <task-name>
```

Archive the current active task plus any extra tasks the user confirmed in Step 1. Each archive produces a `chore(task): archive ...` commit through the script's auto-commit.

## Step 6: Record Session Journal

```bash
{{PYTHON_CMD}} ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary"
```

Use the work-commit hashes produced in Phase 3.4. Do not include archive commit hashes from Step 5. Final git log order: work commits -> archive commit(s) -> `chore: record journal`.
