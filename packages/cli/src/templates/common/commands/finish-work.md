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
{{PYTHON_CMD}} ./.trellis/scripts/task.py list --mine
```

If there is no task branch/worktree metadata yet, prepare it:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py worktree <task-name> --dry-run
```

Create or stage the PR body:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py create-pr <task-name> --draft
```

If a PR already exists, refresh metadata and replace only the Trellis-managed body section:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py sync-pr <task-name>
```

## Step 3: Agent Review Artifact

Create a local review artifact for the human reviewer:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py review-pr <task-name>
```

Then mark the PR ready for human review when CI/review metadata allows:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py finish-pr <task-name>
```

## Step 4: Human Handoff

Tell the user:

> "The PR is prepared for human review. Please review, push/merge as appropriate, then run `/finish-work` again after merge if you want to archive and record the session."

Do not archive by default before merge. After the PR is merged and the user confirms the task is done, archive and record the session:

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py archive <task-name>
{{PYTHON_CMD}} ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "merge-or-final-commit" \
  --summary "Brief summary"
```
