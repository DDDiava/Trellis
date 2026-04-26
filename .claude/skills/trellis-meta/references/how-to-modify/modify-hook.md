# How To: Modify Hook

Change hook behavior for context injection, workflow breadcrumbs, or status display.

---

## Files to Modify

| File | Action | Required |
|------|--------|----------|
| Platform hook script | Modify | Yes |
| Platform settings | Modify if event/matcher/timeout changes | Maybe |
| Shared hook template | Modify when change should ship to new projects | Maybe |
| `trellis-local/SKILL.md` | Update for project-specific changes | Yes |

Typical locations:

```
.claude/hooks/
packages/cli/src/templates/shared-hooks/
packages/cli/src/templates/opencode/plugins/
packages/cli/src/templates/codex/hooks/
```

---

## Current Hook Types

| Hook | Purpose |
|------|---------|
| `session-start.py` | Session boundary context |
| `inject-workflow-state.py` | Per-prompt active task breadcrumb |
| `inject-subagent-context.py` | Sub-agent JSONL context injection |
| `statusline.py` | Compact status display |

`ralph-loop.py` and `SubagentStop:check` are historical removed mechanisms.

---

## Step 1: Understand Input and Output

Hooks receive JSON from the platform, read Trellis files, and emit platform-specific JSON/text. Always preserve current output contract for that platform.

When editing shared hooks, verify every platform that consumes the hook template.

---

## Step 2: Modify Logic

Example: add a file to session context:

```python
extra = repo_root / ".trellis" / "custom-context.md"
if extra.is_file():
    parts.append(extra.read_text(encoding="utf-8"))
```

Example: add a guard to sub-agent context:

```python
if subagent_type == "trellis-implement" and "git commit" in prompt.lower():
    return block("Implement agents must not commit.")
```

---

## Step 3: Update Settings If Needed

If matcher, event, timeout, or command path changes, update the platform settings template and the dogfood copy.

---

## Step 4: Document and Test

Document in `trellis-local`:

- hook file
- event/matcher
- behavior change
- reason
- validation

Manual checks:

```bash
python3 .claude/hooks/session-start.py
python3 .claude/hooks/inject-workflow-state.py
echo '{"tool_input":{"subagent_type":"trellis-implement","prompt":"test"}}' | python3 .claude/hooks/inject-subagent-context.py
```

---

## Historical Note

Do not add validation by restoring `ralph-loop.py`, `SubagentStop:check`, or `worktree.yaml` verification. Current validation belongs in check-agent instructions, explicit commands, CI, and PR handoff.
