# Trellis File Reference

Current `.trellis/` file layout and purpose.

---

## Directory Structure

```
.trellis/
├── .developer
├── .current-task
├── .template-hashes.json
├── .version
├── .gitignore
├── workflow.md
├── workspace/
├── tasks/
├── spec/
└── scripts/
```

`worktree.yaml` and `.ralph-state.json` are historical and are not created by current templates.

---

## Root Files

| File | Purpose | Git state |
|------|---------|-----------|
| `.developer` | Local developer identity | gitignored |
| `.current-task` | Local active task pointer | gitignored |
| `.template-hashes.json` | Template hash tracking for `trellis update` | tracked |
| `.version` | Installed Trellis version | tracked |
| `.gitignore` | Trellis ignore rules | tracked |
| `workflow.md` | Main workflow and phase documentation | tracked |

---

## Directories

| Directory | Purpose |
|-----------|---------|
| `workspace/` | Per-developer journals and session notes |
| `tasks/` | Task metadata, PRDs, context JSONL, research, PR artifacts |
| `spec/` | Package/layer coding guidelines |
| `scripts/` | Trellis Python automation |

---

## Task Artifacts

```
.trellis/tasks/{task}/
├── task.json
├── prd.md
├── info.md
├── implement.jsonl
├── check.jsonl
├── research/
├── pr-body.md
└── review/
```

`pr-body.md` and `review/pr-review-*.md` are local fallback/review artifacts produced by PR-first commands when useful.

---

## Template Files Managed by Update

Typical managed surfaces include:

| File/Directory | Purpose |
|----------------|---------|
| `.trellis/workflow.md` | Workflow docs |
| `.trellis/scripts/` | Runtime scripts |
| `.trellis/spec/` | Default spec templates |
| `.claude/`, `.cursor/`, `.opencode/`, `.agents/`, etc. | Platform integrations |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR-first review template |

Update behavior compares hashes in `.trellis/.template-hashes.json`; modified files are preserved through the normal update conflict flow.

---

## Historical Removed Files

These files can appear in old installations or migration notes only:

| Historical file | Status |
|-----------------|--------|
| `.trellis/worktree.yaml` | Removed; use `task.py worktree` flags and task metadata |
| `.trellis/.ralph-state.json` | Removed Ralph Loop runtime state |
| `.trellis/scripts/multi_agent/*.py` | Removed legacy pipeline |
| `.trellis/scripts/common/registry.py` | Removed legacy agent registry helper |
| `.trellis/scripts/common/worktree.py` | Removed legacy worktree helper |

Do not document these as active current architecture.
