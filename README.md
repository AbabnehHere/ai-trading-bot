# Polymarket Trading Bot

[![CI](https://github.com/AbabnehHere/ai-trading-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/AbabnehHere/ai-trading-bot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A conservative, self-improving trading bot for [Polymarket](https://polymarket.com) prediction markets. The bot identifies mispriced markets, applies strict risk management, and learns from its own trading history to improve over time.

## Overview

- **Edge Detection**: Compares Polymarket prices against independently compiled probability estimates to find mispriced markets
- **News-Reactive Trading**: Monitors news feeds to react to events that shift market probabilities
- **Convergence Trading**: Trades near-resolution markets where outcomes are near-certain but prices haven't converged
- **Conservative Risk Management**: Hard limits on position size, daily losses, drawdown circuit breakers, and portfolio concentration
- **Self-Improvement**: Logs every trade, extracts lessons, and tunes strategy parameters based on performance

## Prerequisites

- Python 3.11+
- Polymarket account with API credentials
- Polygon wallet with USDC for trading
- (Optional) Telegram bot for notifications

## Installation

```bash
# Clone the repository
git clone https://github.com/AbabnehHere/ai-trading-bot.git
cd ai-trading-bot

# Install development dependencies
make install-dev

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys and wallet credentials
```

## Configuration

1. **Environment variables**: Copy `.env.example` to `.env` and fill in your credentials
2. **Strategy settings**: Edit `config/settings.yaml` for trading parameters
3. **Risk limits**: Edit `config/risk_limits.yaml` for risk management thresholds
4. **Market watchlist**: Edit `config/markets_watchlist.yaml` for markets to monitor

## Usage

```bash
# Run backtesting against historical data
make run-backtest

# Run paper trading (simulated trades with live data)
make run-paper

# Run live trading (requires all testing gates passed)
make run-live

# View performance dashboard
make dashboard

# Run system health check
make health
```

## Development

```bash
# Run linter
make lint

# Auto-format code
make format

# Run type checker
make type-check

# Run all tests
make test

# Run unit tests only
make test-unit
```

## Project Structure

```
├── config/          # YAML configuration files
├── src/
│   ├── core/        # Bot orchestrator, order/position/risk management
│   ├── strategy/    # Trading strategies (edge finder, news reactor, convergence)
│   ├── data/        # Market data, news feeds, odds compilation, sentiment
│   ├── learning/    # Trade journal, performance tracking, strategy tuning
│   ├── utils/       # Logging, notifications, config loading, helpers
│   └── backtest/    # Backtesting engine, paper trader, data collection
├── tests/           # Unit and integration tests
├── scripts/         # Database setup, health checks, data export
├── docs/            # Documentation
└── main.py          # CLI entry point
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Disclaimer

**This bot trades with real money. Use at your own risk. Past performance does not guarantee future results. Only trade with funds you can afford to lose.**

This software is provided "as is" without warranty of any kind. The authors are not responsible for any financial losses incurred through the use of this bot.

## License

[MIT](LICENSE)
