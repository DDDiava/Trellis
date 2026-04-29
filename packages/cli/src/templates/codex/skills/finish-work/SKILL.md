---
name: finish-work
description: "Prepare the current Trellis task for PR review, or after merge reconcile the base branch, archive the task, and record the session. Use when code is written and needs PR handoff or final post-merge cleanup."
---

# Finish Work

Prepare or complete the current Trellis task's PR-first handoff. Code commits are handled in workflow Phase 3.4 before this skill archives anything.

## Step 1: Survey Current State

```bash
python3 ./.trellis/scripts/get_context.py --mode record
```

Use active tasks, git status, and recent commits from the output. If other completed-but-unarchived tasks appear, ask once whether to include them in this cleanup round. Default is no.

## Step 2: Sanity Check Code Is Committed

Run `git status --porcelain`. Ignore `.trellis/workspace/` and `.trellis/tasks/`; those are managed by archive/journal scripts. If anything else is dirty, stop and send the user back to workflow Phase 3.4. Do not commit from this skill.

## Step 3: Prepare Or Update The PR

If the task PR is not ready for human review yet:

```bash
python3 ./.trellis/scripts/task.py create-pr <task-name> --draft
python3 ./.trellis/scripts/task.py sync-pr <task-name>
python3 ./.trellis/scripts/task.py review-pr <task-name>
python3 ./.trellis/scripts/task.py finish-pr <task-name>
```

If GitHub CLI or authentication is unavailable, keep the local fallback artifacts (`pr-body.md`, `review/pr-review-*.md`, task metadata, and manual push/PR commands) and report them to the user. If the PR is prepared but not merged, stop and tell the user to merge it, then run `$finish-work` again so post-merge reconcile can happen before archive/journal.

Do not archive by default before merge. Do not archive before merge unless the user explicitly confirms local-only completion.

## Step 4: Post-Merge Reconcile

Run this only after the user says the PR was merged, or explicitly confirms local-only completion:

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

Verify local and origin SHAs match. Do not archive or record the session until the local base branch matches `origin/<base-branch>`. For parallel child PRs, verify each child merge commit is an ancestor of the base branch before cleaning up child worktrees or branches.

## Step 5: Archive And Journal

After reconcile is clean and current:

```bash
python3 ./.trellis/scripts/task.py archive <task-name>
python3 ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary"
```

Use Phase 3.4 work-commit hashes for `--commit`; do not include archive commit hashes.
