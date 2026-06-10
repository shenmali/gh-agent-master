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
