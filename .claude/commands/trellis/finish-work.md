# Finish Work

Prepare the current Trellis task for PR review.

## Step 1: Final Quality Gate

Run the Phase 3 verification path before changing PR state:

- `trellis-check` for spec compliance, lint, type-check, and tests
- `trellis-update-spec` when this task produced reusable project knowledge

Do not continue until failures are fixed or clearly documented.

## Step 2: Prepare Or Update The PR

Inspect the current task and branch state:

```bash
git status --short
python3 ./.trellis/scripts/task.py list --mine
```

If there is no task branch/worktree metadata yet, prepare it:

```bash
python3 ./.trellis/scripts/task.py worktree <task-name> --dry-run
```

Create or stage the PR body:

```bash
python3 ./.trellis/scripts/task.py create-pr <task-name> --draft
```

If a PR already exists, refresh metadata and replace only the Trellis-managed body section:

```bash
python3 ./.trellis/scripts/task.py sync-pr <task-name>
```

## Step 3: Agent Review Artifact

Create a local review artifact for the human reviewer:

```bash
python3 ./.trellis/scripts/task.py review-pr <task-name>
```

Then mark the PR ready for human review when CI/review metadata allows:

```bash
python3 ./.trellis/scripts/task.py finish-pr <task-name>
```

## Step 4: Human Handoff

Tell the user:

> "The PR is prepared for human review. Please review, push/merge as appropriate, then run `/finish-work` again after merge so I can reconcile the local base branch before archiving or recording the session."

Do not archive by default before merge.

## Step 5: Post-Merge Reconcile

Run this only after the PR is merged, or after the user explicitly confirms local-only completion. Use the PR base branch or `task.json.base_branch`; this is usually `main`.

```bash
git fetch origin
git branch --show-current
git status --short --branch
```

Confirm the current workspace is on `<base-branch>`. Inspect `git status --short --branch` before pulling. Local untracked or dirty files are a blocker requiring backup, commit, stash, or a user decision before pull.

Only when the workspace is on the base branch and clean:

```bash
git pull --ff-only origin <base-branch>
git status --short --branch
git rev-parse <base-branch>
git rev-parse origin/<base-branch>
```

Verify both `git rev-parse` commands print the same commit SHA. Do not archive or record the session until the local base branch matches `origin/<base-branch>`.

## Step 6: Archive And Record

After post-merge reconcile is clean and current, archive and record the session:

```bash
python3 ./.trellis/scripts/task.py archive <task-name>
python3 ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "merge-or-final-commit" \
  --summary "Brief summary"
```
