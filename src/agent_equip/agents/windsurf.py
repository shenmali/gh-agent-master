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
