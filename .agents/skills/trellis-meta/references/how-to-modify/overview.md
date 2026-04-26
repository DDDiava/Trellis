# How-To Modification Guide

Common Trellis customization scenarios and the files they touch.

---

## Quick Reference

| Task | Files to Modify | Platform |
|------|-----------------|----------|
| Add slash command | platform commands + `trellis-local` | All |
| Add agent | platform agents, hook/prelude, JSONL, `trellis-local` | Agent-capable |
| Modify hook | hook file, settings, `trellis-local` | Hook-capable |
| Add spec category | `.trellis/spec/`, task JSONL, `trellis-local` | All |
| Change validation commands | workflow/agent/check docs, CI, `trellis-local` | All |
| Add workflow phase guidance | `.trellis/workflow.md`, command/skill prompts, `trellis-local` | All |
| Add setup step for worktrees | child task `info.md` or repo setup scripts | All |
| Add core script | `.trellis/scripts/` and template copy | All |
| Change task metadata | task writers/readers/tests/spec docs | All |

`worktree.yaml` and `task.py init-context` are removed. Do not use them for new customization guidance.

---

## Add Slash Command

Create or modify the platform command templates, then document the change in `trellis-local`.

Examples:

```
.claude/commands/trellis/my-command.md
.cursor/commands/trellis-my-command.md
.opencode/commands/trellis/my-command.md
packages/cli/src/templates/common/commands/my-command.md
```

---

## Add Agent

Create the platform agent definition, add hook/prelude loading if needed, create a JSONL manifest for the new context, and document in `trellis-local`.

See `add-agent.md`.

---

## Modify Hook

Edit the hook implementation and platform settings if the event or timeout changes.

See `modify-hook.md`.

---

## Add Spec Category

Create the spec files and add them to task JSONL manifests through Phase 1.3 curation or `task.py add-context`.

See `add-spec.md`.

---

## Change Validation Commands

Current validation lives in:

- agent instructions
- `.trellis/workflow.md`
- CI workflows
- project scripts such as `package.json`
- task/PR validation evidence

Do not add a `verify:` block to `.trellis/worktree.yaml`; that config is historical.

---

## Add Setup Step for Worktrees

Current `task.py worktree` does not read `post_create` config. Put setup steps in:

- child task `info.md`
- the parent ownership/dependency plan
- repo scripts such as `scripts/setup-dev`
- worker instructions in the parallel prompt

---

## Add Core Script

When adding files under `.trellis/scripts/`, also update the installable template copy under `packages/cli/src/templates/trellis/scripts/` and register new template files through `packages/cli/src/templates/trellis/index.ts`.

---

## Historical Removed Guidance

If an old guide says to modify `worktree.yaml`, `task.py init-context`, `common/registry.py`, `common/worktree.py`, or `.trellis/scripts/multi_agent/*.py`, treat it as historical unless the repository restored that implementation.
