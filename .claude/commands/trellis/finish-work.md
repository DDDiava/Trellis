# Finish Work

Prepare or complete the current Trellis task's PR-first handoff. Code commits are handled in workflow Phase 3.4 before this command archives anything.

## Step 1: Survey Current State

```bash
python ./.trellis/scripts/get_context.py --mode record
```

This prints active tasks, git status, and recent commits. Use the recent work-commit hashes later for `add_session.py --commit`.

If other completed-but-unarchived tasks appear, ask once whether to include them in this cleanup round. Default is no.

If `--mode record` surfaces other completed tasks not tied to the current session, surface them to the user with a one-shot confirmation: "These N tasks look done — archive them too in this round? [y/N]". Default is no; the current active task is always archived in Step 3 regardless.

## Step 2: Sanity check — classify dirty paths

Run:

```bash
git status --porcelain
```

Filter out paths under `.trellis/workspace/` and `.trellis/tasks/` — those are managed by `add_session.py` and `task.py archive` auto-commits and will appear dirty as part of this skill's own work.

For each remaining dirty path, decide whether it belongs to **the current task** or to **other parallel work** (e.g., another terminal window editing the same repo). Heuristics:

- Paths referenced in the current task's `prd.md` / `implement.jsonl` / `check.jsonl` → current task
- Paths in code areas matching the task's stated scope, or that you remember editing this session → current task
- Paths in unrelated areas you have no recollection of touching this session → other parallel work

Then route:

- **Any remaining path looks like current-task work** — bail out with:
  > "Working tree has uncommitted code changes from this task: `<list>`. Return to workflow Phase 3.4 to commit them before running `/trellis:finish-work`."

  Do NOT run `git commit` here. Do NOT prompt the user to commit. The user goes back to Phase 3.4 and the AI drives the batched commit there.
- **All remaining paths look unrelated** (other parallel-window work) — report them once and continue to Step 3:
  > "FYI, dirty files outside this task's scope — leaving them for the other window: `<list>`."
- **Genuinely unsure** — ask the user once: "Are `<list>` this task's work I forgot to commit, or another window's? (commit / ignore)" — then route per their answer.

## Step 3: Prepare Or Update The PR

If the task PR is not ready for human review yet, prepare it now:

```bash
python ./.trellis/scripts/task.py create-pr <task-name> --draft
python ./.trellis/scripts/task.py sync-pr <task-name>
python ./.trellis/scripts/task.py review-pr <task-name>
python ./.trellis/scripts/task.py finish-pr <task-name>
```

If GitHub CLI or authentication is unavailable, keep the local fallback artifacts (`pr-body.md`, `review/pr-review-*.md`, task metadata, and manual push/PR commands) and report them to the user.

If the PR is prepared but not merged, stop here and tell the user:

> "The PR is ready for human review. Merge it, then run `/trellis:finish-work` again so I can reconcile the local base branch before archiving or journaling."

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
python ./.trellis/scripts/task.py archive <task-name>
```

Archive the current active task plus any extra tasks the user confirmed in Step 1. Each archive produces a `chore(task): archive ...` commit through the script's auto-commit.

## Step 6: Record Session Journal

```bash
python ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary"
```

Use the work-commit hashes produced in Phase 3.4. Do not include archive commit hashes from Step 5. Final git log order: work commits -> archive commit(s) -> `chore: record journal`.
