# Claude Code Instructions for Polymarket Bot

## Quick Start

When the user says "start the bot reviews" or "start reviews", set up these cron jobs:

### 1. News Analysis (every 5 minutes)
Read `data/reports/market_scan.json`. For each non-sports market in the top 20:
- Read the question, YES price, and recent_news headlines
- Estimate the TRUE probability independently based on news and knowledge
- Compare to market price — is there a >10% edge after 2% fees?
- If confident edge found, read `data/reports/signals.json`, add signal, write back
- Signal format: `{"market_id": "id", "token_id": "", "side": "BUY", "size": 20, "price": the_price, "reasoning": "explanation"}`
- Append one line to `data/logs/claude_review.log`

### 2. Strategy Review (every 15 minutes)
- Check bot is running: `pgrep -f paper-trade`
- Read last 50 lines of `data/logs/bot.log` for errors
- Check `data/reports/market_scan.json` is being updated
- Check `data/reports/trade_log.json` for positions
- Query database: `sqlite3 data/trades.db "SELECT COUNT(*) FROM trades;"`
- Assess workflow efficiency, fix issues, adjust `config/settings.yaml` if needed
- Append summary to `data/logs/strategy_review.log`

### 3. Nightly Deep Review (midnight)
- Full performance analysis from database
- Review all trades, lessons, and strategy parameters
- Suggest or apply config changes
- Write to `data/logs/nightly_review.log`

## Bot Management
- Start bot: `./scripts/start_bot.sh` (or `./scripts/start_bot.sh live`)
- Stop bot: `pkill -f 'main.py --mode'`
- Dashboard: `python scripts/dashboard.py`
- Logs: `tail -f data/logs/bot.log`

## How Signals Work
The bot reads `data/reports/signals.json` every cycle (60s). Claude Code writes
trade signals there after analyzing markets. The bot validates signals through
the risk manager before executing. All signals go through risk checks — they
can be rejected if position limits, daily loss limits, or other rules are violated.

## Key Files
- `config/settings.yaml` — Strategy parameters (edge thresholds, risk limits)
- `data/reports/market_scan.json` — Latest market opportunities (updated every 60s)
- `data/reports/signals.json` — Trade signals for bot to execute
- `data/reports/trade_log.json` — Current positions and recent trades
- `data/trades.db` — Full trade history database
