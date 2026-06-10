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

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not isinstance(getattr(cls, "name", None), str):
            raise TypeError(f"{cls.__name__} must define a string class attribute 'name'")
        if getattr(cls, "scope", None) not in ("global", "project"):
            raise TypeError(f"{cls.__name__} must define scope as 'global' or 'project'")

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
