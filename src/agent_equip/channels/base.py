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

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for attr in ("name", "description"):
            if not isinstance(getattr(cls, attr, None), str):
                raise TypeError(
                    f"{cls.__name__} must define a string class attribute {attr!r}"
                )

    @abstractmethod
    def check(self) -> CheckResult:
        """Report whether this channel's upstream tooling is ready."""

    @abstractmethod
    def skill_source(self) -> Path:
        """Path to the bundled SKILL.md delivered to agents."""
