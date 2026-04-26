# Claude Code Features Overview

Claude Code support is one platform integration for the current Trellis workflow. It provides commands, agents, and hooks, while PR-first task state remains in `.trellis/` and is shared across platforms.

---

## Current Features

| Feature | Purpose |
|---------|---------|
| Commands | User-facing `/trellis:*` prompts |
| Agents | `trellis-research`, `trellis-implement`, `trellis-check` |
| SessionStart hook | Inject workflow and task context at session boundaries |
| UserPromptSubmit hook | Inject current workflow breadcrumb per user prompt |
| PreToolUse hook | Inject task JSONL context into sub-agents |
| Status line | Show Trellis task/status information |
| PR-first commands | Shared `task.py` branch/worktree and PR handoff |

Claude Code no longer depends on a `SubagentStop` Ralph Loop, `worktree.yaml`, or the removed `multi_agent/` scripts.

---

## Feature Categories

### Hooks

Hooks keep context current:

- `session-start.py`
- `inject-workflow-state.py`
- `inject-subagent-context.py`
- `statusline.py`

See [hooks.md](./hooks.md).

### Agents

Agents handle focused phases:

- `trellis-research` persists research artifacts under the current task.
- `trellis-implement` writes code using `implement.jsonl`, `prd.md`, and `info.md`.
- `trellis-check` reviews/fixes changes using `check.jsonl` and runs validation.

See [agents.md](./agents.md).

### Parallel PR-First Work

Parallel work uses parent and child tasks. Each child gets its own branch/worktree and draft PR.

See [multi-session.md](./multi-session.md).

### Historical Worktree Config

The `worktree-config.md` page is retained only to explain the removed `worktree.yaml` mechanism and map it to current command flags.

---

## Documents in This Directory

| Document | Content |
|----------|---------|
| `hooks.md` | Current Claude Code hook behavior |
| `agents.md` | Agent types and context loading |
| `multi-session.md` | PR-first parallel child-task workflow |
| `scripts.md` | Current script commands and removed-script mapping |
| `worktree-config.md` | Historical `worktree.yaml` notes |
| `ralph-loop.md` | Historical removed Ralph Loop notes |

---

## Checking Claude Code Availability

```bash
claude --version
cat .claude/settings.json
```

If hooks are missing, Trellis still works from files and commands, but automatic context injection will be unavailable.
