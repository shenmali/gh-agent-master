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
