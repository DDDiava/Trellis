# Implement PR-first Workflow Redesign

## Goal

Adopt the PR-first Trellis workflow described in `D:/Google_download/trellis-pr-first-guides/` on top of `feat/v0.5.0-beta`, using the current branch `codex/pr-first-workflow-redesign`. Trellis should guide medium and large user tasks toward branch/worktree, draft PR, agent validation, human PR review, merge, then archive, while preserving local-only and non-GitHub fallback paths.

## Requirements

- Extend Trellis task metadata with optional PR-first fields: `pr_number`, `pr_status`, `review_status`, `ci_status`, `issue_url`, `milestone`, `labels`, `reviewers`, `merge_strategy`, `integration_branch`, `last_pr_sync_at`, `last_agent_review_at`, and `validation`.
- Preserve existing fields and unknown task metadata when reading or writing `task.json`.
- Keep `.trellis/scripts/...` and `packages/cli/src/templates/trellis/scripts/...` synchronized for all script behavior.
- Add `task.py worktree <task>` with `--base`, `--branch`, `--path`, `--force`, `--dry-run`, and `--json`.
- Make `worktree` default to `base = --base || task.base_branch || current branch`, `branch = task/<task-slug>`, and `path = ../trellis-worktrees/<task-slug>`.
- Make `worktree` update `branch`, `base_branch`, and `worktree_path` only after successful execution; dry-run must not mutate metadata.
- Add `task.py create-pr <task>` with `--base`, `--head`, `--title`, `--draft`, repeated `--label`, `--milestone`, repeated `--reviewer`, `--issue`, `--body-file`, `--push/--no-push`, `--dry-run`, and `--json`.
- Generate PR bodies from task PRD/info/metadata with task, goal, acceptance criteria, what changed, validation evidence, reviewer focus, agent review, and risk/rollback sections.
- Use `gh` when available and authenticated; if unavailable, print manual commands and keep the workflow usable as `local_only`/draft instead of crashing.
- Detect existing PRs for the same head branch where possible to avoid duplicates.
- Add feasible `sync-pr`, `review-pr`, and `finish-pr` support for PR status syncing, Trellis-managed body-section replacement, local review artifacts, and ready-for-human-review gating.
- Redesign installable `/finish-work` template around preparing a reviewable PR, not asking the user to review individual commits.
- Update `.trellis/workflow.md` and `packages/cli/src/templates/trellis/workflow.md` to describe the PR-first lifecycle and commands.
- Add `.github/PULL_REQUEST_TEMPLATE.md` with PR-first review fields.
- Update `.github/workflows/ci.yml` so pull requests targeting `feat/v0.5.0-beta` run CI, using actual package scripts.
- Add `.github/release.yml` if it stays low-risk and useful for release-note categorization.
- Add/update tests for metadata compatibility, command availability, dry-run behavior, generated PR body, managed-section replacement, finish-work text, and CI/template coverage.

## Acceptance Criteria

- [ ] `task.py --help` exposes `worktree`, `create-pr`, `sync-pr`, `review-pr`, and `finish-pr` where implemented.
- [ ] New tasks include PR-first metadata defaults or old tasks receive defaults safely when loaded/saved.
- [ ] `task.py worktree <task> --dry-run` prints the git worktree command and does not mutate metadata.
- [ ] `task.py worktree <task>` can create a branch/worktree in a temp git repo and updates task metadata.
- [ ] Branch, path, dirty tree, missing base, missing GitHub CLI, and unauthenticated GitHub cases produce clear next steps.
- [ ] `task.py create-pr <task> --dry-run --draft` prints the push/gh flow and does not mutate `pr_url`.
- [ ] `create-pr` fallback without `gh` does not crash and leaves task metadata in a clear local/draft state.
- [ ] Generated PR body includes task, goal, acceptance criteria, validation, reviewer focus, agent review, and risk/rollback.
- [ ] Managed section replacement preserves human-written PR body content outside Trellis markers.
- [ ] `/finish-work` template no longer treats "review and commit" as the main finish action and does not archive before merge by default.
- [ ] `.trellis` dogfood scripts and package templates remain behaviorally synchronized.
- [ ] CI includes PRs targeting `feat/v0.5.0-beta`.
- [ ] Available validation runs pass, or any skipped check is explained honestly.

## Definition of Done

- Tests added or updated for changed behavior.
- `pnpm lint`, `pnpm typecheck`, and relevant tests pass.
- Python scripts remain cross-platform: `pathlib`, explicit UTF-8 subprocess/file handling, clear Windows-safe command wording where user-facing.
- Generated/installable templates are registered through existing template export mechanisms.
- No GitHub-only hard dependency is introduced.

## Technical Approach

Implement the MVP in small internal slices:

1. Add shared task PR metadata defaults and PR/worktree helpers in Python, then sync dogfood and package template script trees.
2. Wire new argparse subcommands in both `task.py` copies.
3. Implement PR body generation and managed-section replacement as pure helpers with unit/regression coverage.
4. Update workflow and finish-work templates.
5. Add GitHub template/release files and CI beta branch trigger.
6. Validate with TypeScript tests plus targeted Python smoke commands where practical.

## Decision (ADR-lite)

Context: The external plan recommends multiple PRs, but the user asked this agent to complete the change from a single branch. The repo already dogfoods Trellis scripts and installable templates, so partial script/template drift would be worse than a broader but coherent MVP.

Decision: Implement one coherent PR-first MVP on `codex/pr-first-workflow-redesign`, prioritizing runnable `worktree` and `create-pr`, metadata compatibility, `/finish-work` semantics, PR template, and CI beta targeting. Include `sync-pr/review-pr/finish-pr` if they can be implemented with clear local/dry-run behavior and tests.

Consequences: The branch will touch Python scripts, template files, docs, GitHub metadata, and tests. The implementation must stay conservative and keep GitHub as an enhancement path rather than a hard requirement.

## Out of Scope

- Rewriting all release scripts in this pass.
- Automatically creating GitHub labels or milestones.
- Hardcoding CODEOWNERS usernames.
- Auto-archiving tasks before PR merge.
- Forcing every small task to use PR/worktree.
- Changing `CONTRIBUTING.md` except for incidental consistency if discovered necessary.

## Research References

- `research/external-plan-summary.md` - condensed requirements and repo findings from the supplied plan package.

## Technical Notes

- Current task branch: `codex/pr-first-workflow-redesign`.
- Base branch: `feat/v0.5.0-beta`.
- Must sync `.trellis/scripts/` with `packages/cli/src/templates/trellis/scripts/`.
- Relevant specs: `.trellis/spec/cli/backend/index.md`, `.trellis/spec/cli/unit-test/index.md`, and cross-platform/code-reuse guides.
