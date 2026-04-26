# How To: Change Validation Commands

Current Trellis does not use `worktree.yaml` or Ralph Loop verification. Validation commands belong in workflow guidance, agent instructions, CI, repo scripts, and PR evidence.

---

## Files to Consider

| File | Why |
|------|-----|
| `.trellis/workflow.md` | Human/AI workflow guidance |
| Platform agent/check prompts | What check agents must run |
| `.github/workflows/*.yml` | CI validation |
| `package.json` or project scripts | Source of actual commands |
| `trellis-local/SKILL.md` | Project-specific customization notes |

---

## Common Command Sets

Node/TypeScript:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Python:

```bash
ruff check .
mypy .
pytest
```

Go:

```bash
go fmt ./...
go vet ./...
go test ./...
```

Rust:

```bash
cargo fmt --check
cargo clippy
cargo test
```

---

## PR-First Evidence

After running validation, keep PR metadata/body current:

```bash
python3 ./.trellis/scripts/task.py review-pr <task>
python3 ./.trellis/scripts/task.py finish-pr <task>
```

When validation cannot run, record the reason in the task notes, PR body, or local review artifact.

---

## Historical Note

Older docs said to add commands under `verify:` in `.trellis/worktree.yaml`. That is removed. Do not create or edit `worktree.yaml` for current validation.
