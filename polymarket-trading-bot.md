# Polymarket Automated Trading Bot — Claude Code Master Prompt

> **Purpose**: You are an autonomous AI agent tasked with building, testing, and deploying a conservative, self-improving trading bot on Polymarket. This document is your complete specification. Follow every section in order. Do not skip phases. Do not deploy to live markets until all testing gates are passed.

---

## TABLE OF CONTENTS

0. [Phase 0 — Repository Preparation & Project Scaffolding](#phase-0--repository-preparation--project-scaffolding)
1. [Phase 1 — Deep Research & Knowledge Building](#phase-1--deep-research--knowledge-building)
2. [Phase 2 — Wallet Setup & Fund Transfer](#phase-2--wallet-setup--fund-transfer)
3. [Phase 3 — Architecture & Infrastructure](#phase-3--architecture--infrastructure)
4. [Phase 4 — Strategy Design](#phase-4--strategy-design)
5. [Phase 5 — Risk Management Framework](#phase-5--risk-management-framework)
6. [Phase 6 — Backtesting & Paper Trading](#phase-6--backtesting--paper-trading)
7. [Phase 7 — Self-Improvement Engine](#phase-7--self-improvement-engine)
8. [Phase 8 — Live Deployment](#phase-8--live-deployment)
9. [Phase 9 — Monitoring & Maintenance](#phase-9--monitoring--maintenance)
10. [Appendix — Key Principles & Rules](#appendix--key-principles--rules)

---

## PHASE 0 — Repository Preparation & Project Scaffolding

**This is the very first thing you do. A clean, professional, well-structured repo is the foundation of everything that follows. Do not write any strategy or bot logic until the repo is fully scaffolded, linted, and passing CI checks.**

### 0.1 — Initialize the Repository

```bash
mkdir polymarket-bot && cd polymarket-bot
git init
```

Create the full directory structure immediately. Every folder should exist from the start, even if files inside are empty stubs. Use placeholder `__init__.py` files in every Python package directory.

```
polymarket-bot/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Lint + test on every push/PR
│       └── security.yml           # Dependency vulnerability scanning
├── config/
│   ├── settings.yaml              # All tunable strategy parameters
│   ├── settings.dev.yaml          # Dev/paper-trading overrides
│   ├── settings.prod.yaml         # Production overrides
│   ├── markets_watchlist.yaml     # Markets to monitor
│   └── risk_limits.yaml           # Risk management parameters
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bot.py                 # Main bot orchestrator
│   │   ├── market_analyzer.py     # Market analysis & opportunity detection
│   │   ├── order_manager.py       # Order placement, tracking, cancellation
│   │   ├── position_manager.py    # Portfolio and position tracking
│   │   └── risk_manager.py        # Risk checks before every trade
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── base_strategy.py       # Abstract base class for strategies
│   │   ├── edge_finder.py         # Core: find mispriced markets
│   │   ├── news_reactor.py        # News-based trading signals
│   │   └── convergence.py         # Late-stage convergence trading
│   ├── data/
│   │   ├── __init__.py
│   │   ├── market_data.py         # Polymarket API data fetching
│   │   ├── news_feed.py           # News aggregation from multiple sources
│   │   ├── odds_compiler.py       # Compile "true odds" from external data
│   │   └── sentiment.py           # Basic sentiment analysis on news/social
│   ├── learning/
│   │   ├── __init__.py
│   │   ├── trade_journal.py       # Detailed logging of every trade + context
│   │   ├── performance.py         # Performance analytics and metrics
│   │   ├── lessons.py             # Extract and store lessons from trades
│   │   └── strategy_tuner.py      # Adjust parameters based on performance
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py              # Structured logging setup
│   │   ├── notifications.py       # Alert system (Telegram, email, etc.)
│   │   ├── config_loader.py       # YAML config loading with env var overrides
│   │   └── helpers.py             # Common utility functions
│   └── backtest/
│       ├── __init__.py
│       ├── backtester.py          # Historical backtesting engine
│       ├── paper_trader.py        # Paper trading with live data
│       └── data_collector.py      # Collect and store historical data
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_risk_manager.py
│   │   ├── test_order_manager.py
│   │   ├── test_position_manager.py
│   │   ├── test_edge_finder.py
│   │   ├── test_convergence.py
│   │   ├── test_kelly.py
│   │   └── test_config_loader.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_connection.py
│   │   ├── test_paper_trader.py
│   │   └── test_backtest_pipeline.py
│   └── fixtures/
│       ├── sample_market_data.json
│       ├── sample_orderbook.json
│       └── sample_news_events.json
├── research/
│   └── FINDINGS.md                # Phase 1 research output
├── docs/
│   ├── WALLET_SETUP.md
│   ├── SECURITY.md
│   ├── STRATEGY.md
│   ├── ARCHITECTURE.md
│   ├── RUNBOOK.md
│   └── CHANGELOG.md
├── scripts/
│   ├── setup_db.py                # Initialize SQLite database with schema
│   ├── health_check.py            # Quick system health check
│   └── export_trades.py           # Export trade history to CSV
├── data/
│   ├── .gitkeep
│   ├── historical/
│   │   └── .gitkeep
│   └── logs/
│       └── .gitkeep
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── README.md
├── LICENSE
└── main.py                        # Entry point with CLI argument parsing
```

### 0.2 — Create the `.gitignore`

Generate a comprehensive `.gitignore` covering Python, environment files, secrets, data, and IDE artifacts:

```gitignore
# Environment & secrets — NEVER commit these
.env
.env.*
!.env.example
*.pem
*.key

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.egg
.eggs/
venv/
.venv/
env/

# Data & databases — too large and/or sensitive
data/trades.db
data/trades.db-journal
data/historical/*.json
data/historical/*.csv
data/logs/*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Test / coverage
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Docker
docker-compose.override.yml
```

### 0.3 — Create `pyproject.toml`

This is the single source of truth for project metadata, linting, formatting, and testing config:

```toml
[project]
name = "polymarket-bot"
version = "0.1.0"
description = "Conservative, self-improving trading bot for Polymarket prediction markets"
requires-python = ">=3.11"
readme = "README.md"
license = {text = "MIT"}

[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "S",    # flake8-bandit (security)
]
ignore = ["S101"]  # Allow assert in tests

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: Unit tests (fast, no external deps)",
    "integration: Integration tests (may need API access)",
    "slow: Slow tests (backtesting, etc.)",
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
```

### 0.4 — Create `requirements.txt` and `requirements-dev.txt`

**`requirements.txt`** — production dependencies:

```txt
# Polymarket API
py-clob-client>=0.1.0
python-dotenv>=1.0.0

# HTTP & async
httpx>=0.27.0
aiohttp>=3.9.0
websockets>=12.0

# Data & storage
sqlalchemy>=2.0.0
aiosqlite>=0.20.0

# News & data feeds
feedparser>=6.0.0

# Configuration
pyyaml>=6.0.0

# Scheduling
apscheduler>=3.10.0

# Notifications
python-telegram-bot>=21.0

# Utilities
tenacity>=8.2.0          # Retry logic
structlog>=24.0.0        # Structured logging
tabulate>=0.9.0          # CLI table formatting
click>=8.1.0             # CLI argument parsing
numpy>=1.26.0            # Numerical computations
```

**`requirements-dev.txt`** — development and testing:

```txt
-r requirements.txt

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
pytest-mock>=3.12.0
freezegun>=1.3.0          # Time mocking for backtests

# Linting & formatting
ruff>=0.5.0
mypy>=1.10.0

# Pre-commit hooks
pre-commit>=3.7.0

# Type stubs
types-PyYAML
types-tabulate
types-requests
```

### 0.5 — Create the `Makefile`

A `Makefile` gives consistent commands for every operation. Every developer (and every Claude Code session) should use these:

```makefile
.PHONY: help install install-dev lint format type-check test test-unit test-integration setup-db run-backtest run-paper run-live dashboard health clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install all dependencies including dev tools
	pip install -r requirements-dev.txt
	pre-commit install

lint:  ## Run linter (ruff)
	ruff check src/ tests/ main.py

format:  ## Auto-format code
	ruff format src/ tests/ main.py
	ruff check --fix src/ tests/ main.py

type-check:  ## Run type checker (mypy)
	mypy src/ main.py

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest -m unit

test-integration:  ## Run integration tests only
	pytest -m integration

setup-db:  ## Initialize the SQLite database
	python scripts/setup_db.py

run-backtest:  ## Run backtesting
	python main.py --mode backtest

run-paper:  ## Run paper trading
	python main.py --mode paper-trade

run-live:  ## Run live trading (requires passing all gates)
	python main.py --mode live

dashboard:  ## Show performance dashboard
	python main.py --mode dashboard

health:  ## Run system health check
	python scripts/health_check.py

clean:  ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage dist build *.egg-info
```

### 0.6 — Create `.pre-commit-config.yaml`

Enforce code quality on every commit:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: detect-private-key          # Catches accidentally committed keys
      - id: check-merge-conflict

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks                    # Scans for API keys, secrets, tokens
```

### 0.7 — Create GitHub Actions CI Pipeline

**`.github/workflows/ci.yml`**:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: ruff check src/ tests/ main.py

      - name: Format check with ruff
        run: ruff format --check src/ tests/ main.py

      - name: Type check with mypy
        run: mypy src/ main.py

      - name: Run unit tests
        run: pytest -m unit --cov=src --cov-report=term-missing

      - name: Check for secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**`.github/workflows/security.yml`**:

```yaml
name: Security Audit

on:
  schedule:
    - cron: "0 8 * * 1"  # Every Monday at 8 AM
  push:
    paths:
      - "requirements*.txt"

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install pip-audit
        run: pip install pip-audit

      - name: Audit dependencies
        run: pip-audit -r requirements.txt
```

### 0.8 — Create `Dockerfile` and `docker-compose.yml`

For reproducible deployments (especially for running the live bot on a server):

**`Dockerfile`**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Non-root user for security
RUN useradd --create-home botuser && chown -R botuser:botuser /app
USER botuser

ENTRYPOINT ["python", "main.py"]
CMD ["--mode", "live"]
```

**`docker-compose.yml`**:

```yaml
version: "3.8"

services:
  bot:
    build: .
    container_name: polymarket-bot
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data          # Persist database and logs
      - ./config:/app/config      # Mount config for hot-reload
    command: ["--mode", "live"]
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"

  paper:
    build: .
    container_name: polymarket-paper
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    command: ["--mode", "paper-trade"]
    profiles: ["paper"]           # Only runs with: docker compose --profile paper up
```

### 0.9 — Create `main.py` Entry Point Stub

Create a working entry point that parses CLI args and dispatches to the correct mode. It should work immediately (printing "not yet implemented" for unbuilt modes):

```python
"""Polymarket Trading Bot — Entry Point."""

import click
import sys

from src.utils.logger import setup_logging


@click.group(invoke_without_command=True)
@click.option("--mode", type=click.Choice([
    "live", "paper-trade", "backtest", "collect-data",
    "dashboard", "review", "reconcile",
]), required=True, help="Operating mode")
@click.option("--config", default="config/settings.yaml", help="Path to config file")
@click.option("--verbose", is_flag=True, help="Enable debug logging")
def main(mode: str, config: str, verbose: bool) -> None:
    """Polymarket Conservative Trading Bot."""
    setup_logging(verbose=verbose)

    match mode:
        case "live":
            click.echo("Starting live trading...")
            # from src.core.bot import TradingBot
            # bot = TradingBot(config_path=config, paper=False)
            # bot.run()
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
```

### 0.10 — Create Stub Files with Docstrings and Type Hints

For EVERY file in the `src/` directory tree, create a stub file that contains:

1. A module-level docstring explaining the file's purpose.
2. Import statements that will be needed.
3. Class or function stubs with full type-hinted signatures, docstrings, and `raise NotImplementedError("Phase N")` bodies.
4. A clear comment at the top: `# TODO: Implement in Phase N`.

Example for `src/core/risk_manager.py`:

```python
# TODO: Implement in Phase 5
"""Risk management engine — the most critical component of the bot.

Every trade MUST pass through the RiskManager before execution.
If any check fails, the trade is rejected. No exceptions. No overrides.
"""

from dataclasses import dataclass


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    approved: bool
    reason: str
    details: dict


class RiskManager:
    """Pre-trade risk verification.

    Checks: position size, portfolio concentration, daily loss limit,
    drawdown circuit breaker, liquidity, correlation, market validity.
    """

    def check_trade(self, market_id: str, side: str, size: float, price: float) -> RiskCheckResult:
        """Run ALL risk checks on a proposed trade. Returns approval or rejection with reason."""
        raise NotImplementedError("Phase 5")

    def check_daily_loss_limit(self) -> RiskCheckResult:
        """Check if daily loss limit has been breached."""
        raise NotImplementedError("Phase 5")

    def check_drawdown_circuit_breaker(self) -> RiskCheckResult:
        """Check if max drawdown circuit breaker should trigger."""
        raise NotImplementedError("Phase 5")
```

**Do this for every file.** The goal is that after Phase 0, you can run `make lint`, `make type-check`, and `make test` (with placeholder tests) and everything passes cleanly.

### 0.11 — Create Initial Unit Test Stubs

In every test file, create test stubs that will be filled in as each phase is implemented:

```python
"""Tests for RiskManager — filled in during Phase 5."""

import pytest


class TestRiskManager:
    """Risk manager test suite."""

    @pytest.mark.unit
    def test_rejects_trade_exceeding_max_position_size(self):
        """Trade larger than max_position_pct should be rejected."""
        pytest.skip("Not yet implemented — Phase 5")

    @pytest.mark.unit
    def test_rejects_trade_when_daily_loss_limit_hit(self):
        """No new trades after daily loss limit is breached."""
        pytest.skip("Not yet implemented — Phase 5")

    @pytest.mark.unit
    def test_circuit_breaker_halts_all_trading(self):
        """Drawdown circuit breaker should halt everything."""
        pytest.skip("Not yet implemented — Phase 5")
```

### 0.12 — Create the `README.md`

Write a professional README with:

- Project name and one-line description
- Badges (CI status, Python version, license)
- Quick overview of what the bot does
- Prerequisites (Python 3.11+, Polymarket account, API keys)
- Installation instructions (`make install-dev`)
- Configuration guide (how to set up `.env` and `config/settings.yaml`)
- Usage for each mode (`make run-backtest`, `make run-paper`, `make run-live`)
- Project structure overview (brief, link to `docs/ARCHITECTURE.md` for details)
- Contributing guidelines
- Disclaimer: "This bot trades with real money. Use at your own risk. Past performance does not guarantee future results. Only trade with funds you can afford to lose."

### 0.13 — Create `docs/CHANGELOG.md`

Start the changelog from day one:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial project scaffolding and repository structure
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Docker support for deployment
- Stub files for all modules with type hints
- Makefile for common operations
```

### 0.14 — Initial Commit and Verification

After all the above is done:

```bash
# Verify everything works
make install-dev
make lint          # Should pass with zero errors
make format        # Should report no changes needed
make type-check    # Should pass (stubs with NotImplementedError are valid)
make test          # Should show all tests skipped (not failed)

# If anything fails, fix it before proceeding

# Initial commit
git add -A
git commit -m "feat: initial project scaffolding — Phase 0 complete

- Full directory structure with stub files
- CI/CD pipeline (lint, type-check, test, security audit)
- Pre-commit hooks (ruff, gitleaks, trailing whitespace)
- Docker and docker-compose for deployment
- Makefile with all common commands
- README, CHANGELOG, and documentation stubs
- .env.example with required credentials
- All config files with default values"
```

### 0.15 — Phase 0 Acceptance Criteria

**All of these must pass before moving to Phase 1:**

- [ ] `make lint` passes with zero errors
- [ ] `make format` reports no changes needed
- [ ] `make type-check` passes with zero errors
- [ ] `make test` runs and shows all tests as skipped (not errored)
- [ ] `python main.py --mode live` runs and prints "NOT YET IMPLEMENTED"
- [ ] `.gitignore` prevents `.env` from being tracked
- [ ] Every `src/` module has a stub file with docstring and type hints
- [ ] Every `tests/` module has a corresponding test stub
- [ ] `README.md` is complete and professional
- [ ] Initial git commit is clean

**Do not proceed to Phase 1 until every box is checked.**

---

## PHASE 1 — Deep Research & Knowledge Building

**Before writing a single line of code, you must conduct exhaustive research. This phase is mandatory and non-negotiable.**

### 0.1 — Understand Polymarket Fundamentals

Research and document the following thoroughly:

- **What Polymarket is**: A decentralized prediction market platform where users trade on the outcomes of real-world events. Markets resolve to $0 or $1. You profit by buying shares below their true probability and selling or holding to resolution.
- **How Polymarket works technically**: It runs on the Polygon blockchain. Users deposit USDC to trade. Each market has YES and NO shares. The price of a share represents the market's implied probability of the event occurring.
- **The CLOB (Central Limit Order Book)**: Polymarket uses an off-chain order book with on-chain settlement. Understand how limit orders, market orders, maker/taker fees, and order matching work. Research the Polymarket CLOB API in detail.
- **The Polymarket API**: Research the full REST and WebSocket API surface. Document every endpoint relevant to: reading markets, reading order books, placing orders, canceling orders, checking positions, and checking balances. The base URL, authentication method (API key + signing with your Polygon wallet private key), and rate limits.
- **Resolution mechanics**: How markets are resolved, who resolves them (UMA oracle), what happens on resolution, edge cases (ambiguous resolutions, voided markets, early resolution). This is critical — you must understand what happens to your money in every edge case.
- **Fee structure**: Maker fees, taker fees, any withdrawal or deposit fees. Factor these into every profitability calculation.
- **Liquidity dynamics**: How deep are order books typically? What markets have the most liquidity? What is slippage like on different market sizes?

### 0.2 — Study Successful Prediction Market Strategies

Research and document these known strategy categories:

- **Market-making**: Providing liquidity on both sides of the order book and profiting from the bid-ask spread. Requires careful inventory management.
- **Informed trading / edge-based**: Finding markets where you believe the true probability differs from the market price, based on superior information or analysis. This is your primary strategy.
- **Arbitrage**: Cross-market arbitrage (e.g., if related markets are inconsistent) and cross-platform arbitrage.
- **News-reactive trading**: Rapidly incorporating breaking news before the market adjusts.
- **Mean reversion**: Identifying markets that overreact to news and trading the correction.
- **Late-stage / convergence trading**: As markets approach resolution, prices converge to 0 or 1. Identifying near-certain outcomes while shares still trade at 92-98 cents.

Research what strategies have been publicly documented by successful Polymarket traders, bots, and open-source projects on GitHub. Look for:
- Open-source Polymarket bot repositories
- Blog posts or Twitter/X threads from successful prediction market traders
- Academic papers on prediction market strategies
- The Polymarket documentation and developer guides

### 0.3 — Understand the Competitive Landscape

- What bots are already operating on Polymarket? How sophisticated are they?
- What edges are already arbitraged away? What edges remain?
- How fast do markets react to news? (This determines how much time you have to act.)
- What common mistakes do retail traders on Polymarket make that a bot can exploit?

### 0.4 — Research News & Data Sources

Identify and evaluate free and accessible data sources for:

- **Real-time news**: RSS feeds, news APIs (NewsAPI, GDELT, Google News RSS), social media monitoring (Twitter/X API or scraping).
- **Polling data**: For political markets — FiveThirtyEight, RealClearPolitics, polling aggregators.
- **Sports data**: For sports markets — ESPN API, odds comparison sites.
- **Crypto/financial data**: For crypto or financial markets — CoinGecko, Yahoo Finance.
- **Weather data**: For weather-related markets.
- **Official sources**: Government websites, regulatory filing databases, official announcements.

Document which sources are reliable, how frequently they update, and how to access them programmatically.

### 0.5 — Research Output

Create a file called `research/FINDINGS.md` that contains:
- A comprehensive summary of everything learned
- Links to all key resources, API docs, and repositories found
- A pros/cons analysis of each strategy type for our conservative approach
- Your recommended strategy (with detailed justification)
- Identified risks and how to mitigate them

**Do not proceed to Phase 2 until this research document is complete and thorough.**

---

## PHASE 2 — Wallet Setup & Fund Transfer

### 1.1 — Guide: Transferring SOL from Phantom to Polymarket

The user currently holds Solana (SOL) in a Phantom wallet. Polymarket operates on the Polygon network and uses USDC. Here is the process you must document clearly for the user in a file called `docs/WALLET_SETUP.md`:

**Step-by-step instructions to include:**

1. **Convert SOL to USDC**:
   - Option A: Use Phantom's built-in swap feature to swap SOL → USDC (Solana) directly within Phantom.
   - Option B: Send SOL to a centralized exchange (Coinbase, Kraken, Binance) and sell for USDC.

2. **Bridge USDC to Polygon**:
   - If you swapped within Phantom: Use a cross-chain bridge to move USDC from Solana to Polygon. Recommended bridges: Portal (Wormhole), Allbridge, or use a centralized exchange as an intermediary.
   - If you used a centralized exchange: Withdraw USDC directly to your Polygon wallet address. Make sure to select the Polygon network when withdrawing.

3. **Set up a Polygon wallet for Polymarket**:
   - Polymarket uses a browser-based wallet. When you sign up on polymarket.com, it creates a proxy wallet for you.
   - Alternatively, you can connect MetaMask (on Polygon network) or use Polymarket's deposit flow which supports deposits from major exchanges.

4. **Deposit USDC into Polymarket**:
   - Once USDC is on Polygon, deposit it into Polymarket through the platform's deposit UI.
   - Polymarket also supports direct deposits from Coinbase, which may be the simplest path: Phantom → sell SOL on Coinbase → deposit USDC from Coinbase to Polymarket.

5. **Obtain API credentials**:
   - Go to Polymarket and generate an API key.
   - You will need your API key and your wallet's private key for signing orders via the CLOB API.
   - Document how to securely store these credentials (use environment variables, never hardcode).

**IMPORTANT**: Include gas fee estimates for each step, estimated time for each step, and the cheapest/fastest path. Recommend the simplest path first (likely: swap SOL to USDC on exchange → withdraw USDC on Polygon → deposit to Polymarket).

### 1.2 — Secure Credential Management

Create a `.env.example` file showing what environment variables are needed:

```
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_PRIVATE_KEY=your_polygon_wallet_private_key_here
POLYMARKET_API_SECRET=your_api_secret_here
NEWS_API_KEY=your_newsapi_key_here
```

Create a `docs/SECURITY.md` file covering:
- Never commit `.env` to git (ensure `.gitignore` includes it)
- Use a dedicated wallet for bot trading with only the funds you can afford to lose
- Consider using a hardware wallet for signing if available
- Key rotation practices
- Principle of least privilege — the bot wallet should only have trading funds, not your main holdings

---

## PHASE 3 — Architecture & Infrastructure

### 2.1 — Tech Stack

Use the following stack (adjust based on your research findings if better options exist):

- **Language**: Python 3.11+
- **Polymarket SDK**: `py-clob-client` (the official Python SDK for Polymarket's CLOB API). Research and use the latest version. If this SDK is insufficient, use direct HTTP requests to the API.
- **Database**: SQLite for local storage (trade history, market data, lessons learned, performance metrics). Use SQLAlchemy for ORM.
- **Scheduling**: APScheduler or a simple event loop for periodic tasks.
- **News monitoring**: `feedparser` for RSS, `httpx` or `aiohttp` for API calls.
- **Logging**: Python `logging` module with structured JSON logs. Log everything.
- **Configuration**: YAML config files for strategy parameters, with environment variable overrides.

### 2.2 — Project Structure

```
polymarket-bot/
├── config/
│   ├── settings.yaml          # All tunable parameters
│   ├── markets_watchlist.yaml  # Markets to monitor
│   └── risk_limits.yaml       # Risk management parameters
├── src/
│   ├── core/
│   │   ├── bot.py             # Main bot orchestrator
│   │   ├── market_analyzer.py # Market analysis and opportunity detection
│   │   ├── order_manager.py   # Order placement, tracking, cancellation
│   │   ├── position_manager.py# Portfolio and position tracking
│   │   └── risk_manager.py    # Risk checks before every trade
│   ├── strategy/
│   │   ├── base_strategy.py   # Abstract base class for strategies
│   │   ├── edge_finder.py     # Core strategy: find mispriced markets
│   │   ├── news_reactor.py    # News-based trading signals
│   │   └── convergence.py     # Late-stage convergence trading
│   ├── data/
│   │   ├── market_data.py     # Polymarket API data fetching
│   │   ├── news_feed.py       # News aggregation from multiple sources
│   │   ├── odds_compiler.py   # Compile "true odds" from external data
│   │   └── sentiment.py       # Basic sentiment analysis on news/social
│   ├── learning/
│   │   ├── trade_journal.py   # Detailed logging of every trade + context
│   │   ├── performance.py     # Performance analytics and metrics
│   │   ├── lessons.py         # Extract and store lessons from trades
│   │   └── strategy_tuner.py  # Adjust parameters based on performance
│   ├── utils/
│   │   ├── logger.py          # Structured logging setup
│   │   ├── notifications.py   # Alert system (email, Telegram, etc.)
│   │   └── helpers.py         # Common utility functions
│   └── backtest/
│       ├── backtester.py      # Historical backtesting engine
│       ├── paper_trader.py    # Paper trading with live data
│       └── data_collector.py  # Collect and store historical data
├── tests/
│   ├── test_strategy.py
│   ├── test_risk_manager.py
│   ├── test_order_manager.py
│   └── test_backtester.py
├── research/
│   └── FINDINGS.md
├── docs/
│   ├── WALLET_SETUP.md
│   ├── SECURITY.md
│   ├── STRATEGY.md
│   └── RUNBOOK.md
├── data/
│   ├── trades.db              # SQLite database
│   ├── historical/            # Historical market data
│   └── logs/                  # Application logs
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── main.py                    # Entry point
```

### 2.3 — Database Schema

Design tables for:

- **markets**: market_id, slug, question, category, end_date, resolution, liquidity_score, last_updated
- **trades**: trade_id, market_id, side (YES/NO), direction (BUY/SELL), price, size, timestamp, fees, order_type, status, fill_price, strategy_used, reasoning
- **positions**: position_id, market_id, side, avg_entry_price, current_size, unrealized_pnl, realized_pnl
- **trade_lessons**: lesson_id, trade_id, what_happened, what_was_expected, what_went_wrong_or_right, lesson_learned, parameter_adjustment_made, timestamp
- **performance_snapshots**: snapshot_id, timestamp, total_balance, total_pnl, win_rate, avg_profit, avg_loss, sharpe_ratio, max_drawdown
- **news_events**: event_id, timestamp, source, headline, summary, relevant_markets, sentiment_score, impact_assessment
- **strategy_parameters**: parameter_name, current_value, previous_value, changed_at, reason_for_change

---

## PHASE 4 — Strategy Design

### 3.1 — Core Philosophy: Conservative, Continuous Profits

**This bot is NOT a degen gambler. It is a patient, disciplined trader optimizing for long-term compound growth.**

Core principles:
- **High win rate over high returns**: Target 60-70% win rate with small, consistent profits rather than big bets.
- **Edge-based only**: Never trade without a quantifiable edge. If the edge is unclear, don't trade.
- **Small position sizes**: Never risk more than 2-5% of total bankroll on a single market.
- **Diversification**: Spread across multiple uncorrelated markets.
- **Patience**: It's better to make zero trades in a day than one bad trade. The bot should have strict entry criteria.

### 3.2 — Primary Strategy: Probability Edge Detection

This is a simple, automatable strategy:

1. **Compile external probability estimate**: For each active market, gather data from external sources to form an independent probability estimate. Examples:
   - Political markets: Use polling aggregator data to compute a probability.
   - Sports markets: Use bookmaker odds (converted to implied probability, adjusted for overround).
   - Event markets: Use base rates, expert opinions, and historical precedent.

2. **Compare to market price**: The Polymarket share price IS the market's implied probability. If your estimate differs significantly from the market price, there may be an edge.

3. **Quantify the edge**: Edge = (Your probability - Market probability). Only trade when:
   - The edge exceeds a minimum threshold (start with 8-10% — e.g., you believe true probability is 60% but market says 50%).
   - You have high confidence in your probability estimate (based on multiple corroborating sources).
   - The market has sufficient liquidity for you to enter and exit.

4. **Enter the trade**: Buy YES shares if your probability > market price, or buy NO shares if your probability < market price. Use limit orders to avoid slippage.

5. **Monitor and exit**:
   - Exit if your edge disappears (market moves to your estimated probability — take profit).
   - Exit if new information invalidates your thesis (cut losses).
   - Hold to resolution if conviction remains high and the market hasn't moved to your target.

### 3.3 — Secondary Strategy: News-Reactive Trading

1. **Monitor news feeds continuously** for events that directly affect active Polymarket markets.
2. **When a relevant news event is detected**:
   - Assess the likely impact on the market's probability.
   - Check if the Polymarket price has already adjusted.
   - If the market hasn't moved yet (or hasn't moved enough), place a trade.
3. **Speed matters here but accuracy matters more**. Better to be 2 minutes late and right than 10 seconds fast and wrong. The bot should validate the news from multiple sources before trading.

### 3.4 — Tertiary Strategy: Convergence Trading

1. **Identify markets approaching resolution** where the outcome is nearly certain (e.g., an election where one candidate has a 98% lead in polls, but shares trade at $0.93).
2. **Buy shares at a discount to the near-certain outcome** — e.g., buy YES at $0.93 for a market that is 98% likely to resolve YES.
3. **This is low-risk, low-reward, but highly consistent.** The risk is the 2% chance you're wrong, but the reward is nearly guaranteed profit (7 cents per share in this example).
4. **Criteria**: Only enter convergence trades where the market resolves within 14 days, your assessed probability is above 95%, and the spread is at least 3 cents.

### 3.5 — Strategy Configuration

All thresholds must be configurable in `config/settings.yaml`:

```yaml
strategy:
  edge_detection:
    min_edge_threshold: 0.08      # Minimum probability edge to enter
    confidence_required: 0.7      # Minimum confidence in estimate (0-1)
    max_markets_concurrent: 10    # Don't hold more than N positions
    min_liquidity_usd: 5000       # Skip illiquid markets
    min_time_to_resolution_hours: 24  # Don't enter markets about to close
    
  news_reactive:
    enabled: true
    min_sources_to_confirm: 2     # Require multiple sources
    max_response_time_minutes: 15 # Don't chase old news
    news_edge_threshold: 0.10     # Higher edge needed for speed trades
    
  convergence:
    enabled: true
    min_probability_for_entry: 0.95
    max_days_to_resolution: 14
    min_spread_cents: 0.03

  general:
    check_interval_seconds: 60    # How often to scan for opportunities
    order_type: "limit"           # Prefer limit orders
    limit_offset_cents: 0.01      # Place limit orders 1 cent better than best
```

---

## PHASE 5 — Risk Management Framework

**Risk management is the single most important component of this bot. Build it first and never bypass it.**

### 4.1 — Pre-Trade Risk Checks

Before ANY order is placed, the risk manager must verify ALL of the following:

1. **Position size check**: The trade size must not exceed `max_position_pct` of total bankroll (default: 3%).
2. **Portfolio concentration check**: Total exposure to any single category of market (e.g., "US Politics") must not exceed `max_category_exposure_pct` (default: 20%).
3. **Total positions check**: Must not exceed `max_concurrent_positions` (default: 10).
4. **Daily loss limit check**: If realized losses today exceed `max_daily_loss_pct` of bankroll (default: 3%), stop all trading for the rest of the day.
5. **Drawdown circuit breaker**: If total bankroll drops below `max_drawdown_pct` from peak (default: 10%), halt all trading and alert the user immediately. Require manual restart.
6. **Liquidity check**: Ensure the market's order book can absorb the trade without excessive slippage (define max acceptable slippage, default: 2%).
7. **Correlation check**: Don't enter a new position that is highly correlated with existing positions (e.g., don't bet on both "Will X win?" and "Will X's party win?" — they're the same bet).
8. **Market validity check**: Ensure the market hasn't been flagged, voided, or is in dispute.

### 4.2 — Position Sizing (Kelly Criterion — Fractional)

Use a fractional Kelly Criterion for position sizing:

```
Full Kelly: f = (p * b - q) / b
Where:
  p = your estimated probability of winning
  b = the net odds (payout / stake - 1)
  q = 1 - p (probability of losing)

Fractional Kelly: actual_size = f * kelly_fraction
```

**Use kelly_fraction = 0.25 (quarter Kelly).** This is deliberately conservative. Full Kelly is optimal for maximizing long-term growth but has massive variance. Quarter Kelly sacrifices some growth for much smoother returns and lower drawdowns.

Additionally, cap the position size at the `max_position_pct` from section 4.1 regardless of what Kelly suggests.

### 4.3 — Stop-Loss and Take-Profit Rules

- **Stop-loss**: If a position moves against you by more than `stop_loss_pct` (default: 30% of the position value), exit the position. This prevents holding losers to zero.
- **Take-profit**: If a position gains more than `take_profit_pct` (default: 50% of the position value), consider taking partial profits (sell 50% of the position). Let the rest ride to resolution.
- **Time-based exit**: If a position has been held for more than `max_hold_days` (default: 30 days) with no significant movement, re-evaluate. If the edge has disappeared, exit.

### 4.4 — Risk Configuration

```yaml
risk:
  max_position_pct: 0.03           # Max 3% of bankroll per trade
  max_category_exposure_pct: 0.20  # Max 20% in any category
  max_concurrent_positions: 10
  max_daily_loss_pct: 0.03         # Stop trading after 3% daily loss
  max_drawdown_pct: 0.10           # Circuit breaker at 10% drawdown from peak
  max_slippage_pct: 0.02           # Max 2% slippage
  kelly_fraction: 0.25             # Quarter Kelly
  stop_loss_pct: 0.30              # Cut losses at 30%
  take_profit_pct: 0.50            # Take partial profits at 50% gain
  max_hold_days: 30                # Re-evaluate after 30 days
  min_bankroll_usd: 50             # Stop trading if bankroll drops below $50
  cooldown_after_loss_minutes: 30  # Wait 30 minutes after a loss before trading
```

---

## PHASE 6 — Backtesting & Paper Trading

**No live trading until this phase is complete and results are satisfactory. This is a hard gate.**

### 5.1 — Historical Data Collection

1. **Collect historical market data from Polymarket**: Use the API to fetch all resolved markets from the past 6-12 months. For each market, collect:
   - The full price history (time series of YES share prices)
   - The order book snapshots (if available)
   - Resolution outcome and date
   - Market metadata (category, question, liquidity)

2. **Collect historical news data**: For the same time period, collect relevant news events that would have affected those markets. This is for testing the news-reactive strategy.

3. **Store everything** in the `data/historical/` directory and in the SQLite database.

### 5.2 — Backtesting Engine

Build a backtesting engine (`src/backtest/backtester.py`) that:

1. Replays historical data chronologically.
2. Simulates the bot's strategy as if it were running in real-time (no look-ahead bias — the bot can only see data that was available at the time).
3. Simulates order execution with realistic assumptions (slippage, fees, partial fills).
4. Tracks all the same metrics as live trading (PnL, win rate, drawdown, Sharpe ratio, etc.).
5. Outputs a detailed report including:
   - Total return
   - Win rate
   - Average profit per winning trade
   - Average loss per losing trade
   - Maximum drawdown
   - Sharpe ratio (if applicable — use daily returns)
   - Profit factor (gross profit / gross loss)
   - Number of trades
   - Equity curve chart (save as image or HTML)

### 5.3 — Backtesting Acceptance Criteria

The strategy MUST meet ALL of the following in backtesting before proceeding:

- Win rate ≥ 55%
- Profit factor ≥ 1.3
- Maximum drawdown ≤ 15%
- At least 50 trades in the backtest sample
- Positive total return after fees

If these criteria are not met, return to Phase 4 and adjust the strategy parameters. Document what was changed and why.

### 5.4 — Paper Trading (Simulated Live Trading)

**Polymarket does not have an official paper trading or testnet environment.** Therefore, build a paper trading system:

1. **`src/backtest/paper_trader.py`**: This connects to the LIVE Polymarket API to read real-time market data but simulates all trades internally without placing real orders.
2. It uses the exact same logic as the live bot (same strategy, same risk manager, same order sizing).
3. It maintains a simulated balance and simulated positions.
4. It runs for a minimum of **7-14 days** before live deployment.
5. Every simulated trade is logged with the same detail as a live trade (including the reasoning, the edge detected, and what the bot would have done).

### 5.5 — Paper Trading Acceptance Criteria

After the paper trading period:

- Simulated return must be positive.
- Win rate must be ≥ 55%.
- No simulated drawdown > 10%.
- The bot must have executed at least 10 simulated trades.
- Review every trade manually in the trade journal and confirm the reasoning was sound.

**Create a file `docs/PAPER_TRADING_REPORT.md` with the full results.**

Only after all criteria are met should you proceed to live trading. If not met, iterate on the strategy and re-run paper trading.

---

## PHASE 7 — Self-Improvement Engine

**This is what separates a good bot from a great bot. The bot must learn from every trade.**

### 6.1 — Trade Journal (`src/learning/trade_journal.py`)

After every trade (entry and exit), automatically record:

- **Market details**: What market, what was the question, category, time to resolution.
- **Entry reasoning**: Why did the bot enter? What was the detected edge? What was the confidence level? What data sources were used?
- **Entry details**: Price, size, order type, slippage, fees.
- **Market context at entry**: What was happening in the news? What was the order book like? What was the overall market sentiment?
- **Exit reasoning**: Why did the bot exit? Did the edge disappear? Did it hit stop-loss? Did it hit take-profit? Did the market resolve?
- **Exit details**: Price, size, fees, PnL.
- **Outcome**: Win or loss? By how much? Was the edge estimate accurate?

### 6.2 — Lesson Extraction (`src/learning/lessons.py`)

After every completed trade (position fully closed), run an analysis:

1. **Compare expected vs actual**: Did the market move the way you expected? Was your probability estimate accurate?
2. **Categorize the outcome**:
   - **Good trade, good outcome**: Edge was real, strategy worked. Reinforce this pattern.
   - **Good trade, bad outcome**: Edge was real but the low-probability outcome occurred. This is normal variance — don't change anything based on this.
   - **Bad trade, good outcome**: Got lucky. The edge wasn't really there or the reasoning was flawed. Identify why and adjust.
   - **Bad trade, bad outcome**: The reasoning was wrong and the outcome was bad. This is the most important lesson — deep-dive into what went wrong.
3. **Store the lesson** in the `trade_lessons` table with specific, actionable insights.

### 6.3 — Strategy Tuning (`src/learning/strategy_tuner.py`)

Every 20 trades (configurable), run a strategy review:

1. **Analyze recent performance**: Win rate, average PnL, drawdown, Sharpe ratio over the last 20 trades.
2. **Compare to historical performance**: Is performance improving, stable, or declining?
3. **Identify patterns**:
   - Are certain market categories more profitable than others? (Adjust category focus.)
   - Are certain times of day better? (Adjust trading schedule.)
   - Are certain edge sizes more reliable? (Adjust minimum edge threshold.)
   - Are you taking too many losses from a specific source? (Add a filter.)
4. **Propose adjustments**: Generate a list of parameter changes with justification.
5. **Apply conservatively**: Only change one parameter at a time, by a small amount (e.g., increase min_edge_threshold from 0.08 to 0.09). Never make drastic changes.
6. **Log the change**: Record in `strategy_parameters` table what changed, from what to what, and why.

### 6.4 — Performance Dashboard

Build a simple local dashboard (can be a CLI printout or a basic HTML file generated periodically) showing:

- Current bankroll and total PnL
- Open positions with unrealized PnL
- Win rate (lifetime, last 7 days, last 30 days)
- Equity curve
- Recent trades with outcomes
- Current strategy parameter values
- Recent lessons learned
- System health (last API call timestamp, any errors)

---

## PHASE 8 — Live Deployment

### 7.1 — Graduated Deployment

**Do NOT deploy full bankroll on day one.** Use a graduated approach:

1. **Week 1-2**: Deploy with 10% of intended bankroll. Max position size reduced to 1%.
2. **Week 3-4**: If Week 1-2 was profitable and stable, increase to 30% of bankroll. Max position size 2%.
3. **Week 5+**: If Week 3-4 was profitable and stable, increase to full intended bankroll. Max position size 3%.

At each stage, if the bot is unprofitable or has a drawdown > 5%, pause and review. Do not advance to the next stage.

### 7.2 — Live Trading Rules

- **The bot runs continuously** (or on a fixed schedule, e.g., every 60 seconds).
- **Every order goes through the risk manager first** — no exceptions.
- **All trades are logged** with full detail.
- **The self-improvement engine runs after every trade** and every 20-trade review cycle.
- **The user receives notifications** for: every trade executed, daily summary, any risk limit triggered, any error.

### 7.3 — Main Loop Logic

```
EVERY check_interval_seconds:
    1. Update market data (prices, order books, market list)
    2. Update news feeds
    3. Check existing positions:
       a. Any stop-loss hit? → Exit
       b. Any take-profit hit? → Partial exit
       c. Any time-based exit needed? → Re-evaluate
       d. Any market about to resolve? → Log and monitor
    4. Scan for new opportunities:
       a. Run edge detection strategy
       b. Run news-reactive strategy
       c. Run convergence strategy
    5. For each opportunity found:
       a. Calculate position size (Kelly)
       b. Run ALL risk checks
       c. If approved, place order
       d. Log everything
    6. Update performance metrics
    7. If 20-trade threshold reached, run strategy tuner
    8. Log system health
```

---

## PHASE 9 — Monitoring & Maintenance

### 8.1 — Alerts & Notifications

Set up notifications (recommend Telegram bot or email) for:

- **Every trade**: Brief summary (market, side, size, price, reasoning).
- **Daily summary**: PnL, win/loss count, open positions, bankroll.
- **Risk alerts**: Daily loss limit approaching, drawdown increasing, circuit breaker triggered.
- **Errors**: API failures, network issues, unexpected exceptions.
- **Strategy changes**: When the tuner adjusts parameters.

### 8.2 — Error Handling & Resilience

- **Retry logic**: API calls should retry with exponential backoff (3 retries, 1s/2s/4s delays).
- **Graceful degradation**: If news APIs are down, the bot should still function using other strategies.
- **State persistence**: The bot's state (open orders, positions) must survive restarts. Use the database as the source of truth.
- **Crash recovery**: On startup, the bot should check for any orphaned orders or untracked positions and reconcile with the Polymarket API.

### 8.3 — Regular Maintenance Tasks

- **Weekly**: Review the trade journal and lessons learned. Manually validate the bot's reasoning on a sample of trades.
- **Monthly**: Full performance review. Compare to a "buy and hold" benchmark if applicable. Evaluate if the strategy is still working in current market conditions.
- **Quarterly**: Deep review of all strategy parameters. Consider if market conditions have changed enough to warrant strategy changes.

---

## APPENDIX — Key Principles & Rules

### The Golden Rules (Never Violate These)

1. **Never trade without an edge.** If you can't quantify why this trade has positive expected value, don't make it.
2. **Never risk more than 3% of bankroll on a single trade.** Survival is the prerequisite for profit.
3. **Never override the risk manager.** It exists to protect you from yourself.
4. **Never deploy untested code to live trading.** Every change goes through backtest → paper trade → graduated live deployment.
5. **Log everything.** If it's not logged, it didn't happen. You can't learn from trades you can't review.
6. **When in doubt, don't trade.** The opportunity cost of a missed trade is zero. The cost of a bad trade is real.
7. **Fees are real.** Always factor in maker/taker fees, gas costs, and slippage in every profitability calculation.
8. **Markets can stay irrational longer than you can stay solvent.** Don't average down into losing positions unless the thesis is stronger than ever AND risk limits allow it.
9. **Respect the circuit breakers.** When a drawdown circuit breaker triggers, the correct action is to stop and review, not to override and chase losses.
10. **Compound slowly.** A 1% daily return sounds small. It's 3,678% annualized. Don't get greedy.

### What "Conservative" Means for This Bot

- Skip trades where the edge is marginal. You don't need to trade every market.
- Prefer markets with high liquidity and clear resolution criteria.
- Prefer markets where your external data sources are strongest (don't guess on topics you can't analyze).
- Take profits along the way rather than holding everything to resolution.
- Diversify across uncorrelated markets.
- Maintain a cash reserve — never be 100% deployed. Target 30-50% cash at all times.
- Cash reserve target: configurable, default 40% of bankroll must remain undeployed.

### How to Handle Specific Scenarios

- **Market you're in gets voided or disputed**: Do nothing. Wait for resolution. Log the event. This is why you diversify.
- **Flash crash in a market**: Do NOT buy the dip unless your edge model confirms it. Flash crashes can be informational.
- **Your overall strategy is unprofitable for 2+ weeks**: Pause live trading. Return to paper trading. Review everything.
- **A single trade wipes out a week of profits**: This will happen. It's normal variance. Check the trade journal — was the reasoning sound? If yes, it's fine. If no, learn and adjust.
- **API goes down**: Cancel all open orders immediately if possible. Wait for API recovery. Reconcile state on restart.
- **You discover a bug in the strategy code**: Immediately pause live trading. Fix the bug. Review all trades that may have been affected. Resume with paper trading first.

---

## HOW TO RUN THIS PROJECT

### Initial Setup
```bash
# Clone / create the project
mkdir polymarket-bot && cd polymarket-bot

# Set up Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies (generated during Phase 0)
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your actual keys
```

### Phase Execution
```bash
# Phase 0: Repo scaffolding (this should already be done)
make install-dev
make lint
make test

# Phase 1: Research (manual — read, document, store in research/)

# Phase 6a: Collect historical data
python main.py --mode collect-data

# Phase 6b: Run backtest
python main.py --mode backtest

# Phase 6c: Run paper trading
python main.py --mode paper-trade

# Phase 8: Live trading (only after paper trading is approved)
python main.py --mode live

# Utilities
python main.py --mode dashboard    # View performance dashboard
python main.py --mode review       # Run strategy review
python main.py --mode reconcile    # Reconcile positions with exchange
```

---

## FINAL INSTRUCTION TO CLAUDE CODE

**Execute this project in the phase order specified above. Do not skip phases. Do not take shortcuts. At each phase gate (especially Phase 6), stop and present the results before proceeding. If any acceptance criteria are not met, iterate until they are. Build this as if real money depends on it — because it will.**

**Start with Phase 0. Scaffold the repo. Verify everything passes. Then proceed one phase at a time.**
