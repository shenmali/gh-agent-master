from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer

from . import manifest, registry
from .agents.generic import GenericAdapter
from .manifest import ManifestEntry

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
