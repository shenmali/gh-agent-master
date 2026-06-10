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
