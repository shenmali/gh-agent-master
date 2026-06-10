"""Tracks every file agent-equip writes, so uninstall is surgical."""

from __future__ import annotations

import json
import os
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
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"manifest at {p} is corrupt ({exc}); delete it to reset.") from None
    return [ManifestEntry(**e) for e in data.get("installs", [])]


def record(entry: ManifestEntry, root: Path | None = None) -> None:
    entries = load(root)
    if entry not in entries:
        entries.append(entry)
    p = manifest_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"installs": [asdict(e) for e in entries]}
    tmp = p.parent / f".manifest.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(p)


def clear(root: Path | None = None) -> None:
    p = manifest_path(root)
    if p.exists():
        p.unlink()
    if p.parent.exists() and not any(p.parent.iterdir()):
        p.parent.rmdir()
