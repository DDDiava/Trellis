# How To: Add Agent

Add a new Trellis agent type.

---

## Files to Modify

| File | Action | Required |
|------|--------|----------|
| Platform agent definition | Create | Yes |
| Hook/prelude context loader | Modify if the platform needs explicit routing | Maybe |
| Task JSONL manifest | Create or curate | Yes |
| `trellis-local/SKILL.md` | Update | Yes |
| Workflow/commands | Modify if the agent becomes part of standard flow | Maybe |

Examples:

```
.claude/agents/my-agent.md
packages/cli/src/templates/claude/agents/my-agent.md
packages/cli/src/templates/codex/skills/my-agent/SKILL.md
```

---

## Step 1: Create Agent Definition

Use the platform's native agent/skill format and document:

- purpose
- when to use it
- allowed tools
- required context files
- forbidden operations
- output format

---

## Step 2: Add Context Loading

If the platform has hook/prelude routing, add the new agent to that routing. The context source should be a curated JSONL file in the task directory.

Example JSONL:

```jsonl
{"file": ".trellis/spec/guides/index.md", "reason": "Thinking guides"}
{"file": ".trellis/tasks/04-25-example/research/topic.md", "reason": "Research for this agent"}
```

Rows without a `file` field are seed rows and should be skipped.

Do not add the agent through `task.py init-context`; that command was removed. Use Phase 1.3 curation or `task.py add-context`.

---

## Step 3: Add to Workflow If Needed

If the agent becomes part of the standard workflow, update `.trellis/workflow.md`, command/skill prompts, and any platform-specific agent instructions. Prefer explicit phase guidance over legacy `next_action` pipeline fields.

---

## Step 4: Document in trellis-local

Record:

- agent name and path
- platform support
- context JSONL file
- hook/prelude changes
- workflow changes
- validation performed

---

## Testing

1. Create or use a task with the agent JSONL.
2. Start the task.
3. Invoke the agent through the platform.
4. Verify it receives `prd.md`, `info.md`, and curated JSONL context.
5. Verify output follows the agent contract.
