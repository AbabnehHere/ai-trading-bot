# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                   main.py (CLI)                      │
│              Click CLI argument parsing              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              TradingBot (src/core/bot.py)            │
│         Main orchestrator — coordinates all          │
│         components in the trading loop               │
└──┬───────┬──────────┬───────────┬──────────┬────────┘
   │       │          │           │          │
   ▼       ▼          ▼           ▼          ▼
┌──────┐┌───────┐┌─────────┐┌────────┐┌──────────┐
│Market││Order  ││Position ││ Risk   ││ Market   │
│Data  ││Manager││Manager  ││Manager ││ Analyzer │
│Client││       ││         ││        ││          │
└──┬───┘└───────┘└─────────┘└────────┘└────┬─────┘
   │                                        │
   ▼                                        ▼
┌──────────────────┐            ┌──────────────────┐
│   Data Layer     │            │   Strategies     │
│ - News Feed      │            │ - Edge Finder    │
│ - Odds Compiler  │            │ - News Reactor   │
│ - Sentiment      │            │ - Convergence    │
└──────────────────┘            └──────────────────┘

┌─────────────────────────────────────────────────────┐
│              Learning System                         │
│  Trade Journal │ Performance │ Lessons │ Tuner      │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              SQLite Database (data/trades.db)        │
│  markets │ trades │ positions │ lessons │ snapshots  │
└─────────────────────────────────────────────────────┘
```

## Trading Cycle (Main Loop)

Every `cycle_interval_seconds` (default: 60s in dev, 300s in prod):

1. **Check existing positions** — stop-loss, take-profit, time-based exit
2. **Scan markets** — fetch active markets, apply quality filters
3. **Find opportunities** — run all strategies against candidates
4. **For each signal**:
   - Calculate position size (Kelly criterion)
   - Run ALL risk checks (8 checks)
   - If approved, place order
   - Record trade in journal
5. **Update metrics** — performance snapshot
6. **Strategy review** — every 20 trades, suggest parameter adjustments

## Component Details

### Core (`src/core/`)
- **bot.py** — Main orchestrator, trading loop, component wiring
- **market_analyzer.py** — Market scanning, filtering, opportunity detection
- **order_manager.py** — Order placement via CLOB API (or paper simulation)
- **position_manager.py** — Portfolio tracking, P&L calculation, drawdown
- **risk_manager.py** — 8 pre-trade risk checks, Kelly sizing, stop-loss/take-profit

### Strategies (`src/strategy/`)
- **base_strategy.py** — Abstract base class, TradeSignal dataclass
- **edge_finder.py** — Mispricing detection using compiled probability estimates
- **news_reactor.py** — News-driven signals with multi-source confirmation
- **convergence.py** — Near-resolution market trading

### Data (`src/data/`)
- **market_data.py** — Polymarket API client (CLOB + Gamma APIs)
- **news_feed.py** — RSS feed aggregation from major news sources
- **odds_compiler.py** — Multi-source probability compilation
- **sentiment.py** — Keyword-based sentiment analysis

### Learning (`src/learning/`)
- **trade_journal.py** — Trade recording and history queries
- **performance.py** — Metrics calculation (win rate, Sharpe, drawdown)
- **lessons.py** — Post-trade analysis and lesson extraction
- **strategy_tuner.py** — Automatic parameter adjustment suggestions

## Database Schema

7 tables: markets, trades, positions, trade_lessons, performance_snapshots, news_events, strategy_parameters

See `scripts/setup_db.py` for full schema.

## Configuration

Layered configuration system:
1. `config/settings.yaml` — Base config
2. `config/settings.dev.yaml` — Dev overrides
3. `config/settings.prod.yaml` — Production overrides
4. Environment variables (`POLYBOT_*` prefix) — Highest priority
