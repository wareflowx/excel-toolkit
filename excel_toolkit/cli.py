"""Main CLI application for Excel Toolkit."""

from importlib.metadata import version

import typer

from excel_toolkit.commands.info import info as info_command

try:
    __version__ = version("excel-toolkit")
except Exception:
    __version__ = "0.1.0-dev"

app = typer.Typer(
    help="Excel CLI Toolkit - Command-line toolkit for Excel data manipulation and analysis"
)


@app.command()
def version():
    """Show version information."""
    typer.echo(f"Excel CLI Toolkit v{__version__}")


@app.command()
def sysinfo():
    """Show system information."""
    typer.echo("Excel CLI Toolkit")
    typer.echo("Command-line toolkit for Excel data manipulation and analysis")
    typer.echo(f"Version: {__version__}")
    typer.echo(f"Python: 3.14")


# Register file info command from commands module
# Use the info function directly as a command
app.command()(info_command)


if __name__ == "__main__":
    app()
