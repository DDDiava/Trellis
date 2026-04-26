# Hooks System

Claude Code hooks inject Trellis context and workflow breadcrumbs. Current hooks do not use Ralph Loop or `worktree.yaml`.

---

## Current Hook Lifecycle

```
Session starts/clears/compacts
  -> session-start.py injects workflow, task, git, and spec index context

User submits a prompt
  -> inject-workflow-state.py injects the active task breadcrumb

Task/Agent tool is called
  -> inject-subagent-context.py injects JSONL context from the current task

Status line refreshes
  -> statusline.py displays compact Trellis state
```

---

## Configuration

Claude Code stores hook configuration in `.claude/settings.json`.

Typical current entries:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 .claude/hooks/statusline.py"
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/session-start.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/inject-subagent-context.py",
            "timeout": 30
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/inject-workflow-state.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## Hook Scripts

| Script | Event | Purpose |
|--------|-------|---------|
| `session-start.py` | `SessionStart` | Loads session context, active task state, workflow index, and specs |
| `inject-workflow-state.py` | `UserPromptSubmit` | Adds a compact active-task breadcrumb per prompt |
| `inject-subagent-context.py` | `PreToolUse:Task` / `PreToolUse:Agent` | Loads `prd.md`, `info.md`, and JSONL context for sub-agents |
| `statusline.py` | status line | Displays task/status context |

---

## JSONL Context Loading

`inject-subagent-context.py` reads `.trellis/.current-task`, then loads the JSONL matching the sub-agent:

| Agent | JSONL file |
|-------|------------|
| `trellis-implement` / `implement` | `implement.jsonl` |
| `trellis-check` / `check` | `check.jsonl` |
| `trellis-research` / `research` | research-specific instructions and task context |

Rows without a `file` field are seed rows and are skipped.

Example:

```jsonl
{"file": ".trellis/spec/cli/backend/index.md", "reason": "Backend guidelines"}
{"file": ".trellis/tasks/04-25-example/research/api.md", "reason": "API research"}
```

---

## Historical Removed Hooks

Older Trellis docs described a `SubagentStop:check` Ralph Loop and `.claude/hooks/ralph-loop.py`. That mechanism is historical and removed from current templates. Validation now happens through check-agent instructions, explicit commands, CI, and PR handoff evidence.

See [ralph-loop.md](./ralph-loop.md) for the historical note.

---

## Debugging

```bash
python3 .claude/hooks/session-start.py
python3 .claude/hooks/inject-workflow-state.py
echo '{"tool_input":{"subagent_type":"trellis-implement","prompt":"test"}}' | python3 .claude/hooks/inject-subagent-context.py
```

Common issues:

| Issue | Check |
|-------|-------|
| No task context | `.trellis/.current-task` exists and points to a task |
| Empty sub-agent context | JSONL has curated rows with `file` fields |
| Hook not running | `.claude/settings.json` matcher and timeout |
| Wrong Python command | Use the platform-selected Python command in templates |
