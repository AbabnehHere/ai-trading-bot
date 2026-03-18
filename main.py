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
            click.echo("WARNING: This will place REAL orders with REAL money!")
            from src.core.bot import TradingBot

            bot = TradingBot(config_path=config, paper=False)
            bot.run()

        case "paper-trade":
            click.echo("Starting paper trading...")
            from src.core.bot import TradingBot

            bot = TradingBot(config_path=config, paper=True)
            bot.run()

        case "backtest":
            click.echo("Starting backtester...")
            from src.backtest.backtester import Backtester
            from src.strategy.convergence import ConvergenceStrategy
            from src.strategy.edge_finder import EdgeFinder
            from src.strategy.news_reactor import NewsReactor

            strategies = [EdgeFinder(), NewsReactor(), ConvergenceStrategy()]
            bt = Backtester(strategies)
            results = bt.run()

            click.echo("\n--- Backtest Results ---")
            click.echo(f"Total trades: {results.get('total_trades', 0)}")
            click.echo(f"Total P&L: ${results.get('total_pnl', 0):.2f}")
            click.echo(f"Max drawdown: {results.get('max_drawdown', 0):.1%}")
            click.echo(f"Sharpe ratio: {results.get('sharpe_ratio', 0):.2f}")

        case "collect-data":
            click.echo("Collecting historical data...")
            from src.backtest.data_collector import DataCollector

            collector = DataCollector()
            result = collector.collect_all_active_markets()
            click.echo(f"Collected: {result.get('collected', 0)} markets")
            click.echo(f"Errors: {result.get('errors', 0)}")

        case "dashboard":
            click.echo("Loading dashboard...")
            from src.learning.performance import PerformanceTracker

            tracker = PerformanceTracker()
            metrics = tracker.calculate_metrics()

            click.echo("\n--- Performance Dashboard ---")
            click.echo(f"Total trades: {metrics['total_trades']}")
            click.echo(f"Win rate: {metrics['win_rate']:.0%}")
            click.echo(f"Total P&L: ${metrics['total_pnl']:.2f}")
            click.echo(f"Profit factor: {metrics['profit_factor']:.2f}")
            click.echo(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
            click.echo(f"Max drawdown: {metrics['max_drawdown']:.1%}")
            click.echo(f"Best trade: ${metrics['best_trade']:.2f}")
            click.echo(f"Worst trade: ${metrics['worst_trade']:.2f}")

        case "review":
            click.echo("Running strategy review...")
            from src.learning.performance import PerformanceTracker
            from src.learning.strategy_tuner import StrategyTuner

            perf = PerformanceTracker()
            tuner = StrategyTuner(perf)
            from src.utils.config_loader import ConfigLoader

            cfg = ConfigLoader(config)
            suggestions = tuner.suggest_adjustments(cfg.get_all())

            if suggestions:
                click.echo("\n--- Strategy Adjustments Suggested ---")
                for s in suggestions:
                    click.echo(f"  {s['parameter']}: {s['current']} → {s['suggested']}")
                    click.echo(f"    Reason: {s['reason']}")
            else:
                click.echo("No adjustments needed at this time.")

        case "reconcile":
            click.echo("Reconciling positions...")
            click.echo("Position reconciliation requires live API access.")
            click.echo("This will compare local state with exchange state.")


if __name__ == "__main__":
    main()
