# agent-equip v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish `agent-equip` v0.1 — an installer CLI that equips AI coding agents (Claude Code, Cursor, Windsurf, generic) with a GitHub skill backed by the official `gh` CLI.

**Architecture:** Two pluggable axes, every feature one file: `channels/` (platforms; v1 ships only `github`) and `agents/` (adapter per coding agent). An explicit registry wires them. The CLI (`install`/`doctor`/`list`/`uninstall`) orchestrates: check `gh`, detect agents, copy the bundled SKILL.md into each agent's skill/rules dir, record every write in `~/.agent-equip/manifest.json` for surgical uninstall. Zero credentials stored; safe by default (system commands printed, only run with `--auto`).

**Tech Stack:** Python ≥3.10, Typer ≥0.12, pytest, ruff, hatchling, GitHub Actions (ubuntu/macos/windows × 3.10–3.12).

**Spec:** `docs/superpowers/specs/2026-06-10-agent-equip-design.md` (approved)

**Working directory:** `/Users/ali/Documents/GitHub/agent-equip` — all paths below are relative to it. Git repo already initialized on `main` (contains only `docs/`).

**Conventions for all tasks:**
- Run tests with `python -m pytest` from the repo root (venv: `.venv`).
- All file writes in source code use `encoding="utf-8"`.
- CLI output uses ASCII status icons (`[ok]`, `[!]`, `[x]`) — no Unicode symbols (Windows cp1252 consoles crash on them).

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `README.md` (stub — full version in Task 16)
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `src/agent_equip/__init__.py`
- Create: `src/agent_equip/cli.py` (minimal — expanded in Tasks 12–14)
- Create: `tests/__init__.py` (empty file)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-equip"
version = "0.1.0"
description = "Set up GitHub superpowers for any AI coding agent in one command."
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [{ name = "shenmali" }]
dependencies = ["typer>=0.12"]

[project.urls]
Homepage = "https://github.com/shenmali/agent-equip"

[project.scripts]
agent-equip = "agent_equip.cli:app"

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4"]

[tool.hatch.build.targets.wheel]
packages = ["src/agent_equip"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create stub `README.md`**

```markdown
# agent-equip

Set up GitHub superpowers for any AI coding agent in one command.

Work in progress — full docs ship with v0.1.
```

- [ ] **Step 3: Create `LICENSE` (MIT)**

```text
MIT License

Copyright (c) 2026 shenmali

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Create `.gitignore`**

```text
__pycache__/
*.egg-info/
.venv/
dist/
build/
.pytest_cache/
.ruff_cache/
.DS_Store
```

- [ ] **Step 5: Create `src/agent_equip/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 6: Create minimal `src/agent_equip/cli.py`**

```python
import typer

app = typer.Typer(no_args_is_help=True, help="Equip AI coding agents with platform skills.")


@app.command()
def version() -> None:
    """Print the agent-equip version."""
    from . import __version__

    typer.echo(__version__)
```

- [ ] **Step 7: Create empty `tests/__init__.py`, set up venv, install editable**

Run:
```bash
cd /Users/ali/Documents/GitHub/agent-equip
touch tests/__init__.py
python3 -m venv .venv
.venv/bin/pip install -q -e ".[dev]"
```
Expected: install succeeds with no errors.

- [ ] **Step 8: Smoke-test the entry point**

Run: `.venv/bin/agent-equip version`
Expected output: `0.1.0`

Run: `.venv/bin/python -m pytest`
Expected: `no tests ran` (exit code 5 is fine at this stage).

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml README.md LICENSE .gitignore src/ tests/
git commit -m "chore: scaffold agent-equip package with Typer CLI entry point"
```

---

### Task 2: Channel base — `CheckResult` and `Channel` ABC

**Files:**
- Create: `src/agent_equip/channels/__init__.py` (empty)
- Create: `src/agent_equip/channels/base.py`
- Test: `tests/test_channels.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_channels.py`:
```python
import pytest

from agent_equip.channels.base import Channel, CheckResult


def test_check_result_defaults():
    res = CheckResult(status="ok", message="all good")
    assert res.status == "ok"
    assert res.message == "all good"
    assert res.fix_hint is None


def test_check_result_with_fix_hint():
    res = CheckResult(status="fail", message="gh missing", fix_hint="brew install gh")
    assert res.fix_hint == "brew install gh"


def test_channel_is_abstract():
    with pytest.raises(TypeError):
        Channel()  # type: ignore[abstract]


def test_channel_subclass_contract(tmp_path):
    class Dummy(Channel):
        name = "dummy"
        description = "a dummy channel"

        def check(self):
            return CheckResult("ok", "fine")

        def skill_source(self):
            return tmp_path / "SKILL.md"

    ch = Dummy()
    assert ch.name == "dummy"
    assert ch.check().status == "ok"
    assert ch.skill_source().name == "SKILL.md"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_channels.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.channels'`

- [ ] **Step 3: Implement `src/agent_equip/channels/base.py`** (and empty `channels/__init__.py`)

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Status = Literal["ok", "warn", "fail"]


@dataclass
class CheckResult:
    """Outcome of a channel health check."""

    status: Status
    message: str
    fix_hint: str | None = None


class Channel(ABC):
    """A platform an agent can be equipped for (e.g. GitHub)."""

    name: str
    description: str

    @abstractmethod
    def check(self) -> CheckResult:
        """Report whether this channel's upstream tooling is ready."""

    @abstractmethod
    def skill_source(self) -> Path:
        """Path to the bundled SKILL.md delivered to agents."""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_channels.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/channels/ tests/test_channels.py
git commit -m "feat: add Channel base interface and CheckResult"
```

---

### Task 3: Bundled GitHub skill content

**Files:**
- Create: `src/agent_equip/skills/__init__.py` (empty)
- Create: `src/agent_equip/skills/github/SKILL.md`

- [ ] **Step 1: Create `src/agent_equip/skills/github/SKILL.md`** with exactly this content:

````markdown
---
name: github
description: Work with GitHub repos, issues, pull requests, releases, and search using the gh CLI. Use whenever the user asks about a GitHub repository, issues, PRs, releases, CI runs, or wants to search GitHub.
---

# GitHub via the gh CLI

Use the official `gh` CLI for all GitHub work. It is installed and authenticated on this machine (if a command fails with an auth error, see Troubleshooting below).

## Ground rules

- Prefer `gh` subcommands; for anything without a subcommand, use `gh api <endpoint>`.
- Need machine-readable output? Add `--json <fields>` and filter with `--jq <expr>`.
- Destructive actions (deleting repos, force-pushing, closing others' issues) require explicit user confirmation first.
- For public repos, `gh` works even without auth for many read operations — try before declaring failure.

## Recipes

### Inspect a repo

```bash
gh repo view owner/repo                        # README + metadata
gh repo view owner/repo --json description,stargazerCount,primaryLanguage,licenseInfo
gh repo clone owner/repo                       # clone (uses your auth)
gh api repos/owner/repo/languages              # language breakdown
gh api repos/owner/repo/commits --jq '.[0:5] | .[] | .commit.message'   # last 5 commit messages
```

### Search GitHub

```bash
gh search repos "vector database" --language=rust --sort=stars --limit 10
gh search code "def parse_config" --repo owner/repo
gh search issues "memory leak" --repo owner/repo --state open
gh search prs "fix auth" --repo owner/repo --merged
```

### Issues

```bash
gh issue list --repo owner/repo --state open --limit 20
gh issue view 123 --repo owner/repo --comments
gh issue create --repo owner/repo --title "Bug: ..." --body "..."
gh issue comment 123 --repo owner/repo --body "..."
```

### Pull requests

```bash
gh pr list --repo owner/repo --state open
gh pr view 42 --repo owner/repo --comments
gh pr diff 42 --repo owner/repo
gh pr checkout 42                              # inside a clone
gh pr create --title "..." --body "..."        # from current branch
gh pr review 42 --approve --body "LGTM"
```

### Releases and CI

```bash
gh release list --repo owner/repo
gh release view v1.2.0 --repo owner/repo
gh run list --repo owner/repo --limit 10       # recent CI runs
gh run view <run-id> --repo owner/repo --log-failed
```

### Anything else: gh api

```bash
gh api repos/owner/repo/stats/participation    # weekly commit activity
gh api user                                    # who am I
gh api -X POST repos/owner/repo/forks          # fork a repo
```

## Troubleshooting

- **Auth errors / 401:** run `gh auth status`; if logged out, ask the user to run `gh auth login` (interactive).
- **404 on a repo that should exist:** likely a private repo and the current auth lacks access — check `gh auth status` output for the active account.
- **403 rate limit:** check `gh api rate_limit`; authenticated requests get much higher limits, so make sure auth is active.
- **`gh: command not found`:** ask the user to run `agent-equip doctor` for install guidance.
````

- [ ] **Step 2: Verify the file parses as expected**

Run: `head -4 src/agent_equip/skills/github/SKILL.md`
Expected: first line `---`, second line starting `name: github`.

- [ ] **Step 3: Commit**

```bash
git add src/agent_equip/skills/
git commit -m "feat: add bundled GitHub SKILL.md content"
```

---

### Task 4: GitHub channel

**Files:**
- Create: `src/agent_equip/channels/github.py`
- Modify: `tests/test_channels.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_channels.py`**

```python
import subprocess
from types import SimpleNamespace

from agent_equip.channels.github import GitHubChannel, gh_install_hint


def test_github_check_fail_when_gh_missing(monkeypatch):
    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: None)
    res = GitHubChannel().check()
    assert res.status == "fail"
    assert res.fix_hint == gh_install_hint()


def test_github_check_ok_when_authenticated(monkeypatch):
    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr(
        "agent_equip.channels.github.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0),
    )
    res = GitHubChannel().check()
    assert res.status == "ok"


def test_github_check_warn_when_not_authenticated(monkeypatch):
    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr(
        "agent_equip.channels.github.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=1),
    )
    res = GitHubChannel().check()
    assert res.status == "warn"
    assert "gh auth login" in (res.fix_hint or "")


def test_github_check_warn_on_timeout(monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="gh", timeout=5)

    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr("agent_equip.channels.github.subprocess.run", boom)
    res = GitHubChannel().check()
    assert res.status == "warn"


def test_github_skill_source_exists():
    src = GitHubChannel().skill_source()
    assert src.is_file()
    assert src.name == "SKILL.md"
    assert "gh " in src.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_channels.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.channels.github'` (the 4 base tests still pass).

- [ ] **Step 3: Implement `src/agent_equip/channels/github.py`**

```python
from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

from .base import Channel, CheckResult

_INSTALL_HINTS = {
    "Darwin": "brew install gh",
    "Linux": "sudo apt install gh  (or see https://cli.github.com)",
    "Windows": "winget install --id GitHub.cli",
}


def gh_install_hint() -> str:
    """OS-appropriate command for installing the gh CLI."""
    return _INSTALL_HINTS.get(platform.system(), "see https://cli.github.com")


class GitHubChannel(Channel):
    name = "github"
    description = "GitHub repos, issues, and PRs via the official gh CLI"

    def check(self) -> CheckResult:
        gh = shutil.which("gh")
        if gh is None:
            return CheckResult("fail", "gh CLI not found on PATH", fix_hint=gh_install_hint())
        try:
            proc = subprocess.run(
                [gh, "auth", "status"], capture_output=True, text=True, timeout=5
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return CheckResult(
                "warn",
                f"could not check gh auth status: {exc}",
                fix_hint="run `gh auth status` manually",
            )
        if proc.returncode == 0:
            return CheckResult("ok", "gh CLI installed and authenticated")
        return CheckResult(
            "warn", "gh CLI installed but not authenticated", fix_hint="run `gh auth login`"
        )

    def skill_source(self) -> Path:
        return Path(__file__).resolve().parent.parent / "skills" / "github" / "SKILL.md"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_channels.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/channels/github.py tests/test_channels.py
git commit -m "feat: add GitHub channel with gh CLI health check"
```

---

### Task 5: Agent adapter base — `InstallResult`, `strip_frontmatter`, `AgentAdapter`

**Files:**
- Create: `src/agent_equip/agents/__init__.py` (empty)
- Create: `src/agent_equip/agents/base.py`
- Test: `tests/test_agents.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_agents.py`:
```python
from pathlib import Path

from agent_equip.agents.base import AgentAdapter, InstallResult, strip_frontmatter
from agent_equip.channels.base import Channel, CheckResult


class FakeChannel(Channel):
    name = "fake"
    description = "fake channel"

    def __init__(self, skill_path: Path):
        self._skill_path = skill_path

    def check(self) -> CheckResult:
        return CheckResult("ok", "fine")

    def skill_source(self) -> Path:
        return self._skill_path


class DummyAdapter(AgentAdapter):
    name = "dummy"
    scope = "project"

    def detect(self) -> bool:
        return True

    def skill_target(self, channel: Channel) -> Path:
        return self.cwd / "rules" / f"{channel.name}.md"


def make_channel(tmp_path: Path, body: str = "---\nname: fake\n---\n\n# Fake skill\n") -> FakeChannel:
    skill = tmp_path / "SKILL.md"
    skill.write_text(body, encoding="utf-8")
    return FakeChannel(skill)


def test_strip_frontmatter_removes_yaml_block():
    text = "---\nname: x\ndescription: y\n---\n\n# Body\n"
    assert strip_frontmatter(text) == "# Body\n"


def test_strip_frontmatter_passthrough_without_block():
    assert strip_frontmatter("# Just body\n") == "# Just body\n"


def test_install_skill_fresh_install(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    result = ad.install_skill(ch)
    assert result == InstallResult("dummy", tmp_path / "proj" / "rules" / "fake.md", "installed")
    assert result.path.read_text(encoding="utf-8").startswith("---\nname: fake")


def test_install_skill_is_idempotent_skip(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    ad.install_skill(ch)
    assert ad.install_skill(ch).action == "skipped"


def test_install_skill_updates_changed_content(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    ad.install_skill(ch)
    ch.skill_source().write_text("---\nname: fake\n---\n\n# New body\n", encoding="utf-8")
    result = ad.install_skill(ch)
    assert result.action == "updated"
    assert "# New body" in result.path.read_text(encoding="utf-8")


def test_uninstall_skill_removes_file(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    result = ad.install_skill(ch)
    ad.uninstall_skill(ch)
    assert not result.path.exists()


def test_uninstall_skill_tolerates_missing_file(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    ad.uninstall_skill(ch)  # must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.agents'`

- [ ] **Step 3: Implement `src/agent_equip/agents/base.py`** (and empty `agents/__init__.py`)

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..channels.base import Channel

Action = Literal["installed", "updated", "skipped"]


@dataclass
class InstallResult:
    agent: str
    path: Path
    action: Action


def strip_frontmatter(text: str) -> str:
    """Drop a leading YAML frontmatter block (--- ... ---) if present."""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :].lstrip("\n")


class AgentAdapter(ABC):
    """A coding agent that can receive channel skills."""

    name: str
    scope: Literal["global", "project"]
    auto: bool = True  # False → only used with an explicit --agent flag

    def __init__(self, home: Path | None = None, cwd: Path | None = None) -> None:
        self.home = home or Path.home()
        self.cwd = cwd or Path.cwd()

    @abstractmethod
    def detect(self) -> bool:
        """Is this agent present (home dir for global scope, cwd for project scope)?"""

    @abstractmethod
    def skill_target(self, channel: Channel) -> Path:
        """Where the rendered skill lands for this agent."""

    def render(self, channel: Channel) -> str:
        """Skill content for this agent; default is the bundled SKILL.md verbatim."""
        return channel.skill_source().read_text(encoding="utf-8")

    def install_skill(self, channel: Channel) -> InstallResult:
        target = self.skill_target(channel)
        content = self.render(channel)
        if target.exists():
            action: Action = (
                "skipped" if target.read_text(encoding="utf-8") == content else "updated"
            )
        else:
            action = "installed"
        if action != "skipped":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return InstallResult(self.name, target, action)

    def uninstall_skill(self, channel: Channel) -> None:
        target = self.skill_target(channel)
        if target.exists():
            target.unlink()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/agents/ tests/test_agents.py
git commit -m "feat: add AgentAdapter base with idempotent skill install"
```

---

### Task 6: Claude Code adapter

**Files:**
- Create: `src/agent_equip/agents/claude_code.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_agents.py`**

```python
from agent_equip.agents.claude_code import ClaudeCodeAdapter


def test_claude_code_detect(tmp_path):
    ad = ClaudeCodeAdapter(home=tmp_path, cwd=tmp_path)
    assert ad.detect() is False
    (tmp_path / ".claude").mkdir()
    assert ad.detect() is True


def test_claude_code_is_global_scope_and_auto():
    assert ClaudeCodeAdapter.scope == "global"
    assert ClaudeCodeAdapter.auto is True


def test_claude_code_install_target_and_content(tmp_path):
    (tmp_path / ".claude").mkdir()
    ch = make_channel(tmp_path)
    ad = ClaudeCodeAdapter(home=tmp_path, cwd=tmp_path)
    result = ad.install_skill(ch)
    assert result.path == tmp_path / ".claude" / "skills" / "fake" / "SKILL.md"
    # Claude Code keeps the original frontmatter
    assert result.path.read_text(encoding="utf-8").startswith("---\nname: fake")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.agents.claude_code'`

- [ ] **Step 3: Implement `src/agent_equip/agents/claude_code.py`**

```python
from __future__ import annotations

from pathlib import Path

from ..channels.base import Channel
from .base import AgentAdapter


class ClaudeCodeAdapter(AgentAdapter):
    """Installs skills into Claude Code's global skills directory."""

    name = "claude-code"
    scope = "global"

    def detect(self) -> bool:
        return (self.home / ".claude").is_dir()

    def skill_target(self, channel: Channel) -> Path:
        return self.home / ".claude" / "skills" / channel.name / "SKILL.md"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/agents/claude_code.py tests/test_agents.py
git commit -m "feat: add Claude Code adapter (global scope)"
```

---

### Task 7: Cursor adapter

**Files:**
- Create: `src/agent_equip/agents/cursor.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_agents.py`**

```python
from agent_equip.agents.cursor import CursorAdapter


def test_cursor_detect_against_cwd(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    ad = CursorAdapter(home=tmp_path, cwd=proj)
    assert ad.detect() is False
    (proj / ".cursor").mkdir()
    assert ad.detect() is True


def test_cursor_renders_mdc_with_own_frontmatter(tmp_path):
    proj = tmp_path / "proj"
    (proj / ".cursor").mkdir(parents=True)
    ch = make_channel(tmp_path)
    ad = CursorAdapter(home=tmp_path, cwd=proj)
    result = ad.install_skill(ch)
    assert result.path == proj / ".cursor" / "rules" / "fake.mdc"
    text = result.path.read_text(encoding="utf-8")
    assert text.startswith("---\ndescription: fake channel\nalwaysApply: false\n---\n")
    assert "# Fake skill" in text
    assert "name: fake" not in text  # original frontmatter stripped
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.agents.cursor'`

- [ ] **Step 3: Implement `src/agent_equip/agents/cursor.py`**

```python
from __future__ import annotations

from pathlib import Path

from ..channels.base import Channel
from .base import AgentAdapter, strip_frontmatter


class CursorAdapter(AgentAdapter):
    """Installs rules into the current project's .cursor/rules directory."""

    name = "cursor"
    scope = "project"

    def detect(self) -> bool:
        return (self.cwd / ".cursor").is_dir()

    def skill_target(self, channel: Channel) -> Path:
        return self.cwd / ".cursor" / "rules" / f"{channel.name}.mdc"

    def render(self, channel: Channel) -> str:
        body = strip_frontmatter(super().render(channel))
        return f"---\ndescription: {channel.description}\nalwaysApply: false\n---\n\n{body}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/agents/cursor.py tests/test_agents.py
git commit -m "feat: add Cursor adapter rendering .mdc rules"
```

---

### Task 8: Windsurf adapter

**Files:**
- Create: `src/agent_equip/agents/windsurf.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_agents.py`**

```python
from agent_equip.agents.windsurf import WindsurfAdapter


def test_windsurf_detect_and_target(tmp_path):
    proj = tmp_path / "proj"
    (proj / ".windsurf").mkdir(parents=True)
    ch = make_channel(tmp_path)
    ad = WindsurfAdapter(home=tmp_path, cwd=proj)
    assert ad.detect() is True
    result = ad.install_skill(ch)
    assert result.path == proj / ".windsurf" / "rules" / "fake.md"
    text = result.path.read_text(encoding="utf-8")
    assert text.startswith("# Fake skill")  # frontmatter stripped, plain markdown
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.agents.windsurf'`

- [ ] **Step 3: Implement `src/agent_equip/agents/windsurf.py`**

```python
from __future__ import annotations

from pathlib import Path

from ..channels.base import Channel
from .base import AgentAdapter, strip_frontmatter


class WindsurfAdapter(AgentAdapter):
    """Installs rules into the current project's .windsurf/rules directory."""

    name = "windsurf"
    scope = "project"

    def detect(self) -> bool:
        return (self.cwd / ".windsurf").is_dir()

    def skill_target(self, channel: Channel) -> Path:
        return self.cwd / ".windsurf" / "rules" / f"{channel.name}.md"

    def render(self, channel: Channel) -> str:
        return strip_frontmatter(super().render(channel))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/agents/windsurf.py tests/test_agents.py
git commit -m "feat: add Windsurf adapter (project scope)"
```

---

### Task 9: Generic adapter (AGENTS.md marked block, opt-in)

**Files:**
- Create: `src/agent_equip/agents/generic.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_agents.py`**

```python
from agent_equip.agents.generic import GenericAdapter


def _generic(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    return GenericAdapter(home=tmp_path, cwd=proj), proj


def test_generic_is_opt_in_but_detects_true():
    assert GenericAdapter.auto is False
    assert GenericAdapter(home=Path("/x"), cwd=Path("/y")).detect() is True


def test_generic_creates_agents_md_with_marked_block(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    result = ad.install_skill(ch)
    assert result.action == "installed"
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- agent-equip:fake:start -->")
    assert "# Fake skill" in text
    assert text.rstrip().endswith("<!-- agent-equip:fake:end -->")


def test_generic_appends_to_existing_agents_md(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    (proj / "AGENTS.md").write_text("# My project notes\n", encoding="utf-8")
    result = ad.install_skill(ch)
    assert result.action == "installed"
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith("# My project notes")
    assert "<!-- agent-equip:fake:start -->" in text


def test_generic_replaces_existing_block_idempotently(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    ad.install_skill(ch)
    assert ad.install_skill(ch).action == "skipped"
    ch.skill_source().write_text("---\nname: fake\n---\n\n# Updated body\n", encoding="utf-8")
    assert ad.install_skill(ch).action == "updated"
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Updated body" in text
    assert text.count("<!-- agent-equip:fake:start -->") == 1


def test_generic_uninstall_removes_only_the_block(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    (proj / "AGENTS.md").write_text("# Keep me\n", encoding="utf-8")
    ad.install_skill(ch)
    ad.uninstall_skill(ch)
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep me" in text
    assert "agent-equip:fake" not in text


def test_generic_uninstall_deletes_file_if_block_was_everything(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    ad.install_skill(ch)
    ad.uninstall_skill(ch)
    assert not (proj / "AGENTS.md").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.agents.generic'`

- [ ] **Step 3: Implement `src/agent_equip/agents/generic.py`**

```python
from __future__ import annotations

from pathlib import Path

from ..channels.base import Channel
from .base import AgentAdapter, InstallResult, strip_frontmatter


def _start(channel_name: str) -> str:
    return f"<!-- agent-equip:{channel_name}:start -->"


def _end(channel_name: str) -> str:
    return f"<!-- agent-equip:{channel_name}:end -->"


class GenericAdapter(AgentAdapter):
    """Maintains a marked block inside the project's AGENTS.md. Opt-in only."""

    name = "generic"
    scope = "project"
    auto = False  # never auto-selected; requires --agent generic

    def detect(self) -> bool:
        return True  # can always write AGENTS.md when explicitly requested

    def skill_target(self, channel: Channel) -> Path:
        return self.cwd / "AGENTS.md"

    def _block(self, channel: Channel) -> str:
        body = strip_frontmatter(
            channel.skill_source().read_text(encoding="utf-8")
        ).rstrip()
        return f"{_start(channel.name)}\n{body}\n{_end(channel.name)}"

    def install_skill(self, channel: Channel) -> InstallResult:
        target = self.skill_target(channel)
        block = self._block(channel)
        start, end = _start(channel.name), _end(channel.name)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(block + "\n", encoding="utf-8")
            return InstallResult(self.name, target, "installed")
        text = target.read_text(encoding="utf-8")
        if start in text and end in text:
            pre, rest = text.split(start, 1)
            _, post = rest.split(end, 1)
            new = f"{pre}{block}{post}"
            if new == text:
                return InstallResult(self.name, target, "skipped")
            target.write_text(new, encoding="utf-8")
            return InstallResult(self.name, target, "updated")
        target.write_text(text.rstrip() + f"\n\n{block}\n", encoding="utf-8")
        return InstallResult(self.name, target, "installed")

    def uninstall_skill(self, channel: Channel) -> None:
        self.remove_block(self.skill_target(channel), channel.name)

    @staticmethod
    def remove_block(path: Path, channel_name: str) -> None:
        if not path.exists():
            return
        start, end = _start(channel_name), _end(channel_name)
        text = path.read_text(encoding="utf-8")
        if start not in text or end not in text:
            return
        pre, rest = text.split(start, 1)
        _, post = rest.split(end, 1)
        cleaned = (pre.rstrip() + "\n" + post.lstrip("\n")).strip()
        if cleaned:
            path.write_text(cleaned + "\n", encoding="utf-8")
        else:
            path.unlink()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_agents.py -v`
Expected: 20 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/agents/generic.py tests/test_agents.py
git commit -m "feat: add opt-in generic adapter using marked AGENTS.md block"
```

---

### Task 10: Manifest

**Files:**
- Create: `src/agent_equip/manifest.py`
- Test: `tests/test_manifest.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_manifest.py`:
```python
from agent_equip import manifest
from agent_equip.manifest import ManifestEntry


def test_load_returns_empty_when_no_manifest(tmp_path):
    assert manifest.load(root=tmp_path) == []


def test_record_and_load_roundtrip(tmp_path):
    entry = ManifestEntry(agent="claude-code", channel="github", path="/x/SKILL.md")
    manifest.record(entry, root=tmp_path)
    assert manifest.load(root=tmp_path) == [entry]
    assert (tmp_path / ".agent-equip" / "manifest.json").is_file()


def test_record_deduplicates(tmp_path):
    entry = ManifestEntry(agent="cursor", channel="github", path="/y/github.mdc")
    manifest.record(entry, root=tmp_path)
    manifest.record(entry, root=tmp_path)
    assert manifest.load(root=tmp_path) == [entry]


def test_clear_removes_manifest_and_empty_dir(tmp_path):
    manifest.record(
        ManifestEntry(agent="a", channel="c", path="/p"), root=tmp_path
    )
    manifest.clear(root=tmp_path)
    assert not (tmp_path / ".agent-equip").exists()
    assert manifest.load(root=tmp_path) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_manifest.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError` for `agent_equip.manifest`

- [ ] **Step 3: Implement `src/agent_equip/manifest.py`**

```python
"""Tracks every file agent-equip writes, so uninstall is surgical."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ManifestEntry:
    agent: str
    channel: str
    path: str


def manifest_path(root: Path | None = None) -> Path:
    base = root or Path.home()
    return base / ".agent-equip" / "manifest.json"


def load(root: Path | None = None) -> list[ManifestEntry]:
    p = manifest_path(root)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [ManifestEntry(**e) for e in data.get("installs", [])]


def record(entry: ManifestEntry, root: Path | None = None) -> None:
    entries = load(root)
    if entry not in entries:
        entries.append(entry)
    p = manifest_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"installs": [asdict(e) for e in entries]}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear(root: Path | None = None) -> None:
    p = manifest_path(root)
    if p.exists():
        p.unlink()
    if p.parent.exists() and not any(p.parent.iterdir()):
        p.parent.rmdir()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_manifest.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/manifest.py tests/test_manifest.py
git commit -m "feat: add install manifest for surgical uninstall"
```

---

### Task 11: Registry

**Files:**
- Create: `src/agent_equip/registry.py`
- Test: `tests/test_registry.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_registry.py`:
```python
import pytest

from agent_equip import registry
from agent_equip.channels.github import GitHubChannel


def test_channels_contains_github():
    assert isinstance(registry.CHANNELS["github"], GitHubChannel)


def test_get_channel_known():
    assert registry.get_channel("github").name == "github"


def test_get_channel_unknown_raises_with_available_list():
    with pytest.raises(KeyError, match="github"):
        registry.get_channel("nope")


def test_make_adapters_returns_all_four(tmp_path):
    adapters = registry.make_adapters(home=tmp_path, cwd=tmp_path)
    names = [a.name for a in adapters]
    assert names == ["claude-code", "cursor", "windsurf", "generic"]
    assert all(a.home == tmp_path for a in adapters)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent_equip.registry'`

- [ ] **Step 3: Implement `src/agent_equip/registry.py`**

```python
"""Explicit wiring of channels and agent adapters. No discovery magic."""

from __future__ import annotations

from pathlib import Path

from .agents.base import AgentAdapter
from .agents.claude_code import ClaudeCodeAdapter
from .agents.cursor import CursorAdapter
from .agents.generic import GenericAdapter
from .agents.windsurf import WindsurfAdapter
from .channels.base import Channel
from .channels.github import GitHubChannel

CHANNELS: dict[str, Channel] = {c.name: c for c in [GitHubChannel()]}

ADAPTER_TYPES: list[type[AgentAdapter]] = [
    ClaudeCodeAdapter,
    CursorAdapter,
    WindsurfAdapter,
    GenericAdapter,
]


def get_channel(name: str) -> Channel:
    try:
        return CHANNELS[name]
    except KeyError:
        available = ", ".join(sorted(CHANNELS))
        raise KeyError(f"unknown channel '{name}'; available: {available}") from None


def make_adapters(
    home: Path | None = None, cwd: Path | None = None
) -> list[AgentAdapter]:
    return [cls(home=home, cwd=cwd) for cls in ADAPTER_TYPES]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_registry.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/registry.py tests/test_registry.py
git commit -m "feat: add explicit channel/adapter registry"
```

---

### Task 12: CLI — `list` and `doctor`

**Files:**
- Modify: `src/agent_equip/cli.py` (replace entire file)
- Test: `tests/test_cli.py`

**Testing approach for all CLI tasks:** Typer's `CliRunner` + monkeypatching `Path.home`/`Path.cwd` so adapters and the manifest operate on `tmp_path`, and monkeypatching `registry.CHANNELS` with a fake channel so no real `gh` calls happen.

- [ ] **Step 1: Write the failing tests**

`tests/test_cli.py`:
```python
from pathlib import Path

from typer.testing import CliRunner

from agent_equip import registry
from agent_equip.channels.base import Channel, CheckResult
from agent_equip.cli import app

runner = CliRunner()


class StubChannel(Channel):
    name = "github"
    description = "stub github channel"

    def __init__(self, status="ok", skill_path: Path | None = None):
        self._status = status
        self._skill_path = skill_path

    def check(self) -> CheckResult:
        hints = {"warn": "run `gh auth login`", "fail": "brew install gh"}
        return CheckResult(self._status, f"status is {self._status}", hints.get(self._status))

    def skill_source(self) -> Path:
        return self._skill_path


def use_stub(monkeypatch, tmp_path, status="ok"):
    """Point the CLI at a stub channel and an isolated home/cwd under tmp_path."""
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: github\n---\n\n# GitHub skill\n", encoding="utf-8")
    stub = StubChannel(status=status, skill_path=skill)
    monkeypatch.setattr(registry, "CHANNELS", {"github": stub})
    home = tmp_path / "home"
    cwd = tmp_path / "proj"
    home.mkdir(exist_ok=True)
    cwd.mkdir(exist_ok=True)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(Path, "cwd", classmethod(lambda cls: cwd))
    return home, cwd


def test_list_shows_channels_and_agents(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    for expected in ["github", "claude-code", "cursor", "windsurf", "generic", "opt-in"]:
        assert expected in result.output


def test_doctor_ok_exit_zero(monkeypatch, tmp_path):
    home, _ = use_stub(monkeypatch, tmp_path, status="ok")
    (home / ".claude").mkdir()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "[ok] github" in result.output
    assert "claude-code" in result.output


def test_doctor_warn_exit_one(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path, status="warn")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "[!] github" in result.output
    assert "gh auth login" in result.output


def test_doctor_fail_exit_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path, status="fail")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 2
    assert "[x] github" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: FAIL — `list`/`doctor` commands don't exist yet (Typer exits with usage error).

- [ ] **Step 3: Replace `src/agent_equip/cli.py` entirely**

```python
from __future__ import annotations

import typer

from . import manifest, registry

app = typer.Typer(no_args_is_help=True, help="Equip AI coding agents with platform skills.")

_ICONS = {"ok": "[ok]", "warn": "[!]", "fail": "[x]"}
_SEVERITY = {"ok": 0, "warn": 1, "fail": 2}


@app.command()
def version() -> None:
    """Print the agent-equip version."""
    from . import __version__

    typer.echo(__version__)


@app.command("list")
def list_() -> None:
    """Show available channels and supported agents."""
    typer.echo("Channels:")
    for ch in registry.CHANNELS.values():
        typer.echo(f"  {ch.name} - {ch.description}")
    typer.echo("Agents:")
    for ad in registry.make_adapters():
        note = "" if ad.auto else " (opt-in via --agent)"
        typer.echo(f"  {ad.name} [{ad.scope}]{note}")


@app.command()
def doctor() -> None:
    """Read-only health report. Exit code: 0 ok, 1 warn, 2 fail."""
    worst = 0
    for ch in registry.CHANNELS.values():
        res = ch.check()
        line = f"{_ICONS[res.status]} {ch.name}: {res.message}"
        if res.fix_hint:
            line += f"  -> {res.fix_hint}"
        typer.echo(line)
        worst = max(worst, _SEVERITY[res.status])
    detected = [a.name for a in registry.make_adapters() if a.auto and a.detect()]
    typer.echo("Detected agents: " + (", ".join(detected) if detected else "none"))
    entries = manifest.load()
    if entries:
        typer.echo("Installed skills:")
        for e in entries:
            typer.echo(f"  {e.channel} -> {e.agent} ({e.path})")
    raise typer.Exit(code=worst)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: 5 passed

- [ ] **Step 5: Run the whole suite**

Run: `.venv/bin/python -m pytest`
Expected: all tests pass (33 so far).

- [ ] **Step 6: Commit**

```bash
git add src/agent_equip/cli.py tests/test_cli.py
git commit -m "feat: add list and doctor CLI commands"
```

---

### Task 13: CLI — `install`

**Files:**
- Modify: `src/agent_equip/cli.py` (append command)
- Modify: `tests/test_cli.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_cli.py`**

```python
def test_install_into_detected_agents(monkeypatch, tmp_path):
    home, cwd = use_stub(monkeypatch, tmp_path, status="ok")
    (home / ".claude").mkdir()
    (cwd / ".cursor").mkdir()
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 0
    assert (home / ".claude" / "skills" / "github" / "SKILL.md").is_file()
    assert (cwd / ".cursor" / "rules" / "github.mdc").is_file()
    # windsurf not detected -> not installed
    assert not (cwd / ".windsurf").exists()
    # manifest recorded under home
    assert (home / ".agent-equip" / "manifest.json").is_file()
    assert "installed" in result.output


def test_install_unknown_channel_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "nope"])
    assert result.exit_code == 2
    assert "unknown channel" in result.output


def test_install_fail_status_prints_hint_and_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path, status="fail")
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 2
    assert "brew install gh" in result.output


def test_install_warn_status_still_installs(monkeypatch, tmp_path):
    home, _ = use_stub(monkeypatch, tmp_path, status="warn")
    (home / ".claude").mkdir()
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 0
    assert (home / ".claude" / "skills" / "github" / "SKILL.md").is_file()
    assert "gh auth login" in result.output


def test_install_no_agents_detected_exits_one(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 1
    assert "No agents detected" in result.output


def test_install_specific_agent_generic(monkeypatch, tmp_path):
    _, cwd = use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "github", "--agent", "generic"])
    assert result.exit_code == 0
    assert (cwd / "AGENTS.md").is_file()


def test_install_specific_agent_unknown_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "github", "--agent", "nope"])
    assert result.exit_code == 2
    assert "unknown agent" in result.output


def test_install_specific_agent_undetected_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)  # no .claude dir created
    result = runner.invoke(app, ["install", "github", "--agent", "claude-code"])
    assert result.exit_code == 2
    assert "not detected" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: the 8 new tests FAIL (no `install` command); first 5 still pass.

- [ ] **Step 3: Append the `install` command to `src/agent_equip/cli.py`**

Add these imports at the top of the file:
```python
import subprocess
from typing import Annotated, Optional

from .manifest import ManifestEntry
```

Append this command at the bottom:
```python
@app.command()
def install(
    channel_name: Annotated[str, typer.Argument(metavar="CHANNEL", help="Channel to set up, e.g. 'github'")],
    agent: Annotated[
        Optional[str], typer.Option("--agent", help="Install for one specific agent only")
    ] = None,
    auto: Annotated[
        bool, typer.Option("--auto", help="Run system install commands instead of printing them")
    ] = False,
) -> None:
    """Check the channel's tooling and install its skill into detected agents."""
    try:
        channel = registry.get_channel(channel_name)
    except KeyError as exc:
        typer.echo(f"error: {exc.args[0]}")
        raise typer.Exit(code=2)

    res = channel.check()
    typer.echo(f"{_ICONS[res.status]} {channel.name}: {res.message}")
    if res.fix_hint:
        typer.echo(f"  -> {res.fix_hint}")

    if res.status == "fail":
        if auto and res.fix_hint:
            typer.echo(f"--auto: running `{res.fix_hint}`")
            subprocess.run(res.fix_hint, shell=True, check=False)
            res = channel.check()
            typer.echo(f"{_ICONS[res.status]} {channel.name}: {res.message}")
        if res.status == "fail":
            typer.echo("Channel tooling missing; fix the issue above and re-run.")
            raise typer.Exit(code=2)

    adapters = registry.make_adapters()
    if agent is not None:
        chosen = [a for a in adapters if a.name == agent]
        if not chosen:
            names = ", ".join(a.name for a in adapters)
            typer.echo(f"error: unknown agent '{agent}'; available: {names}")
            raise typer.Exit(code=2)
        if not chosen[0].detect():
            typer.echo(f"error: agent '{agent}' not detected on this machine/project")
            raise typer.Exit(code=2)
    else:
        chosen = [a for a in adapters if a.auto and a.detect()]

    if not chosen:
        typer.echo("No agents detected. Use --agent to target one (see `agent-equip list`).")
        raise typer.Exit(code=1)

    for ad in chosen:
        result = ad.install_skill(channel)
        manifest.record(ManifestEntry(ad.name, channel.name, str(result.path)))
        typer.echo(f"{result.action}: {channel.name} skill -> {ad.name} ({result.path})")

    typer.echo('\nDone. Try asking your agent: "list the open issues in <owner>/<repo>"')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/cli.py tests/test_cli.py
git commit -m "feat: add install command with agent detection and manifest recording"
```

---

### Task 14: CLI — `uninstall`

**Files:**
- Modify: `src/agent_equip/cli.py` (append command)
- Modify: `tests/test_cli.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_cli.py`**

```python
def test_uninstall_removes_files_and_manifest(monkeypatch, tmp_path):
    home, cwd = use_stub(monkeypatch, tmp_path)
    (home / ".claude").mkdir()
    runner.invoke(app, ["install", "github"])
    skill = home / ".claude" / "skills" / "github" / "SKILL.md"
    assert skill.is_file()
    result = runner.invoke(app, ["uninstall"])
    assert result.exit_code == 0
    assert not skill.exists()
    assert not (home / ".agent-equip").exists()


def test_uninstall_removes_generic_block_but_keeps_user_content(monkeypatch, tmp_path):
    _, cwd = use_stub(monkeypatch, tmp_path)
    (cwd / "AGENTS.md").write_text("# Keep me\n", encoding="utf-8")
    runner.invoke(app, ["install", "github", "--agent", "generic"])
    result = runner.invoke(app, ["uninstall"])
    assert result.exit_code == 0
    text = (cwd / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep me" in text
    assert "agent-equip" not in text


def test_uninstall_with_nothing_installed(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["uninstall"])
    assert result.exit_code == 0
    assert "Nothing to uninstall" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: 3 new tests FAIL (no `uninstall` command).

- [ ] **Step 3: Append the `uninstall` command to `src/agent_equip/cli.py`**

Add this import near the other imports:
```python
from pathlib import Path

from .agents.generic import GenericAdapter
```

Append this command:
```python
@app.command()
def uninstall() -> None:
    """Remove every skill agent-equip installed, then clear the manifest."""
    entries = manifest.load()
    if not entries:
        typer.echo("Nothing to uninstall (no manifest found).")
        raise typer.Exit(code=0)
    for e in entries:
        p = Path(e.path)
        if e.agent == "generic":
            GenericAdapter.remove_block(p, e.channel)
            typer.echo(f"removed: {e.channel} block from {p}")
        elif p.exists():
            p.unlink()
            typer.echo(f"removed: {p}")
    manifest.clear()
    typer.echo("Manifest cleared. agent-equip leftovers: none.")
```

- [ ] **Step 4: Run the whole suite**

Run: `.venv/bin/python -m pytest -v`
Expected: all tests pass (44 total).

- [ ] **Step 5: Commit**

```bash
git add src/agent_equip/cli.py tests/test_cli.py
git commit -m "feat: add uninstall command driven by the manifest"
```

---

### Task 15: Lint clean + CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Run ruff and fix anything it reports**

Run: `.venv/bin/ruff check .`
Expected: `All checks passed!` — if not, apply `.venv/bin/ruff check . --fix`, review the diff, re-run until clean. Do not change behavior; only mechanical lint fixes (unused imports, ordering).

- [ ] **Step 2: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.10", "3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - name: Install
        run: pip install -e ".[dev]"
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest -v
```

- [ ] **Step 3: Run the full suite once more**

Run: `.venv/bin/python -m pytest && .venv/bin/ruff check .`
Expected: all tests pass, lint clean.

- [ ] **Step 4: Commit**

```bash
git add .github/ src/ tests/
git commit -m "ci: add lint+test matrix across 3 OSes and Python 3.10-3.12"
```

---

### Task 16: README and CHANGELOG

**Files:**
- Modify: `README.md` (replace stub entirely)
- Create: `CHANGELOG.md`

- [ ] **Step 1: Replace `README.md` with the full version**

````markdown
# agent-equip

**Set up GitHub superpowers for any AI coding agent in one command.**

Your AI coding agent (Claude Code, Cursor, Windsurf, ...) can write code — but does it know how to *work GitHub*? `agent-equip` makes sure it does:

1. Checks that the official [`gh` CLI](https://cli.github.com) is installed and authenticated — and tells you exactly how to fix it if not.
2. Installs a battle-ready GitHub skill into every agent it detects on your machine, teaching the agent which `gh` command answers which request.
3. Gets out of the way. After setup your agent talks to GitHub directly through `gh`. No wrapper, no middleman, no new API to learn.

```bash
pipx install git+https://github.com/shenmali/agent-equip
agent-equip install github
```

Then ask your agent things like:

> *"What are the open issues in vercel/next.js?"*
> *"Summarize the diff of PR #42 in our repo."*
> *"Find popular Rust vector databases on GitHub."*

## Supported agents

| Agent | Scope | Skill location |
|---|---|---|
| Claude Code | global | `~/.claude/skills/github/SKILL.md` |
| Cursor | project | `.cursor/rules/github.mdc` |
| Windsurf | project | `.windsurf/rules/github.md` |
| Generic (any agent reading AGENTS.md) | project, opt-in | marked block in `AGENTS.md` |

Project-scoped agents are detected per project: run `agent-equip install github` inside the project. The generic adapter only runs when you explicitly ask: `--agent generic`.

## Commands

| Command | What it does |
|---|---|
| `agent-equip install github` | Check `gh`, detect agents, install the skill |
| `agent-equip install github --agent cursor` | Target a single agent |
| `agent-equip install github --auto` | Also *run* system install commands instead of printing them |
| `agent-equip doctor` | Read-only health report (exit code 0/1/2 = ok/warn/fail) |
| `agent-equip list` | Show channels and agents |
| `agent-equip uninstall` | Remove everything agent-equip installed — exactly that, nothing else |

## Security posture

- **Zero credentials stored.** Authentication is handled entirely by `gh`'s own secure store. agent-equip never sees, stores, or transmits a token.
- **Safe by default.** agent-equip never runs system-modifying commands unless you pass `--auto`. Without it, commands are printed for you to review and run.
- **Surgical uninstall.** Every file written is recorded in `~/.agent-equip/manifest.json`; `uninstall` removes exactly those and nothing else.
- `doctor` is strictly read-only.

## Architecture

Two pluggable axes — every feature is one file:

```
src/agent_equip/
├── channels/        # platforms (v1: github)
│   └── github.py    # health check for the gh CLI
├── agents/          # adapters (claude-code, cursor, windsurf, generic)
└── skills/
    └── github/SKILL.md   # the content agents receive
```

Adding a channel = one file in `channels/` + a `SKILL.md` + one registry line.
Adding an agent = one file in `agents/` + one registry line.

## Contributing

PRs welcome — especially new agent adapters and channels. Each one is a single file with a small interface (see `channels/base.py` and `agents/base.py`); copy an existing one, adjust, add tests.

## License

MIT.

*Architecture philosophy inspired by [Agent-Reach](https://github.com/Panniantong/Agent-Reach); all code written from scratch.*
````

- [ ] **Step 2: Create `CHANGELOG.md`**

```markdown
# Changelog

## 0.1.0 — 2026-06-10

Initial release.

- `install github`: checks the gh CLI, detects agents, installs the GitHub skill.
- Adapters: Claude Code (global), Cursor (project), Windsurf (project), generic AGENTS.md block (opt-in).
- `doctor` read-only health report with meaningful exit codes.
- `uninstall` driven by an install manifest — removes exactly what was installed.
- Safe by default: system commands are printed, not run, unless `--auto`.
```

- [ ] **Step 3: Verify README renders (quick sanity)**

Run: `head -5 README.md`
Expected: title + tagline visible, no stub text remaining.

- [ ] **Step 4: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: add full README and changelog for v0.1.0"
```

---

### Task 17: End-to-end verification on the real machine

**Files:** none (verification only)

- [ ] **Step 1: Full suite + lint**

Run: `.venv/bin/python -m pytest -v && .venv/bin/ruff check .`
Expected: all tests pass, lint clean.

- [ ] **Step 2: Real `doctor` run**

Run: `.venv/bin/agent-equip doctor`
Expected (this machine has gh installed + authed and `~/.claude` exists):
```
[ok] github: gh CLI installed and authenticated
Detected agents: claude-code
```
Exit code 0. If gh is unauthenticated, `[!]` + exit 1 is also acceptable — record what you saw.

- [ ] **Step 3: Real install + uninstall roundtrip (safe: only touches skill dirs + manifest)**

Run:
```bash
.venv/bin/agent-equip install github
cat ~/.claude/skills/github/SKILL.md | head -5
cat ~/.agent-equip/manifest.json
.venv/bin/agent-equip uninstall
ls ~/.claude/skills/github 2>&1 || echo "cleaned"
```
Expected: skill installed with frontmatter, manifest lists it, uninstall removes both, final command prints an error or `cleaned`.

- [ ] **Step 4: Commit (only if fixes were needed)**

If steps 1–3 surfaced bugs, fix them test-first, then:
```bash
git add -A
git commit -m "fix: <describe what e2e verification caught>"
```

---

### Task 18: Publish to GitHub

**Files:** none (publishing only)

> **STOP — user confirmation required before this task.** Creating a public repo is outward-facing. Confirm with the user immediately before running these commands.

- [ ] **Step 1: Confirm with the user** that the repo should be created as `shenmali/agent-equip` (public).

- [ ] **Step 2: Create and push**

```bash
cd /Users/ali/Documents/GitHub/agent-equip
gh repo create shenmali/agent-equip --public --source=. --push \
  --description "Set up GitHub superpowers for any AI coding agent in one command."
```
Expected: repo created, `main` pushed.

- [ ] **Step 3: Add topics and verify CI**

```bash
gh repo edit shenmali/agent-equip --add-topic ai-agent --add-topic claude-code --add-topic cursor --add-topic github-cli --add-topic agent-skills --add-topic cli
gh run list --repo shenmali/agent-equip --limit 1
```
Expected: topics set; first CI run visible (wait for it, expect green across the matrix; if a leg fails, fix test-first and push).

- [ ] **Step 4: Report the repo URL to the user.**

---

## Self-review notes (completed)

- **Spec coverage:** scaffolding+packaging (T1), Channel/CheckResult (T2), SKILL.md content (T3), GitHub channel incl. timeout handling (T4), adapter base + idempotent install (T5), all four adapters with scope semantics (T6–9), manifest (T10), registry (T11), CLI list/doctor with exit codes (T12), install flow incl. `--auto` and `--agent` errors (T13), surgical uninstall incl. generic block (T14), CI matrix + ruff (T15), README with security posture + attribution + contributing (T16), e2e verification (T17), publishing (T18). PyPI release is explicitly post-v1 in the spec — not in this plan.
- **Type consistency check:** `CheckResult(status, message, fix_hint)`, `InstallResult(agent, path, action)`, adapter ctor `(home, cwd)`, `manifest.ManifestEntry(agent, channel, path)` — used identically across all tasks.
- **Placeholder scan:** clean — every step carries its full code/command/expected output.
