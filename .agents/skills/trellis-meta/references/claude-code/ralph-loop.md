# Historical Ralph Loop Reference

Ralph Loop is historical. Current Trellis templates do not ship a `SubagentStop` quality loop, `.claude/hooks/ralph-loop.py`, or `worktree.yaml` verification config.

This page exists so old references are not mistaken for active guidance.

---

## Removed Behavior

Older Trellis versions described:

1. Check agent stops.
2. `SubagentStop:check` hook runs `ralph-loop.py`.
3. The hook reads `verify` commands from `.trellis/worktree.yaml`.
4. Failing commands block the check agent until fixed or a max-iteration limit is reached.

That flow has been removed.

---

## Current Replacement

Use normal validation and PR evidence:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

The check agent should run relevant validation and self-fix issues. CI and `task.py finish-pr` provide the final ready-for-human-review gate when available.

---

## Migration Rule

If you find these names in old docs, treat them as removed unless the repository has restored the implementation:

- `.claude/hooks/ralph-loop.py`
- `SubagentStop:check`
- `.trellis/worktree.yaml`
- `verify:` in worktree config

Do not advise users to recreate these files as part of current Trellis setup.
