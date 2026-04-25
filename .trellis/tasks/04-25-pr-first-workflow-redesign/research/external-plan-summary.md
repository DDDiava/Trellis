# External Plan Summary

Source package: `D:/Google_download/trellis-pr-first-guides/`

## Key Decision

Implement a PR-first Trellis workflow for user projects. This is not the repository contributor workflow in `CONTRIBUTING.md`; it is the workflow Trellis installs and dogfoods through `.trellis/`, command templates, task metadata, and task scripts.

## Required MVP

- Treat a PR as the primary review/completion unit for medium and large tasks.
- Preserve commits as implementation details inside a PR.
- Extend task metadata with optional PR/worktree/review/CI fields while preserving old tasks and unknown fields.
- Add `task.py worktree <task>` with dry-run support, clear branch/path/base conflict handling, and metadata updates.
- Add `task.py create-pr <task>` with dry-run support, generated PR body, GitHub CLI integration where available, and local-only fallback where unavailable.
- Redesign `/finish-work` so it prepares or updates a PR for human review instead of centering commit review.
- Add a PR template that supports task, goal, acceptance criteria, validation evidence, reviewer focus, agent review, and rollback notes.
- Update CI so PRs targeting `feat/v0.5.0-beta` run checks, using scripts that actually exist.

## Stretch Scope If Feasible

- Add `task.py sync-pr <task>` to refresh PR metadata and update only the Trellis-managed PR body section.
- Add `task.py review-pr <task>` to export PR diff/check data and local review summaries.
- Add `task.py finish-pr <task>` to gate draft-to-ready transitions on CI/review status.
- Add `.github/release.yml` for label-based release notes.

## Non-Goals

- Do not make GitHub mandatory; local branch/worktree flows must still work.
- Do not auto-archive unmerged work by default.
- Do not rewrite Trellis architecture.
- Do not hardcode a repository owner in CODEOWNERS.
- Do not make `CONTRIBUTING.md` the centerpiece.
- Do not overwrite human-written PR body content outside `<!-- trellis:start -->` / `<!-- trellis:end -->`.

## Relevant Repo Findings

- `.trellis/scripts/task.py` and `packages/cli/src/templates/trellis/scripts/task.py` currently expose task CRUD, branch/base metadata, context JSONL, hierarchy, list, and archive commands.
- `.trellis/scripts/common/task_store.py` and the template copy seed `branch`, `base_branch`, `worktree_path`, `commit`, and `pr_url`, but not the expanded PR metadata.
- `.trellis/scripts/common/git.py` and the template copy provide only `run_git`.
- `.trellis/workflow.md` and the template copy mention `create-pr` in docs, but `task.py` does not implement it yet.
- `packages/cli/src/templates/common/commands/finish-work.md` is commit-centric and should become PR-ready-centric.
- `.github/workflows/ci.yml` currently targets only `main`; root `package.json` has `lint`, `typecheck`, `test`, and `build` scripts.

## Source Documents Read

- `README.md`
- `01-scope-and-principles.md`
- `02-target-user-workflow.md`
- `03-task-metadata-and-state.md`
- `04-cli-command-spec.md`
- `05-finish-work-pr-redesign.md`
- `06-worktree-parallel-development.md`
- `07-pr-reviewer-experience.md`
- `08-github-integration-milestones-labels-tags.md`
- `09-release-flow.md`
- `10-implementation-sequence.md`
- `11-test-and-acceptance-plan.md`
- `12-codex-execution-prompt.md`
