import typer

app = typer.Typer(no_args_is_help=True, help="Equip AI coding agents with platform skills.")


@app.command()
def version() -> None:
    """Print the agent-equip version."""
    from . import __version__

    typer.echo(__version__)
