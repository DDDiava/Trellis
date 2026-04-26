# Agents Reference

Trellis uses specialized agents for research, implementation, and checking. Current task state lives in `.trellis/`; agents receive task context from `prd.md`, optional `info.md`, and curated JSONL files.

---

## Current Agent Types

| Agent | Purpose | Writes? | Git handoff |
|-------|---------|---------|-------------|
| `trellis-research` | Research code, APIs, docs, and persist findings | Only `{TASK_DIR}/research/` | No |
| `trellis-implement` | Implement requirements using injected specs/context | Yes | No commit/push by default |
| `trellis-check` | Review changes, fix findings, run validation | Yes | No commit/push by default |

Some platforms expose names without the `trellis-` prefix internally, but the workflow intent is the same.

---

## Context Loading

Agents must resolve the current task first:

```bash
Get-Content .trellis/.current-task
```

Then load:

- `prd.md`
- `info.md` when present
- JSONL rows with a `file` field from the matching context manifest

Seed rows such as `{"_example": "..."}` are ignored.

---

## Research Agent

The research agent is read-only except for research artifacts:

```
{TASK_DIR}/research/<topic>.md
```

Research output must be persisted to files because conversations compact. The main session or later sub-agents should consume the artifact paths, not rely on chat memory.

---

## Implement Agent

The implement agent:

1. Reads task requirements and design notes.
2. Reads every curated `implement.jsonl` file entry.
3. Searches code before editing.
4. Makes focused code changes.
5. Runs relevant lint/typecheck/test commands where practical.

It should not commit, push, merge, or open PRs unless the platform-specific worker prompt explicitly owns a parallel child-task handoff.

---

## Check Agent

The check agent:

1. Reviews the diff.
2. Checks behavior against `prd.md` and specs from `check.jsonl`.
3. Fixes findings directly.
4. Runs available validation.
5. Reports remaining risks honestly.

Current Trellis does not rely on a `SubagentStop` Ralph Loop. Validation is explicit in the check agent, CI, and PR handoff commands.

---

## Parallel Worker Agents

For parallel child tasks, a worker may own the full branch/worktree handoff after implement/check:

```bash
git status
git add -A
git commit -m "<child-task>: <summary>"
git push -u origin task/<child-task>
python3 ./.trellis/scripts/task.py create-pr <child-task> --draft
python3 ./.trellis/scripts/task.py sync-pr <child-task>
python3 ./.trellis/scripts/task.py review-pr <child-task>
python3 ./.trellis/scripts/task.py finish-pr <child-task>
```

If GitHub integration is unavailable, the worker leaves local fallback artifacts and exact manual commands.

---

## Adding Custom Agents

1. Create the platform agent definition.
2. Add context loading behavior in the platform hook/prelude if needed.
3. Add a curated JSONL file for tasks that need the agent.
4. Document the customization in `trellis-local`.

Do not add custom agents by reviving `task.py init-context` or the old `next_action` pipeline. Current context is curated directly through JSONL files and task PRDs.

---

## Historical Removed Pipeline

Older docs described `dispatch`, `plan`, `debug`, `next_action`, and a multi-agent pipeline ending in old PR scripts. Those names are historical unless the current repository explicitly ships matching agents and scripts.

Current PR-first orchestration is described in `.trellis/workflow.md` and implemented through task commands plus platform-native agent/skill dispatch.
