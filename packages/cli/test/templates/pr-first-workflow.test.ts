import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { getCommandTemplates } from "../../src/templates/common/index.js";
import { getAllPrompts } from "../../src/templates/copilot/index.js";
import { getSharedHookScripts } from "../../src/templates/shared-hooks/index.js";
import {
  commonTaskPr,
  commonTaskStore,
  commonTypes,
  getAllScripts,
  pullRequestTemplate,
  taskScript,
  workflowMdTemplate,
} from "../../src/templates/trellis/index.js";
import { emptyTaskJson } from "../../src/utils/task-json.js";

const pythonCommand = process.platform === "win32" ? "python" : "python3";

interface CommandResult {
  ok: boolean;
  dry_run?: boolean;
  mode?: string;
  body?: string;
  body_changed?: boolean;
  body_file?: string;
  commands?: string[][];
}

function repoRoot(): string {
  return path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../../../..",
  );
}

function readRepoText(relativePath: string): string {
  return fs
    .readFileSync(path.join(repoRoot(), relativePath), "utf-8")
    .replace(/\r\n/g, "\n");
}

function stripLeadingFrontmatter(content: string): string {
  return content.replace(/^---\n[\s\S]*?\n---\n\n?/, "");
}

function writeTrellisScripts(root: string): void {
  const scriptsDir = path.join(root, ".trellis", "scripts");
  for (const [relativePath, content] of getAllScripts()) {
    const target = path.join(scriptsDir, relativePath);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, content, "utf-8");
  }
}

function writeTask(root: string, data: Record<string, unknown>): string {
  const taskDir = path.join(root, ".trellis", "tasks", "04-25-demo");
  fs.mkdirSync(taskDir, { recursive: true });
  fs.writeFileSync(
    path.join(taskDir, "task.json"),
    JSON.stringify(data, null, 2),
    "utf-8",
  );
  fs.writeFileSync(
    path.join(taskDir, "prd.md"),
    [
      "# Demo Task",
      "",
      "## Goal",
      "",
      "Ship a PR-first workflow.",
      "",
      "## Acceptance Criteria",
      "",
      "- [ ] Generated PR body includes review sections.",
      "- [ ] Dry runs do not mutate task metadata.",
      "",
    ].join("\n"),
    "utf-8",
  );
  return taskDir;
}

function runTask(root: string, args: string[]): string {
  return execFileSync(
    pythonCommand,
    [path.join(root, ".trellis", "scripts", "task.py"), ...args],
    { cwd: root, encoding: "utf-8" },
  );
}

describe("PR-first workflow templates", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "trellis-pr-first-"));
    writeTrellisScripts(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("exposes PR-first task commands and ships the shared task_pr helper", () => {
    for (const command of [
      "worktree",
      "create-pr",
      "sync-pr",
      "review-pr",
      "finish-pr",
    ]) {
      expect(taskScript).toContain(`"${command}"`);
      expect(runTask(tmpDir, ["--help"])).toContain(command);
    }

    const scripts = getAllScripts();
    expect(scripts.has("common/task_pr.py")).toBe(true);
    expect(commonTaskPr).toContain("def cmd_create_pr");
    expect(commonTaskPr).toContain("def replace_trellis_managed_section");
  });

  it("adds canonical PR metadata defaults in Python and TypeScript task writers", () => {
    const taskJson = emptyTaskJson();
    expect(taskJson.pr_number).toBeNull();
    expect(taskJson.pr_status).toBe("none");
    expect(taskJson.review_status).toBe("none");
    expect(taskJson.ci_status).toBe("unknown");
    expect(taskJson.merge_strategy).toBe("squash");
    expect(taskJson.labels).toEqual([]);
    expect(taskJson.reviewers).toEqual([]);
    expect(taskJson.validation).toEqual({
      lint: "unknown",
      typecheck: "unknown",
      test: "unknown",
      build: "unknown",
    });

    for (const field of [
      '"pr_number": None',
      '"review_status": "none"',
      '"last_agent_review_at": ""',
      '"merge_strategy": "squash"',
    ]) {
      expect(commonTaskStore).toContain(field);
    }
    expect(commonTypes).toContain("pr_number: int | None");
    expect(commonTypes).toContain("validation: list[str] | dict[str, object]");
  });

  it("worktree dry-run prints the planned git command and does not mutate task.json", () => {
    const taskDir = writeTask(tmpDir, {
      id: "demo",
      name: "demo",
      title: "Demo",
      status: "in_progress",
      base_branch: "main",
      branch: null,
      worktree_path: null,
      custom_field: "preserve-me",
    });
    const before = fs.readFileSync(path.join(taskDir, "task.json"), "utf-8");

    const out = runTask(tmpDir, ["worktree", "demo", "--dry-run", "--json"]);
    const parsed = JSON.parse(out) as CommandResult;

    expect(parsed.ok).toBe(true);
    expect(parsed.dry_run).toBe(true);
    expect(parsed.commands).toBeUndefined();
    expect(out).toContain("task/demo");
    expect(out).toContain("../trellis-worktrees/demo");
    expect(fs.readFileSync(path.join(taskDir, "task.json"), "utf-8")).toBe(
      before,
    );
  });

  it("create-pr falls back to local_only when gh is unavailable and preserves unknown metadata", () => {
    const taskDir = writeTask(tmpDir, {
      id: "demo",
      name: "demo",
      title: "Demo",
      status: "in_progress",
      base_branch: "main",
      branch: "task/demo",
      custom_field: "preserve-me",
    });
    const scriptsDir = path.join(tmpDir, ".trellis", "scripts");
    const runner = [
      "import os, runpy, sys",
      `sys.path.insert(0, ${JSON.stringify(scriptsDir)})`,
      'os.environ["PATH"] = ""',
      'sys.argv = ["task.py", "create-pr", "demo", "--draft", "--no-push", "--label", "workflow", "--reviewer", "octocat", "--milestone", "v0.5", "--json"]',
      `runpy.run_path(${JSON.stringify(path.join(scriptsDir, "task.py"))}, run_name="__main__")`,
    ].join("\n");

    const out = execFileSync(pythonCommand, ["-c", runner], {
      cwd: tmpDir,
      encoding: "utf-8",
    });
    const parsed = JSON.parse(out) as CommandResult;
    const data = JSON.parse(
      fs.readFileSync(path.join(taskDir, "task.json"), "utf-8"),
    ) as Record<string, unknown>;

    expect(parsed.ok).toBe(true);
    expect(parsed.mode).toBe("local_only");
    expect(parsed.commands).toEqual([
      [
        "gh",
        "pr",
        "create",
        "--base",
        "main",
        "--head",
        "task/demo",
        "--title",
        "Demo",
        "--body-file",
        path.join(taskDir, "pr-body.md"),
        "--draft",
        "--label",
        "workflow",
        "--milestone",
        "v0.5",
        "--reviewer",
        "octocat",
      ],
    ]);
    expect(data.custom_field).toBe("preserve-me");
    expect(data.pr_status).toBe("local_only");
    expect(data.review_status).toBe("draft");
    expect(data.labels).toEqual(["workflow"]);
    expect(data.reviewers).toEqual(["octocat"]);
    expect(data.milestone).toBe("v0.5");
    expect(data.pr_url).toBeUndefined();
    expect(fs.existsSync(path.join(taskDir, "pr-body.md"))).toBe(true);
  });

  it("sync-pr dry-run with no gh does not write local artifacts or metadata", () => {
    const taskDir = writeTask(tmpDir, {
      id: "demo",
      name: "demo",
      title: "Demo",
      status: "in_progress",
      base_branch: "main",
      branch: "task/demo",
    });
    const taskJson = path.join(taskDir, "task.json");
    const before = fs.readFileSync(taskJson, "utf-8");
    const scriptsDir = path.join(tmpDir, ".trellis", "scripts");
    const runner = [
      "import os, runpy, sys",
      `sys.path.insert(0, ${JSON.stringify(scriptsDir)})`,
      'os.environ["PATH"] = ""',
      'sys.argv = ["task.py", "sync-pr", "demo", "--dry-run", "--json"]',
      `runpy.run_path(${JSON.stringify(path.join(scriptsDir, "task.py"))}, run_name="__main__")`,
    ].join("\n");

    const out = execFileSync(pythonCommand, ["-c", runner], {
      cwd: tmpDir,
      encoding: "utf-8",
    });
    const parsed = JSON.parse(out) as CommandResult;

    expect(parsed.ok).toBe(true);
    expect(parsed.dry_run).toBe(true);
    expect(parsed.mode).toBe("local_only");
    expect(fs.readFileSync(taskJson, "utf-8")).toBe(before);
    expect(fs.existsSync(path.join(taskDir, "pr-body.md"))).toBe(false);
  });

  it("sync-pr local fallback preserves human PR body text outside Trellis markers", () => {
    const taskDir = writeTask(tmpDir, {
      id: "demo",
      name: "demo",
      title: "Demo",
      status: "in_progress",
      base_branch: "main",
      branch: "task/demo",
    });
    const bodyPath = path.join(taskDir, "pr-body.md");
    fs.writeFileSync(
      bodyPath,
      [
        "Human intro",
        "",
        "<!-- trellis:start -->",
        "old managed text",
        "<!-- trellis:end -->",
        "",
        "Human footer",
        "",
      ].join("\n"),
      "utf-8",
    );
    const scriptsDir = path.join(tmpDir, ".trellis", "scripts");
    const runner = [
      "import os, runpy, sys",
      `sys.path.insert(0, ${JSON.stringify(scriptsDir)})`,
      'os.environ["PATH"] = ""',
      'sys.argv = ["task.py", "sync-pr", "demo", "--json"]',
      `runpy.run_path(${JSON.stringify(path.join(scriptsDir, "task.py"))}, run_name="__main__")`,
    ].join("\n");

    const out = execFileSync(pythonCommand, ["-c", runner], {
      cwd: tmpDir,
      encoding: "utf-8",
    });
    const parsed = JSON.parse(out) as CommandResult;
    const body = fs.readFileSync(bodyPath, "utf-8");
    const data = JSON.parse(
      fs.readFileSync(path.join(taskDir, "task.json"), "utf-8"),
    ) as Record<string, unknown>;

    expect(parsed.ok).toBe(true);
    expect(parsed.body_changed).toBe(true);
    expect(body).toContain("Human intro");
    expect(body).toContain("Human footer");
    expect(body).toContain("## Trellis Task");
    expect(body).not.toContain("old managed text");
    expect(data.pr_status).toBe("local_only");
  });

  it("builds managed PR body sections and preserves human text outside markers", () => {
    const taskDir = writeTask(tmpDir, {
      id: "demo",
      name: "demo",
      title: "Demo",
      status: "in_progress",
      base_branch: "main",
      branch: "task/demo",
      validation: ["pnpm test"],
    });
    const scriptsDir = path.join(tmpDir, ".trellis", "scripts");
    const existingBody = [
      "Human intro",
      "",
      "<!-- trellis:start -->",
      "old managed text",
      "<!-- trellis:end -->",
      "",
      "Human footer",
      "",
    ].join("\n");
    const runner = [
      "import json, sys",
      "from pathlib import Path",
      `sys.path.insert(0, ${JSON.stringify(scriptsDir)})`,
      "from common.io import read_json",
      "from common.task_pr import build_trellis_pr_section, replace_trellis_managed_section",
      `task_dir = Path(${JSON.stringify(taskDir)})`,
      'data = read_json(task_dir / "task.json")',
      "managed = build_trellis_pr_section(task_dir, data)",
      `body = replace_trellis_managed_section(${JSON.stringify(existingBody)}, managed)`,
      "print(json.dumps({'managed': managed, 'body': body}))",
    ].join("\n");

    const out = execFileSync(pythonCommand, ["-c", runner], {
      cwd: tmpDir,
      encoding: "utf-8",
    });
    const parsed = JSON.parse(out) as { managed: string; body: string };

    for (const heading of [
      "## Trellis Task",
      "## Goal",
      "## Acceptance Criteria",
      "## What Changed",
      "## Validation Evidence",
      "## Reviewer Focus",
      "## Agent Review",
      "## Risk / Rollback",
    ]) {
      expect(parsed.managed).toContain(heading);
    }
    expect(parsed.managed).toContain("Ship a PR-first workflow.");
    expect(parsed.managed).toContain("- pnpm test");
    expect(parsed.body).toContain("Human intro");
    expect(parsed.body).toContain("Human footer");
    expect(parsed.body).not.toContain("old managed text");
  });

  it("finish-work template, workflow docs, PR template, and CI describe PR-first review", () => {
    const finishWork = getCommandTemplates().find(
      (template) => template.name === "finish-work",
    );
    expect(finishWork?.content).toContain("create-pr <task-name> --draft");
    expect(finishWork?.content).toContain("sync-pr <task-name>");
    expect(finishWork?.content).toContain("review-pr <task-name>");
    expect(finishWork?.content).toContain("finish-pr <task-name>");
    expect(finishWork?.content).toContain("Do not archive by default before merge");
    expect(finishWork?.content).toContain("Post-Merge Reconcile");
    expect(finishWork?.content).toContain("git fetch origin");
    expect(finishWork?.content).toContain("git status --short --branch");
    expect(finishWork?.content).toContain(
      "Local untracked or dirty files are a blocker",
    );
    expect(finishWork?.content).toContain(
      "git pull --ff-only origin <base-branch>",
    );
    expect(finishWork?.content).toContain(
      "Do not archive or record the session until the local base branch matches `origin/<base-branch>`",
    );
    expect(finishWork?.content).not.toContain(
      "Please review the changes and commit when ready.",
    );

    expect(workflowMdTemplate).toContain("PR-first lifecycle");
    expect(workflowMdTemplate).toContain("Post-merge reconcile gate");
    expect(workflowMdTemplate).toContain("task.py worktree");
    expect(workflowMdTemplate).toContain("task.py finish-pr");
    expect(workflowMdTemplate).toContain("git fetch origin");
    expect(workflowMdTemplate).toContain("git status --short --branch");
    expect(workflowMdTemplate).toContain(
      "git pull --ff-only origin <base-branch>",
    );
    expect(workflowMdTemplate).toContain(
      "Do not archive or record the session until the local base branch matches `origin/<base-branch>`",
    );
    expect(pullRequestTemplate).toContain("## Validation Evidence");
    expect(pullRequestTemplate).toContain("<!-- trellis:start -->");

    const sharedHookContent = getSharedHookScripts()
      .map((hook) => hook.content)
      .join("\n");
    expect(sharedHookContent).toContain("post-merge reconcile");
    expect(sharedHookContent).toContain(
      "only after the local base branch is current",
    );

    const ci = fs.readFileSync(
      path.join(repoRoot(), ".github", "workflows", "ci.yml"),
      "utf-8",
    );
    expect(ci).toContain("branches: [main, feat/v0.5.0-beta]");
    expect(ci).toContain("run: pnpm lint");
    expect(ci).toContain("run: pnpm typecheck");
    expect(ci).toContain("run: pnpm test");
    expect(ci).toContain("run: pnpm build");
  });

  it("keeps dogfood copies aligned on post-merge reconcile guidance", () => {
    const localFinishWorkRefs = new Map([
      [".claude/commands/trellis/finish-work.md", "/trellis:finish-work"],
      [".cursor/commands/trellis-finish-work.md", "/trellis-finish-work"],
      [".opencode/commands/trellis/finish-work.md", "/trellis:finish-work"],
      [".agents/skills/trellis-finish-work/SKILL.md", "$finish-work"],
      [
        "packages/cli/src/templates/codex/skills/finish-work/SKILL.md",
        "$finish-work",
      ],
      [
        "packages/cli/src/templates/copilot/prompts/finish-work.prompt.md",
        "/finish-work",
      ],
    ]);

    for (const [localPath, commandRef] of localFinishWorkRefs) {
      const content = stripLeadingFrontmatter(readRepoText(localPath));
      expect(content).toContain("create-pr <task-name> --draft");
      expect(content).toContain("sync-pr <task-name>");
      expect(content).toContain("review-pr <task-name>");
      expect(content).toContain("finish-pr <task-name>");
      expect(content).toContain("Do not archive by default before merge");
      expect(content).toContain("Local untracked or dirty files are a blocker");
      expect(content).toContain(
        "Do not archive or record the session until the local base branch matches `origin/<base-branch>`",
      );
      expect(content).toContain(commandRef);
      expect(content).not.toContain("{{CMD_REF");
    }

    expect(readRepoText(".trellis/workflow.md")).toBe(
      workflowMdTemplate.replace(/\r\n/g, "\n"),
    );

    const changedHookPaths = [
      ".claude/hooks/inject-workflow-state.py",
      ".claude/hooks/session-start.py",
      ".codex/hooks/inject-workflow-state.py",
      ".codex/hooks/session-start.py",
      ".cursor/hooks/inject-workflow-state.py",
      ".cursor/hooks/session-start.py",
      "packages/cli/src/templates/codex/hooks/session-start.py",
      "packages/cli/src/templates/copilot/hooks/session-start.py",
      "packages/cli/src/templates/opencode/plugins/inject-workflow-state.js",
      "packages/cli/src/templates/opencode/plugins/session-start.js",
      "packages/cli/src/templates/shared-hooks/inject-workflow-state.py",
      "packages/cli/src/templates/shared-hooks/session-start.py",
    ];

    for (const hookPath of changedHookPaths) {
      const content = readRepoText(hookPath);
      const normalizedContent = content.replace(/["'`+]/g, " ").replace(/\s+/g, " ");
      expect(normalizedContent).toContain("post-merge reconcile");
      expect(normalizedContent).toContain(
        "only after the local base branch is current",
      );
      expect(content).not.toMatch(
        /User commits changes; then run task\.py archive|Next: Archive with `python3 \.\/\.trellis\/scripts\/task\.py archive/,
      );
    }
  });

  it("documents parallel child-task PR handoff and avoids removed pipeline scripts", () => {
    expect(workflowMdTemplate).toContain("Parallel work means parallel PRs");
    expect(workflowMdTemplate).toContain("parent task plus child tasks");
    expect(workflowMdTemplate).toContain("distinct branch/worktree");
    expect(workflowMdTemplate).toContain("ownership/dependency plan");
    expect(workflowMdTemplate).toContain("git commit -m");
    expect(workflowMdTemplate).toContain("task.py create-pr <task-name> --draft");
    expect(workflowMdTemplate).toContain("task.py finish-pr <task-name>");

    const parallelPrompt = getAllPrompts().find(
      (prompt) => prompt.name === "parallel",
    );
    const parallelContent = parallelPrompt?.content ?? "";

    expect(parallelContent).toContain(
      "one child task per independently reviewable work item",
    );
    expect(parallelContent).toContain(
      'task.py create "<child goal>" --slug <child-task> --parent <parent-task>',
    );
    expect(parallelContent).not.toContain(
      "task.py add-subtask <parent-task> <child-task>",
    );
    expect(parallelContent).toContain("ownership/dependency plan");
    expect(parallelContent).toContain("task.py worktree <child-task>");
    expect(parallelContent).toContain("git commit -m");
    expect(parallelContent).toContain("git push -u origin task/<child-task>");
    expect(parallelContent).toContain("task.py create-pr <child-task> --draft");
    expect(parallelContent).toContain("task.py sync-pr <child-task>");
    expect(parallelContent).toContain("task.py review-pr <child-task>");
    expect(parallelContent).toContain("task.py finish-pr <child-task>");
    expect(parallelContent).toContain("pr-body.md");
    expect(parallelContent).toContain("review/pr-review-*.md");
    expect(parallelContent).toContain("Parent Post-Merge Reconcile");
    expect(parallelContent).toContain("git fetch origin");
    expect(parallelContent).toContain("git status --short --branch");
    expect(parallelContent).toContain(
      "git pull --ff-only origin <base-branch>",
    );
    expect(parallelContent).toContain(
      "verify every child PR merge commit is present locally",
    );
    expect(parallelContent).toContain("git merge-base --is-ancestor");
    expect(parallelContent).toContain("git worktree remove <worktree-path>");
    expect(parallelContent).toContain("git branch -d task/<child-task>");
    expect(parallelContent).toContain("git rev-parse --show-toplevel");
    expect(parallelContent).toContain(
      "final current-state directory and branch",
    );
    expect(parallelContent).not.toContain("task.py init-context");
    expect(parallelContent).not.toContain("multi_agent");

    expect(
      fs.existsSync(
        path.join(
          repoRoot(),
          "packages/cli/src/templates/markdown/worktree.yaml.txt",
        ),
      ),
    ).toBe(false);
  });

  it("keeps trellis-meta workflow docs on the current PR-first finish flow", () => {
    const root = repoRoot();

    for (const metaDir of [
      "packages/cli/src/templates/common/bundled-skills/trellis-meta",
      ".agents/skills/trellis-meta",
      ".claude/skills/trellis-meta",
      ".cursor/skills/trellis-meta",
      ".opencode/skills/trellis-meta",
    ]) {
      const workflowReference = fs.readFileSync(
        path.join(root, metaDir, "references/local-architecture/workflow.md"),
        "utf-8",
      );
      expect(workflowReference).toContain("PR-first repositories");
      expect(workflowReference).toContain("Phase 3.4");
      expect(workflowReference).toContain("PR handoff");
      expect(workflowReference).toContain("post-merge reconcile");
      expect(workflowReference).toContain("archive + journal");
    }

    for (const removedPath of [
      ".claude/commands/trellis/parallel.md",
      ".claude/commands/trellis/start.md",
      ".cursor/commands/trellis-start.md",
      ".opencode/commands/trellis/parallel.md",
      ".opencode/commands/trellis/start.md",
    ]) {
      expect(fs.existsSync(path.join(root, removedPath))).toBe(false);
    }
  });

  it("keeps shipped start templates on the curated-context flow", () => {
    const copilotStart = getAllPrompts().find(
      (prompt) => prompt.name === "start",
    );
    const codexStart = fs.readFileSync(
      path.join(
        repoRoot(),
        "packages/cli/src/templates/codex/skills/start/SKILL.md",
      ),
      "utf-8",
    );

    for (const content of [copilotStart?.content ?? "", codexStart]) {
      expect(content).toContain('Skip seed rows without a `file` field');
      expect(content).toContain('task.py validate "$TASK_DIR"');
      expect(content).not.toContain("task.py init-context");
    }
  });
});
