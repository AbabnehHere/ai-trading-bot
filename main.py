"""Polymarket Trading Bot — Entry Point."""

import click

from src.utils.logger import setup_logging


@click.group(invoke_without_command=True)
@click.option(
    "--mode",
    type=click.Choice(
        [
            "live",
            "paper-trade",
            "backtest",
            "collect-data",
            "dashboard",
            "review",
            "reconcile",
        ]
    ),
    required=True,
    help="Operating mode",
)
@click.option("--config", default="config/settings.yaml", help="Path to config file")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def main(mode: str, config: str, verbose: bool) -> None:
    """Polymarket Conservative Trading Bot."""
    setup_logging(verbose=verbose)

    match mode:
        case "live":
            click.echo("Starting live trading...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-8 first.")

        case "paper-trade":
            click.echo("Starting paper trading...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-7 first.")

        case "backtest":
            click.echo("Starting backtester...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-6 first.")

        case "collect-data":
            click.echo("Collecting historical data...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-4 first.")

        case "dashboard":
            click.echo("Loading dashboard...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-7 first.")

        case "review":
            click.echo("Running strategy review...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-8 first.")

        case "reconcile":
            click.echo("Reconciling positions...")
            click.echo("[NOT YET IMPLEMENTED] — Complete Phases 2-8 first.")


if __name__ == "__main__":
    main()
