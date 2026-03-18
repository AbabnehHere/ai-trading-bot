# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial project scaffolding and repository structure (Phase 0)
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Docker support for deployment
- Makefile for common operations

### Phase 1 — Research
- Comprehensive research findings in `research/FINDINGS.md`
- Polymarket API, strategies, competitive landscape, data sources

### Phase 2 — Documentation
- Wallet setup guide (`docs/WALLET_SETUP.md`)
- Security guide (`docs/SECURITY.md`)

### Phase 3 — Architecture & Infrastructure
- SQLite database schema (7 tables: markets, trades, positions, lessons, etc.)
- Configuration loader with YAML + env var overrides
- Polymarket API client (`py-clob-client` + REST fallback)
- News feed aggregator (RSS from Reuters, BBC, AP, Google News)
- Sentiment analyzer (keyword-based scoring)
- Order manager (live + paper trading modes)
- Position manager with P&L tracking
- Notification system (Telegram alerts)
- Health check script
- Trade export script

### Phase 4 — Strategies
- Edge detection strategy (probability mispricing)
- News-reactive strategy (multi-source confirmation)
- Convergence strategy (near-resolution trading)
- Market analyzer with quality filters
- Odds compiler (multi-source probability estimation)

### Phase 5 — Risk Management
- 8 pre-trade risk checks (position size, drawdown, daily loss, cooldown, etc.)
- Fractional Kelly Criterion position sizing (quarter Kelly)
- Stop-loss and take-profit rules
- Circuit breaker (10% drawdown halts all trading)
- Configurable risk parameters in `config/risk_limits.yaml`

### Phase 6 — Backtesting & Paper Trading
- Historical data collector
- Backtesting engine with metrics (Sharpe, drawdown, P&L)
- Paper trading system (live data, simulated orders)

### Phase 7 — Self-Improvement
- Trade journal with full context recording
- Performance tracker (win rate, Sharpe, profit factor)
- Lesson extractor (categorizes trade outcomes)
- Strategy tuner (automatic parameter adjustment suggestions)
- Performance dashboard (CLI)

### Phase 8 — Live Deployment
- Full bot orchestrator with trading loop
- Graduated deployment support
- All operating modes: live, paper-trade, backtest, collect-data, dashboard, review

### Phase 9 — Monitoring & Maintenance
- Telegram notification system (trades, errors, daily summaries, risk alerts)
- System health check script
- Error handling with structured logging
