---
name: trellis-meta
description: "Meta-skill for understanding and customizing Mindfold Trellis, including workflow phases, task metadata, PR-first completion, parallel child-task work, hooks, commands, agents, and project-local customization guidance. Modifications should be recorded in a project-local trellis-local skill, not here."
---

# Trellis Meta-Skill

## Version Compatibility

| Item | Value |
|------|-------|
| Trellis CLI Version | 0.5.x PR-first workflow |
| Skill Last Updated | 2026-04-26 |
| Primary platforms | Claude Code, Cursor, OpenCode, Codex, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi |

This skill describes current Trellis behavior. Historical pages are explicitly labeled when they describe removed mechanisms.

---

## Core Contract

Trellis is a file-based workflow system for AI-assisted development:

- Tasks live in `.trellis/tasks/`.
- Requirements live in each task's `prd.md`; optional design notes live in `info.md`.
- Context manifests are curated in `implement.jsonl`, `check.jsonl`, and related JSONL files.
- Project guidance lives under `.trellis/spec/`.
- Medium and large work should finish as a reviewable PR, not as loose commits.
- Parallel work should use a parent task plus child tasks, each child on its own branch/worktree with its own draft PR.

---

## Platform Compatibility

| Feature | Hook-capable platforms | Pull/self-loading platforms | Manual platforms |
|---------|------------------------|-----------------------------|------------------|
| Workspace, tasks, specs | Full | Full | Full |
| Session workflow breadcrumbs | Hook-injected | Hook/plugin/prelude where available | Read manually |
| Sub-agent context | Injected from JSONL | Agent prelude loads JSONL | Main session reads specs |
| PR-first task commands | Full | Full | Full |
| Parallel child tasks/worktrees | Full via `task.py` + platform workers | Full via `task.py` + platform workers | Manual worker coordination |

Current Trellis does not rely on the removed `multi_agent/` script directory, `worktree.yaml`, `common/registry.py`, or `common/worktree.py`.

---

## Architecture Overview

```
User request
  -> workflow.md phase rules
  -> task directory (prd.md, info.md, task.json, context jsonl)
  -> platform command/skill/agent prompts
  -> implement/check agents or main-session equivalent
  -> PR-first handoff commands
```

### Persistence Layer

```
.trellis/
├── workflow.md
├── workspace/
├── tasks/
├── spec/
└── scripts/
```

### Platform Layer

```
.claude/       # Claude Code commands, agents, hooks
.cursor/       # Cursor commands/hooks
.opencode/     # OpenCode commands/plugins/agents
.agents/       # Shared Codex-style skills
packages/cli/src/templates/
```

---

## Task System

Task directories contain:

```
.trellis/tasks/{MM-DD-slug}/
├── task.json
├── prd.md
├── info.md
├── implement.jsonl
├── check.jsonl
└── research/
```

Important metadata includes branch/worktree and PR review fields: `branch`, `base_branch`, `worktree_path`, `pr_url`, `pr_number`, `pr_status`, `review_status`, `ci_status`, `labels`, `reviewers`, `merge_strategy`, and `validation`.

---

## PR-First Parallel Contract

When the user asks for parallel development:

1. Create one parent task for coordination.
2. Create one child task per independently reviewable work item.
3. Record an ownership/dependency plan for shared contracts, shared files, interfaces, migrations, templates, and sequencing.
4. Prefer disjoint write scopes; use a prerequisite scaffold child task only when no worker can proceed independently.
5. Give every child a separate branch/worktree with `task.py worktree`.
6. Each worker runs implement/check for its child task.
7. Each worker completes a PR handoff:

```bash
git status
git add -A
git commit -m "<task-slug>: <summary>"
git push -u origin <branch>
python3 ./.trellis/scripts/task.py create-pr <child-task> --draft
python3 ./.trellis/scripts/task.py sync-pr <child-task>
python3 ./.trellis/scripts/task.py review-pr <child-task>
python3 ./.trellis/scripts/task.py finish-pr <child-task>
```

If `gh`, auth, or a remote is unavailable, workers leave local fallback artifacts such as `pr-body.md`, `review/pr-review-*.md`, task metadata, and exact push/PR commands.

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `.trellis/scripts/get_context.py` | Show session, task, git, and spec context |
| `.trellis/scripts/task.py` | Task CRUD, context JSONL, branch/worktree, and PR commands |
| `.trellis/scripts/add_session.py` | Record session progress |
| `.trellis/scripts/init_developer.py` | Initialize developer identity |

Key PR-first commands:

```bash
python3 ./.trellis/scripts/task.py worktree <task> --dry-run
python3 ./.trellis/scripts/task.py worktree <task>
python3 ./.trellis/scripts/task.py create-pr <task> --draft
python3 ./.trellis/scripts/task.py sync-pr <task>
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

---

## Historical Removed Items

These names can appear in migration notes only. They are not active guidance:

| Removed item | Current replacement |
|--------------|---------------------|
| `.trellis/scripts/multi_agent/plan.py` | Phase 1 task creation + PRD/research + curated JSONL |
| `.trellis/scripts/multi_agent/start.py` | `task.py worktree <task>` plus platform worker dispatch |
| `.trellis/scripts/multi_agent/status.py` | `task.py list`, `git worktree list`, platform session UI |
| `.trellis/scripts/multi_agent/create_pr.py` | `task.py create-pr <task> --draft` |
| `.trellis/scripts/multi_agent/cleanup.py` | `git worktree remove` plus archive after merge |
| `task.py init-context` | Phase 1.3 curated JSONL + `task.py add-context` |
| `.trellis/worktree.yaml` | `task.py worktree` flags and task metadata |
| `common/registry.py`, `common/worktree.py` | `common/task_pr.py` and normal git/platform state |

---

## Resources

| Directory | Purpose |
|-----------|---------|
| `references/core/` | Cross-platform tasks, scripts, files, specs, workspace |
| `references/claude-code/` | Claude Code hooks, agents, and current platform-specific notes |
| `references/how-to-modify/` | Customization recipes |
| `references/meta/` | Project-local skill template and maintenance guidance |

Start with `references/core/tasks.md`, `references/core/scripts.md`, and `references/claude-code/multi-session.md` for PR-first parallel workflow details.

---

## Customization Protocol

Project-specific Trellis changes belong in a `trellis-local` skill:

```
.claude/skills/trellis-local/SKILL.md
.agents/skills/trellis-local/SKILL.md
```

Record what changed, why it changed, affected files, validation, and migration notes. Update `trellis-meta` only when changing vanilla Trellis documentation itself.
