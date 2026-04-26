# Platform Compatibility

Trellis keeps its core workflow in files so every AI coding platform can participate. Platform integrations differ mainly in how much context injection and agent dispatch they automate.

---

## Compatibility Layers

| Layer | Capability | Typical platforms |
|-------|------------|-------------------|
| File-based core | Read/write `.trellis/` tasks, specs, workflow, scripts | All |
| Commands/skills | User-visible Trellis commands or skills | Most platforms |
| Agent-capable | Dedicated implement/check/research workers | Claude Code, Cursor, OpenCode, Codex, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi |
| Hook/prelude context | Automatic or semi-automatic context injection | Platform-dependent |
| Manual workflow | Main session reads specs and runs commands directly | Kilo, Antigravity, Windsurf and fallback paths |

---

## Current Cross-Platform Contract

All platforms should preserve these behaviors:

- tasks are created under `.trellis/tasks/`
- requirements are persisted in `prd.md`
- implementation/check context is curated in JSONL files
- medium/large work can use `task.py worktree`
- reviewable work can use `task.py create-pr`, `sync-pr`, `review-pr`, and `finish-pr`
- parallel work creates parent/child tasks, separate branches/worktrees, and separate draft PRs
- GitHub CLI/auth are enhancements, not hard requirements

---

## Removed Historical Mechanisms

These were part of older Trellis platform designs and are not current requirements:

| Historical mechanism | Current replacement |
|----------------------|---------------------|
| `SubagentStop` Ralph Loop | check-agent validation, CI, PR handoff evidence |
| `.claude/hooks/ralph-loop.py` | explicit validation commands and `task.py finish-pr` |
| `.trellis/worktree.yaml` | `task.py worktree` flags and task metadata |
| `.trellis/scripts/multi_agent/*.py` | parent/child tasks, platform workers, PR commands |
| `task.py init-context` | Phase 1.3 curated JSONL and `task.py add-context` |

---

## Portability Guidance

When adding or changing a Trellis feature:

1. Keep persistent state in `.trellis/`.
2. Keep command names and task metadata platform-neutral.
3. Update shared templates first when a behavior should ship broadly.
4. Update platform-specific adapters only for syntax or hook differences.
5. Search all mirrored locations before renaming commands, scripts, or paths.
6. Keep local-only fallback behavior for GitHub/remote-dependent features.

---

## Version Notes

| Version | Compatibility note |
|---------|--------------------|
| 0.3.x | Historical shell-to-Python and early multi-agent/worktree design |
| 0.5.x | Skill/agent-capable platform expansion, curated JSONL, PR-first task workflow |

Historical migration manifests may mention removed names while explaining upgrades. Do not copy those names into active current guidance.
