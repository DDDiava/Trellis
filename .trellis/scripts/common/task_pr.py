"""
PR-first task workflow helpers.

Provides:
    ensure_pr_metadata_defaults - Add PR metadata defaults without dropping unknown fields
    cmd_worktree                - Create a task worktree and branch
    cmd_create_pr               - Create or stage a GitHub PR
    cmd_sync_pr                 - Sync PR metadata and Trellis-managed body section
    cmd_review_pr               - Write a local PR review artifact
    cmd_finish_pr               - Mark a PR ready for human review
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .git import run_git
from .io import read_json, write_json
from .log import Colors, colored
from .paths import FILE_TASK_JSON, get_current_task, get_repo_root
from .task_utils import resolve_task_dir


PR_METADATA_DEFAULTS: dict[str, Any] = {
    "pr_number": None,
    "pr_status": "none",
    "review_status": "none",
    "ci_status": "unknown",
    "issue_url": "",
    "milestone": "",
    "labels": [],
    "reviewers": [],
    "merge_strategy": "squash",
    "integration_branch": "",
    "last_pr_sync_at": "",
    "last_agent_review_at": "",
    "validation": {
        "lint": "unknown",
        "typecheck": "unknown",
        "test": "unknown",
        "build": "unknown",
    },
}

TRELLIS_START = "<!-- trellis:start -->"
TRELLIS_END = "<!-- trellis:end -->"


def ensure_pr_metadata_defaults(data: dict[str, Any]) -> bool:
    """Add missing PR-first metadata fields to a task dict.

    Mutates the provided dict in place and preserves every existing unknown
    field. Returns True if any defaults were added.
    """
    changed = False
    for key, value in PR_METADATA_DEFAULTS.items():
        if key not in data:
            data[key] = deepcopy(value)
            changed = True
    return changed


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _task_slug(task_dir: Path, data: dict[str, Any]) -> str:
    raw = data.get("name") or data.get("id")
    if isinstance(raw, str) and raw:
        return raw
    return re.sub(r"^\d{2}-\d{2}-", "", task_dir.name)


def _current_branch(repo_root: Path) -> str:
    _, branch_out, _ = run_git(["branch", "--show-current"], cwd=repo_root)
    return branch_out.strip() or "main"


def _resolve_optional_task_dir(task_arg: str | None, repo_root: Path) -> Path | None:
    if task_arg:
        return resolve_task_dir(task_arg, repo_root)

    current = get_current_task(repo_root)
    if current:
        return resolve_task_dir(current, repo_root)

    print(
        colored(
            "Error: task is required when no current task is set",
            Colors.RED,
        ),
        file=sys.stderr,
    )
    return None


def _load_task_data(
    task_arg: str | None,
    repo_root: Path,
) -> tuple[Path, Path, dict[str, Any]] | None:
    task_dir = _resolve_optional_task_dir(task_arg, repo_root)
    if task_dir is None:
        return None

    task_json = task_dir / FILE_TASK_JSON
    if not task_json.is_file():
        print(colored(f"Error: task.json not found at {task_dir}", Colors.RED), file=sys.stderr)
        return None

    data = read_json(task_json)
    if not data:
        print(colored(f"Error: could not read {task_json}", Colors.RED), file=sys.stderr)
        return None

    ensure_pr_metadata_defaults(data)
    return task_dir, task_json, data


def _write_task(task_json: Path, data: dict[str, Any]) -> bool:
    ensure_pr_metadata_defaults(data)
    if write_json(task_json, data):
        return True
    print(colored(f"Error: failed to write {task_json}", Colors.RED), file=sys.stderr)
    return False


def _json_print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _quote_arg(arg: str) -> str:
    if not arg:
        return '""'
    if re.search(r'[\s"]', arg):
        return json.dumps(arg)
    return arg


def _format_command(args: list[str]) -> str:
    return " ".join(_quote_arg(a) for a in args)


def _run_command(args: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def _gh_state() -> tuple[bool, str]:
    if shutil.which("gh") is None:
        return False, "GitHub CLI `gh` is not installed."

    rc, _, err = _run_command(["gh", "auth", "status"], cwd=get_repo_root())
    if rc != 0:
        detail = err.strip() or "`gh auth status` failed."
        return False, f"GitHub CLI is not authenticated. {detail}"
    return True, ""


def _normalized_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _merge_unique(existing: Any, incoming: list[str]) -> list[str]:
    result: list[str] = []
    for item in _normalized_list(existing) + incoming:
        if item not in result:
            result.append(item)
    return result


def _rel_or_abs(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return repo_root / path


def _branch_exists(repo_root: Path, branch: str) -> bool:
    rc, _, _ = run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=repo_root)
    return rc == 0


def _git_ref_exists(repo_root: Path, ref: str) -> bool:
    rc, _, _ = run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=repo_root)
    return rc == 0


def _has_origin_remote(repo_root: Path) -> bool:
    rc, out, _ = run_git(["remote", "get-url", "origin"], cwd=repo_root)
    return rc == 0 and bool(out.strip())


def _resolve_worktree_base_ref(repo_root: Path, base: str) -> str | None:
    if _git_ref_exists(repo_root, base):
        return base

    if not base.startswith("origin/") and _has_origin_remote(repo_root):
        run_git(["fetch", "origin"], cwd=repo_root)
        origin_ref = f"origin/{base}"
        if _git_ref_exists(repo_root, origin_ref):
            return origin_ref

    return None


def _is_git_repo(repo_root: Path) -> bool:
    rc, out, _ = run_git(["rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    return rc == 0 and out.strip() == "true"


def _is_dirty(repo_root: Path) -> bool:
    rc, out, _ = run_git(["status", "--porcelain"], cwd=repo_root)
    return rc == 0 and bool(out)


def _worktree_git_args(
    repo_root: Path,
    branch: str,
    base: str,
    path_value: str,
    force: bool,
) -> list[str]:
    args = ["worktree", "add"]
    if force:
        args.append("--force")
    if _branch_exists(repo_root, branch):
        args.extend([path_value, branch])
    else:
        args.extend(["-b", branch, path_value, base])
    return args


def cmd_worktree(args: argparse.Namespace) -> int:
    """Create a git worktree for a task and update task metadata."""
    repo_root = get_repo_root()
    loaded = _load_task_data(args.task, repo_root)
    if loaded is None:
        return 1
    task_dir, task_json, data = loaded

    slug = _task_slug(task_dir, data)
    base = args.base or data.get("base_branch") or _current_branch(repo_root)
    branch = args.branch or data.get("branch") or f"task/{slug}"
    path_value = args.path or data.get("worktree_path") or f"../trellis-worktrees/{slug}"
    dry_run = bool(getattr(args, "dry_run", False))
    json_mode = bool(getattr(args, "json", False))
    git_args = _worktree_git_args(repo_root, str(branch), str(base), str(path_value), bool(args.force))
    command = ["git"] + git_args

    payload = {
        "task": task_dir.name,
        "branch": branch,
        "base": base,
        "path": path_value,
        "command": command,
        "dry_run": dry_run,
    }

    if dry_run:
        if json_mode:
            _json_print({"ok": True, **payload})
        else:
            print(colored("Worktree dry run:", Colors.BLUE))
            print(f"  {_format_command(command)}")
            print("No task metadata was changed.")
        return 0

    if not _is_git_repo(repo_root):
        print(colored("Error: not inside a git repository", Colors.RED), file=sys.stderr)
        print("Next step: run this command from a git-backed Trellis project.", file=sys.stderr)
        return 1

    if _is_dirty(repo_root) and not json_mode:
        print(
            colored(
                "Warning: current working tree has uncommitted changes; the new worktree will not include them.",
                Colors.YELLOW,
            ),
            file=sys.stderr,
        )

    base_ref = _resolve_worktree_base_ref(repo_root, str(base))
    if base_ref is None:
        print(colored(f"Error: base branch/ref not found: {base}", Colors.RED), file=sys.stderr)
        print(f"Next step: fetch or create `{base}`, or pass --base <ref>.", file=sys.stderr)
        return 1

    git_args = _worktree_git_args(repo_root, str(branch), base_ref, str(path_value), bool(args.force))
    command = ["git"] + git_args

    worktree_path = _rel_or_abs(str(path_value), repo_root)
    if worktree_path.exists() and not args.force:
        print(colored(f"Error: worktree path already exists: {path_value}", Colors.RED), file=sys.stderr)
        print("Next step: choose --path <path>, remove the existing directory, or retry with --force.", file=sys.stderr)
        return 1

    rc, out, err = run_git(git_args, cwd=repo_root)
    if rc != 0:
        print(colored("Error: git worktree creation failed", Colors.RED), file=sys.stderr)
        if err.strip():
            print(err.strip(), file=sys.stderr)
        elif out.strip():
            print(out.strip(), file=sys.stderr)
        print(f"Command: {_format_command(command)}", file=sys.stderr)
        return 1

    data["branch"] = branch
    data["base_branch"] = base
    data["worktree_path"] = path_value
    if not _write_task(task_json, data):
        return 1

    if json_mode:
        _json_print({"ok": True, **payload})
    else:
        print(colored(f"✓ Worktree ready: {path_value}", Colors.GREEN))
        print(f"  Branch: {branch}")
        print(f"  Base: {base}")
    return 0


def _read_optional_file(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_markdown_section(content: str, names: tuple[str, ...]) -> str:
    if not content:
        return ""

    wanted = {name.lower() for name in names}
    lines = content.splitlines()
    capture = False
    start_level = 0
    captured: list[str] = []

    for line in lines:
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip().lower()
            if capture and level <= start_level:
                break
            if title in wanted:
                capture = True
                start_level = level
                captured = []
                continue
        if capture:
            captured.append(line)

    return "\n".join(captured).strip()


def _extract_acceptance_criteria(prd: str) -> str:
    section = _extract_markdown_section(prd, ("acceptance criteria", "acceptance"))
    if section:
        return section
    matches = [line for line in prd.splitlines() if re.match(r"\s*-\s+\[[ xX]\]\s+", line)]
    return "\n".join(matches).strip()


def _format_value_list(value: Any, fallback: str) -> str:
    items = _normalized_list(value)
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def _format_validation(data: dict[str, Any]) -> str:
    validation = data.get("validation")
    if isinstance(validation, dict):
        lines = [f"- {key}: {value}" for key, value in validation.items()]
        return "\n".join(lines) if lines else "- Not recorded yet."
    return _format_value_list(validation, "Not recorded yet.")


def build_trellis_pr_section(task_dir: Path, data: dict[str, Any]) -> str:
    """Build the Trellis-managed section for a PR body."""
    ensure_pr_metadata_defaults(data)
    prd = _read_optional_file(task_dir / "prd.md")
    info = _read_optional_file(task_dir / "info.md")
    goal = _extract_markdown_section(prd, ("goal",)) or data.get("description") or "Not recorded."
    acceptance = _extract_acceptance_criteria(prd) or "- Not recorded."
    what_changed = data.get("what_changed") or data.get("changes")
    reviewer_focus = data.get("reviewer_focus")
    risk = data.get("risk") or "Review the PR diff and validation evidence before merging."
    rollback = data.get("rollback") or "Revert the PR or reset the task branch to the integration branch."
    issue = data.get("issue_url") or "None"
    labels = ", ".join(_normalized_list(data.get("labels"))) or "None"
    reviewers = ", ".join(_normalized_list(data.get("reviewers"))) or "None"
    base = data.get("base_branch") or "unknown"
    branch = data.get("branch") or "unknown"
    pr_status = data.get("pr_status") or "not created"
    review_status = data.get("review_status") or "not reviewed"
    ci_status = data.get("ci_status") or "unknown"
    agent_review = data.get("last_agent_review_at") or "No local agent review recorded yet."
    info_note = ""
    if info:
        info_note = "\n\nTechnical design notes are recorded in `info.md`."

    return "\n".join(
        [
            TRELLIS_START,
            "## Trellis Task",
            "",
            f"- Task: `{task_dir.name}`",
            f"- Title: {data.get('title') or data.get('name') or task_dir.name}",
            f"- Branch: `{branch}`",
            f"- Base: `{base}`",
            f"- PR status: {pr_status}",
            f"- Review status: {review_status}",
            f"- CI status: {ci_status}",
            f"- Issue: {issue}",
            f"- Labels: {labels}",
            f"- Reviewers: {reviewers}",
            "",
            "## Goal",
            "",
            str(goal).strip() + info_note,
            "",
            "## Acceptance Criteria",
            "",
            acceptance,
            "",
            "## What Changed",
            "",
            _format_value_list(what_changed, "Implementation details are in the PR diff."),
            "",
            "## Validation Evidence",
            "",
            _format_validation(data),
            "",
            "## Reviewer Focus",
            "",
            _format_value_list(reviewer_focus, "Check acceptance criteria, validation evidence, and rollback safety."),
            "",
            "## Agent Review",
            "",
            f"- Last agent review: {agent_review}",
            f"- Review status: {review_status}",
            "",
            "## Risk / Rollback",
            "",
            f"- Risk: {risk}",
            f"- Rollback: {rollback}",
            TRELLIS_END,
        ]
    )


def replace_trellis_managed_section(body: str, managed_section: str) -> str:
    """Replace the Trellis-managed PR body section while preserving human text."""
    start = body.find(TRELLIS_START)
    end = body.find(TRELLIS_END)
    managed = managed_section.strip()
    if start != -1 and end != -1 and end > start:
        end += len(TRELLIS_END)
        return body[:start].rstrip() + "\n\n" + managed + "\n\n" + body[end:].lstrip()
    if body.strip():
        return body.rstrip() + "\n\n" + managed + "\n"
    return managed + "\n"


def _apply_pr_option_metadata(data: dict[str, Any], args: argparse.Namespace) -> None:
    labels = _merge_unique(data.get("labels"), list(args.label or []))
    reviewers = _merge_unique(data.get("reviewers"), list(args.reviewer or []))
    data["labels"] = labels
    data["reviewers"] = reviewers
    if args.milestone:
        data["milestone"] = args.milestone
    if args.issue:
        data["issue_url"] = args.issue


def _default_pr_title(data: dict[str, Any], task_dir: Path) -> str:
    title = data.get("title") or data.get("name") or task_dir.name
    scope = data.get("scope")
    if isinstance(scope, str) and scope:
        return f"{scope}: {title}"
    return str(title)


def _default_pr_body_path(task_dir: Path) -> Path:
    return task_dir / "pr-body.md"


def _create_pr_body(task_dir: Path, data: dict[str, Any], body_file: str | None) -> str:
    managed = build_trellis_pr_section(task_dir, data)
    source = Path(body_file) if body_file else _default_pr_body_path(task_dir)
    if not source.is_file():
        return managed + "\n"
    existing = source.read_text(encoding="utf-8", errors="replace")
    return replace_trellis_managed_section(existing, managed)


def _pr_create_command(
    base: str,
    head: str,
    title: str,
    body_file: str,
    draft: bool,
    labels: list[str],
    milestone: str | None,
    reviewers: list[str],
) -> list[str]:
    cmd = [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--head",
        head,
        "--title",
        title,
        "--body-file",
        body_file,
    ]
    if draft:
        cmd.append("--draft")
    for label in labels:
        cmd.extend(["--label", label])
    if milestone:
        cmd.extend(["--milestone", milestone])
    for reviewer in reviewers:
        cmd.extend(["--reviewer", reviewer])
    return cmd


def _existing_pr(repo_root: Path, head: str, base: str) -> dict[str, Any] | None:
    rc, out, _ = _run_command(
        [
            "gh",
            "pr",
            "list",
            "--head",
            head,
            "--base",
            base,
            "--state",
            "open",
            "--json",
            "number,url,state,isDraft,headRefName,baseRefName,title",
            "--limit",
            "1",
        ],
        cwd=repo_root,
    )
    if rc != 0 or not out.strip():
        return None
    try:
        prs = json.loads(out)
    except json.JSONDecodeError:
        return None
    if isinstance(prs, list) and prs:
        item = prs[0]
        if isinstance(item, dict):
            return item
    return None


def _parse_pr_url(url: str) -> int | None:
    match = re.search(r"/pull/(\d+)(?:\D|$)", url)
    if not match:
        return None
    return int(match.group(1))


def _update_from_pr_info(data: dict[str, Any], info: dict[str, Any]) -> None:
    number = info.get("number")
    if isinstance(number, int):
        data["pr_number"] = number
    url = info.get("url")
    if isinstance(url, str) and url:
        data["pr_url"] = url
    is_draft = bool(info.get("isDraft"))
    state = str(info.get("state") or "open").lower()
    data["pr_status"] = "draft" if is_draft else state
    head = info.get("headRefName")
    base = info.get("baseRefName")
    if isinstance(head, str) and head:
        data["branch"] = head
    if isinstance(base, str) and base:
        data["base_branch"] = base
    review_decision = info.get("reviewDecision")
    if isinstance(review_decision, str) and review_decision:
        data["review_status"] = review_decision.lower()
    data["last_pr_sync_at"] = _now_iso()


def _write_local_pr_body(task_dir: Path, body: str) -> Path:
    body_path = _default_pr_body_path(task_dir)
    body_path.write_text(body, encoding="utf-8")
    return body_path


def _print_manual_pr_commands(commands: list[list[str]]) -> None:
    print(colored("GitHub PR was not created automatically.", Colors.YELLOW), file=sys.stderr)
    print("Manual next steps:", file=sys.stderr)
    for command in commands:
        print(f"  {_format_command(command)}", file=sys.stderr)


def cmd_create_pr(args: argparse.Namespace) -> int:
    """Create a PR, or stage local PR metadata when gh is unavailable."""
    repo_root = get_repo_root()
    loaded = _load_task_data(args.task, repo_root)
    if loaded is None:
        return 1
    task_dir, task_json, data = loaded

    _apply_pr_option_metadata(data, args)
    base = args.base or data.get("base_branch") or _current_branch(repo_root)
    head = args.head or data.get("branch") or _current_branch(repo_root)
    title = args.title or _default_pr_title(data, task_dir)
    data["base_branch"] = base
    data["branch"] = head
    body = _create_pr_body(task_dir, data, args.body_file)
    labels = _normalized_list(data.get("labels"))
    reviewers = _normalized_list(data.get("reviewers"))
    milestone = data.get("milestone")
    milestone_arg = milestone if isinstance(milestone, str) and milestone else None
    dry_run = bool(args.dry_run)
    json_mode = bool(args.json)
    body_display = str(_default_pr_body_path(task_dir))
    create_cmd = _pr_create_command(
        str(base),
        str(head),
        str(title),
        body_display,
        bool(args.draft),
        labels,
        milestone_arg,
        reviewers,
    )
    commands: list[list[str]] = []
    if args.push:
        commands.append(["git", "push", "-u", "origin", str(head)])
    commands.append(create_cmd)

    if dry_run:
        payload = {
            "ok": True,
            "dry_run": True,
            "task": task_dir.name,
            "base": base,
            "head": head,
            "title": title,
            "commands": commands,
            "body": body,
        }
        if json_mode:
            _json_print(payload)
        else:
            print(colored("PR creation dry run:", Colors.BLUE))
            for command in commands:
                print(f"  {_format_command(command)}")
            print("No task metadata was changed.")
        return 0

    gh_ok, gh_reason = _gh_state()
    if not gh_ok:
        body_path = _write_local_pr_body(task_dir, body)
        fallback_create_cmd = _pr_create_command(
            str(base),
            str(head),
            str(title),
            str(body_path),
            bool(args.draft),
            labels,
            milestone_arg,
            reviewers,
        )
        fallback_commands: list[list[str]] = []
        if args.push:
            fallback_commands.append(["git", "push", "-u", "origin", str(head)])
        fallback_commands.append(fallback_create_cmd)
        data["pr_status"] = "local_only"
        data["review_status"] = "draft" if args.draft else "needs_pr"
        data["last_pr_sync_at"] = _now_iso()
        if not _write_task(task_json, data):
            return 1
        if json_mode:
            _json_print(
                {
                    "ok": True,
                    "mode": "local_only",
                    "reason": gh_reason,
                    "body_file": str(body_path),
                    "commands": fallback_commands,
                }
            )
        else:
            print(colored(gh_reason, Colors.YELLOW), file=sys.stderr)
            _print_manual_pr_commands(fallback_commands)
            print(colored(f"✓ Local PR draft staged: {body_path}", Colors.GREEN))
        return 0

    existing = _existing_pr(repo_root, str(head), str(base))
    if existing is not None:
        _update_from_pr_info(data, existing)
        if not _write_task(task_json, data):
            return 1
        if json_mode:
            _json_print({"ok": True, "existing": True, "pr": existing})
        else:
            print(colored(f"✓ Existing PR found: {existing.get('url')}", Colors.GREEN))
        return 0

    if args.push:
        rc, out, err = run_git(["push", "-u", "origin", str(head)], cwd=repo_root)
        if rc != 0:
            print(colored("Error: git push failed before PR creation", Colors.RED), file=sys.stderr)
            print((err or out).strip(), file=sys.stderr)
            print("Next step: push the branch manually or retry with --no-push.", file=sys.stderr)
            return 1

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        tmp_body = handle.name

    try:
        cmd = _pr_create_command(
            str(base),
            str(head),
            str(title),
            tmp_body,
            bool(args.draft),
            labels,
            milestone_arg,
            reviewers,
        )
        rc, out, err = _run_command(cmd, cwd=repo_root)
    finally:
        Path(tmp_body).unlink(missing_ok=True)

    if rc != 0:
        print(colored("Error: gh pr create failed", Colors.RED), file=sys.stderr)
        print((err or out).strip(), file=sys.stderr)
        return 1

    pr_url = out.strip().splitlines()[-1] if out.strip() else ""
    data["pr_url"] = pr_url or data.get("pr_url")
    parsed = _parse_pr_url(pr_url)
    if parsed is not None:
        data["pr_number"] = parsed
    data["pr_status"] = "draft" if args.draft else "open"
    data["review_status"] = "draft" if args.draft else "ready_for_review"
    data["last_pr_sync_at"] = _now_iso()
    if not _write_task(task_json, data):
        return 1

    if json_mode:
        _json_print({"ok": True, "pr_url": data.get("pr_url"), "pr_number": data.get("pr_number")})
    else:
        print(colored(f"✓ PR ready: {data.get('pr_url') or '(created)'}", Colors.GREEN))
    return 0


def _pr_identifier(data: dict[str, Any], args: argparse.Namespace) -> str | None:
    explicit = getattr(args, "pr", None)
    if explicit:
        return str(explicit)
    number = data.get("pr_number")
    if isinstance(number, int):
        return str(number)
    url = data.get("pr_url")
    if isinstance(url, str) and url:
        return url
    branch = data.get("branch")
    if isinstance(branch, str) and branch:
        return branch
    return None


def _view_pr(repo_root: Path, identifier: str) -> dict[str, Any] | None:
    rc, out, err = _run_command(
        [
            "gh",
            "pr",
            "view",
            identifier,
            "--json",
            "number,url,state,isDraft,headRefName,baseRefName,reviewDecision,statusCheckRollup,body,title",
        ],
        cwd=repo_root,
    )
    if rc != 0:
        print(colored("Error: gh pr view failed", Colors.RED), file=sys.stderr)
        print(err.strip(), file=sys.stderr)
        return None
    try:
        parsed = json.loads(out)
    except json.JSONDecodeError:
        print(colored("Error: gh returned invalid JSON", Colors.RED), file=sys.stderr)
        return None
    return parsed if isinstance(parsed, dict) else None


def _ci_status_from_rollup(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    states: list[str] = []
    for item in value:
        if isinstance(item, dict):
            state = item.get("conclusion") or item.get("status") or item.get("state")
            if isinstance(state, str):
                states.append(state.lower())
    if not states:
        return None
    if any(s in ("failure", "failed", "cancelled", "timed_out", "action_required") for s in states):
        return "failing"
    if any(s in ("pending", "queued", "in_progress", "waiting", "requested") for s in states):
        return "pending"
    if all(s in ("success", "completed", "neutral", "skipped") for s in states):
        return "passing"
    return "unknown"


def cmd_sync_pr(args: argparse.Namespace) -> int:
    """Sync PR metadata and the Trellis-managed PR body section."""
    repo_root = get_repo_root()
    loaded = _load_task_data(args.task, repo_root)
    if loaded is None:
        return 1
    task_dir, task_json, data = loaded
    dry_run = bool(args.dry_run)
    json_mode = bool(args.json)

    if args.body_file:
        body_path = Path(args.body_file)
        current_body = body_path.read_text(encoding="utf-8", errors="replace")
        updated_body = replace_trellis_managed_section(
            current_body,
            build_trellis_pr_section(task_dir, data),
        )
        changed = updated_body != current_body
        if not dry_run and changed:
            body_path.write_text(updated_body, encoding="utf-8")
            data["last_pr_sync_at"] = _now_iso()
            if not _write_task(task_json, data):
                return 1
        if json_mode:
            _json_print({"ok": True, "dry_run": dry_run, "body_changed": changed})
        else:
            print(colored("✓ Trellis PR body section is current", Colors.GREEN))
        return 0

    gh_ok, gh_reason = _gh_state()
    if not gh_ok:
        body_path = _default_pr_body_path(task_dir)
        current_body = _read_optional_file(body_path)
        updated_body = replace_trellis_managed_section(
            current_body,
            build_trellis_pr_section(task_dir, data),
        )
        changed = updated_body != current_body
        if not dry_run:
            if changed:
                body_path.write_text(updated_body, encoding="utf-8")
            if data.get("pr_status") in (None, "", "none"):
                data["pr_status"] = "local_only"
            data["last_pr_sync_at"] = _now_iso()
            if not _write_task(task_json, data):
                return 1
        if json_mode:
            _json_print(
                {
                    "ok": True,
                    "dry_run": dry_run,
                    "mode": "local_only",
                    "reason": gh_reason,
                    "body_file": str(body_path),
                    "body_changed": changed,
                }
            )
        else:
            print(colored(gh_reason, Colors.YELLOW), file=sys.stderr)
            if dry_run:
                print(colored(f"Sync PR dry run: would write {body_path}", Colors.BLUE))
            else:
                print(colored(f"✓ Wrote local PR body: {body_path}", Colors.GREEN))
        return 0

    identifier = _pr_identifier(data, args)
    if identifier is None:
        print(colored("Error: no PR identifier available", Colors.RED), file=sys.stderr)
        print("Next step: pass --pr <number|url> or run create-pr first.", file=sys.stderr)
        return 1

    info = _view_pr(repo_root, identifier)
    if info is None:
        return 1
    _update_from_pr_info(data, info)
    ci_status = _ci_status_from_rollup(info.get("statusCheckRollup"))
    if ci_status:
        data["ci_status"] = ci_status

    current_body = str(info.get("body") or "")
    updated_body = replace_trellis_managed_section(
        current_body,
        build_trellis_pr_section(task_dir, data),
    )
    changed = updated_body != current_body

    if not dry_run and changed:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
            handle.write(updated_body)
            tmp_body = handle.name
        try:
            rc, _, err = _run_command(["gh", "pr", "edit", identifier, "--body-file", tmp_body], cwd=repo_root)
        finally:
            Path(tmp_body).unlink(missing_ok=True)
        if rc != 0:
            print(colored("Error: gh pr edit failed", Colors.RED), file=sys.stderr)
            print(err.strip(), file=sys.stderr)
            return 1

    if not dry_run and not _write_task(task_json, data):
        return 1

    if json_mode:
        _json_print({"ok": True, "dry_run": dry_run, "body_changed": changed, "pr": info})
    else:
        print(colored("✓ PR metadata synced", Colors.GREEN))
        if changed:
            print("  Updated Trellis-managed body section")
    return 0


def _write_review_artifact(
    repo_root: Path,
    task_dir: Path,
    data: dict[str, Any],
) -> Path:
    review_dir = task_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = review_dir / f"pr-review-{timestamp}.md"
    base = str(data.get("base_branch") or "main")
    head = str(data.get("branch") or _current_branch(repo_root))
    _, stat, _ = run_git(["diff", "--stat", f"{base}...{head}"], cwd=repo_root)
    _, names, _ = run_git(["diff", "--name-status", f"{base}...{head}"], cwd=repo_root)
    rc_check, check_out, check_err = run_git(["diff", "--check", f"{base}...{head}"], cwd=repo_root)
    check_text = "No whitespace errors reported." if rc_check == 0 else (check_err or check_out).strip()
    content = "\n".join(
        [
            "# Trellis PR Review",
            "",
            f"- Task: `{task_dir.name}`",
            f"- Branch: `{head}`",
            f"- Base: `{base}`",
            f"- Generated: {_now_iso()}",
            "",
            "## Changed Files",
            "",
            "```text",
            names.strip() or "(none)",
            "```",
            "",
            "## Diff Stat",
            "",
            "```text",
            stat.strip() or "(none)",
            "```",
            "",
            "## Diff Check",
            "",
            "```text",
            check_text,
            "```",
            "",
            "## Reviewer Notes",
            "",
            "- Verify acceptance criteria against the PR diff.",
            "- Confirm validation evidence before marking the PR ready.",
            "",
        ]
    )
    target.write_text(content, encoding="utf-8")
    return target


def cmd_review_pr(args: argparse.Namespace) -> int:
    """Write a local review artifact for the task PR."""
    repo_root = get_repo_root()
    loaded = _load_task_data(args.task, repo_root)
    if loaded is None:
        return 1
    task_dir, task_json, data = loaded
    dry_run = bool(args.dry_run)

    if dry_run:
        planned = task_dir / "review" / "pr-review-<timestamp>.md"
        if args.json:
            _json_print({"ok": True, "dry_run": True, "path": str(planned)})
        else:
            print(colored(f"Review dry run: would write {planned}", Colors.BLUE))
        return 0

    artifact = _write_review_artifact(repo_root, task_dir, data)
    data["review_status"] = "agent_reviewed"
    data["last_agent_review_at"] = _now_iso()
    if not _write_task(task_json, data):
        return 1

    if args.json:
        _json_print({"ok": True, "path": str(artifact)})
    else:
        print(colored(f"✓ Review artifact written: {artifact}", Colors.GREEN))
    return 0


def cmd_finish_pr(args: argparse.Namespace) -> int:
    """Mark a task PR as ready for human review when gates pass."""
    repo_root = get_repo_root()
    loaded = _load_task_data(args.task, repo_root)
    if loaded is None:
        return 1
    _, task_json, data = loaded
    dry_run = bool(args.dry_run)
    json_mode = bool(args.json)

    if not args.force and data.get("pr_status") in (None, "", "none"):
        print(colored("Error: no task PR has been created or staged", Colors.RED), file=sys.stderr)
        print("Next step: run `task.py create-pr <task> --draft` first.", file=sys.stderr)
        return 1

    if not args.force and data.get("review_status") == "changes_requested":
        print(colored("Error: agent review requested changes", Colors.RED), file=sys.stderr)
        print("Next step: fix review findings, rerun `task.py review-pr <task>`, then retry.", file=sys.stderr)
        return 1

    if not args.force and data.get("review_status") not in (
        "agent_reviewed",
        "approved",
        "human_review_requested",
    ):
        print(colored("Error: no local PR review recorded", Colors.RED), file=sys.stderr)
        print("Next step: run `task.py review-pr <task>` or retry with --force.", file=sys.stderr)
        return 1

    if not args.force and data.get("ci_status") in ("failing", "failed"):
        print(colored(f"Error: CI is {data.get('ci_status')}", Colors.RED), file=sys.stderr)
        print("Next step: fix CI or retry with --force if this is a local-only PR.", file=sys.stderr)
        return 1

    identifier = _pr_identifier(data, args)
    gh_ok, _ = _gh_state()
    ready_command: list[str] | None = None
    if gh_ok and identifier and data.get("pr_status") == "draft":
        ready_command = ["gh", "pr", "ready", identifier]

    if dry_run:
        payload: dict[str, Any] = {"ok": True, "dry_run": True}
        if ready_command:
            payload["command"] = ready_command
        if json_mode:
            _json_print(payload)
        else:
            print(colored("Finish PR dry run:", Colors.BLUE))
            if ready_command:
                print(f"  {_format_command(ready_command)}")
            print("No task metadata was changed.")
        return 0

    if ready_command:
        rc, _, err = _run_command(ready_command, cwd=repo_root)
        if rc != 0:
            print(colored("Error: gh pr ready failed", Colors.RED), file=sys.stderr)
            print(err.strip(), file=sys.stderr)
            return 1

    data["review_status"] = "human_review_requested"
    if data.get("pr_status") in (None, "", "none", "draft"):
        data["pr_status"] = "ready_for_review"
    data["last_pr_sync_at"] = _now_iso()
    if not _write_task(task_json, data):
        return 1

    if json_mode:
        _json_print({"ok": True, "review_status": data["review_status"], "pr_status": data["pr_status"]})
    else:
        print(colored("✓ PR is ready for human review", Colors.GREEN))
        if not ready_command and data.get("pr_status") == "local_only":
            print("  Local-only PR state recorded; create the hosted PR when ready.")
    return 0
