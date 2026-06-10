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
        safe_desc = channel.description.replace("'", "''")
        return f"---\ndescription: '{safe_desc}'\nalwaysApply: false\n---\n\n{body}"
