from __future__ import annotations

from pathlib import Path

from ..channels.base import Channel
from .base import AgentAdapter, InstallResult, strip_frontmatter


def _start(channel_name: str) -> str:
    return f"<!-- agent-equip:{channel_name}:start -->"


def _end(channel_name: str) -> str:
    return f"<!-- agent-equip:{channel_name}:end -->"


def _block_span(text: str, start: str, end: str) -> tuple[int, int] | None:
    """(start, stop) indices of a well-formed marked block, else None.

    Malformed states (missing or inverted markers) return None so callers
    fall back to appending or leaving the file untouched instead of crashing.
    """
    start_idx = text.find(start)
    end_idx = text.find(end)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return None
    return start_idx, end_idx + len(end)


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
        body = strip_frontmatter(self.render(channel)).rstrip()
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
        span = _block_span(text, start, end)
        if span is not None:
            start_idx, end_idx = span
            new = f"{text[:start_idx]}{block}{text[end_idx:]}"
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
        span = _block_span(text, start, end)
        if span is None:
            return
        start_idx, end_idx = span
        pre, post = text[:start_idx], text[end_idx:]
        cleaned = (pre.rstrip() + "\n" + post.lstrip("\n")).strip()
        if cleaned:
            path.write_text(cleaned + "\n", encoding="utf-8")
        else:
            path.unlink()
