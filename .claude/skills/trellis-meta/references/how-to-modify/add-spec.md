# How To: Add Spec Category

Add a new `.trellis/spec/` category such as `mobile/`.

---

## Files to Modify

| File | Action | Required |
|------|--------|----------|
| `.trellis/spec/<category>/index.md` | Create | Yes |
| `.trellis/spec/<category>/*.md` | Create | Yes |
| Task JSONL manifests | Curate | Yes |
| `trellis-local/SKILL.md` | Update | Yes |

---

## Step 1: Create Category Directory

```bash
mkdir .trellis/spec/mobile
```

On Windows, create the directory through your shell or editor.

---

## Step 2: Create Index File

Create `.trellis/spec/mobile/index.md`:

```markdown
# Mobile Specifications

Guidelines for mobile development.

## Pre-Development Checklist

- Read architecture guidelines.
- Read UI guidelines.

## Guidelines

| Guide | Description |
|-------|-------------|
| [Architecture](./architecture.md) | Architecture patterns |
| [UI Guidelines](./ui-guidelines.md) | UI patterns |
```

---

## Step 3: Create Spec Files

Use focused files with concrete rules and examples. Link related specs explicitly.

---

## Step 4: Curate JSONL Context

Add the specs to relevant task manifests during Phase 1.3:

```bash
python3 ./.trellis/scripts/task.py add-context <task> implement .trellis/spec/mobile/index.md "Mobile guidelines"
python3 ./.trellis/scripts/task.py add-context <task> check .trellis/spec/mobile/index.md "Mobile quality checks"
```

Or edit the JSONL directly:

```jsonl
{"file": ".trellis/spec/mobile/index.md", "reason": "Mobile guidelines"}
{"file": ".trellis/spec/mobile/architecture.md", "reason": "Architecture patterns"}
```

Do not modify `task.py init-context`; that command was removed.

---

## Step 5: Document in trellis-local

Record the category, purpose, files, date, and any project-specific rules.

---

## Checklist

- [ ] Category directory created
- [ ] `index.md` has a pre-development checklist
- [ ] Spec files are concrete and linked
- [ ] Relevant task JSONL files are curated
- [ ] Customization is documented in `trellis-local`
