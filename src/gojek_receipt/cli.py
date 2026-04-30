from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from gojek_receipt import __version__
from gojek_receipt.core.extractor import extract
from gojek_receipt.core.renderer import render

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer(
    name="gojek-receipt",
    help="Convert a Gojek transaction-history PDF to XLSX.",
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    input_path: Optional[Path] = typer.Argument(
        None,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Gojek receipt PDF file.",
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        dir_okay=False,
        help="Output .xlsx path. Defaults to same directory as input.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Convert a Gojek receipt PDF to an Excel workbook."""
    if ctx.invoked_subcommand is not None:
        return

    if input_path is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)

    if input_path.suffix.lower() != ".pdf":
        console.print(
            f"[bold red]Error:[/bold red] Expected a .pdf file, got [yellow]{input_path.suffix}[/yellow]"
        )
        raise typer.Exit(1)

    if output_path is None:
        output_path = input_path.with_suffix(".xlsx")

    console.print(f"[dim]Reading:[/dim] {input_path}")

    try:
        receipt = extract(input_path)
    except Exception as exc:
        console.print(f"[bold red]Extraction error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print(
        f"[dim]Parsed [/dim][bold]{len(receipt.transactions)}[/bold][dim] transactions[/dim]"
    )

    try:
        render(receipt, output_path)
    except Exception as exc:
        console.print(f"[bold red]Render error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Done:[/green] {output_path}")


if __name__ == "__main__":
    app()
