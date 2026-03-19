# Claude Code Instructions for Polymarket Bot

## Research Skills (use these during reviews!)

You have research tools in `.claude/skills/`:
- **get_prices.md** — Fetch live prices for crude oil, gold, crypto, stocks via WebFetch
- **get_news.md** — Fetch breaking news by topic via Google News RSS, Reuters, BBC
- **research_market.md** — Full research process for assessing a Polymarket market

**IMPORTANT:** During every market review, always:
1. Fetch live prices for any market referencing a price target (crude oil, bitcoin, etc.)
2. Fetch topic-specific news for geopolitical markets (Iran, politics, etc.)
3. Use the research_market skill for deep dives on promising opportunities

## Quick Start

When the user says "start the bot reviews" or "start reviews", set up these cron jobs:

### 1. News Analysis (every 5 minutes)
Read `data/reports/market_scan.json`. For each non-sports market in the top 20:
- Read the question, YES price, and recent_news headlines
- **Fetch live prices** for commodity/crypto markets using `.claude/skills/get_prices.md`
- **Fetch topic news** for geopolitical markets using `.claude/skills/get_news.md`
- Estimate the TRUE probability independently based on all evidence
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
- Use research skills to deep-dive on all open positions
- Suggest or apply config changes
- Write to `data/logs/nightly_review.log`

## Bot Management
- Start bot: `./scripts/start_bot.sh` (or `./scripts/start_bot.sh live`)
- Stop bot: `pkill -f 'main.py --mode'`
- Dashboard: `python scripts/dashboard_web.py` (http://localhost:8050)
- Logs: `tail -f data/logs/bot.log`

## How Signals Work
The bot reads `data/reports/signals.json` every cycle (60s). Claude Code writes
trade signals there after analyzing markets. The bot validates signals through
the risk manager before executing. All signals go through risk checks — they
can be rejected if position limits, daily loss limits, or other rules are violated.

## Rules

### Always Record Lessons Learned
After EVERY market review and strategy review, record lessons learned:
- What worked and what didn't
- New patterns discovered (e.g., "sports markets are always efficient")
- Mistakes made (e.g., "ghost trades from pkill during commit")
- Edge cases found (e.g., "crude oil 52-week high was $119, so $110 isn't impossible")
- Append lessons to `data/logs/claude_review.log` with each review entry
- Add durable lessons to `.claude/lessons_learned.md` (the permanent record)
- **Read `.claude/lessons_learned.md` at the start of every session** to avoid repeating mistakes

### Never Ask for Permission During Reviews
Market reviews, strategy reviews, price fetches, news fetches, log writes, and
database queries should all run autonomously without asking the user. Permissions
are configured in `.claude/settings.local.json`.

### Price Verification Rules
- **Trust API prices over news headlines.** Yahoo Finance and CoinGecko return structured data fields. News headlines are ambiguous — "$110" could mean forecast, target, historical, or current.
- **If API and news prices conflict by >10%, DO NOT trade.** Flag it for manual review. Never panic-trade on a price discrepancy.
- **Never issue a stop-loss based on a single unverified source.** A false price alarm causes real losses.
- News headlines are useful for **direction** (surging/crashing) but not for **exact prices.**

### Claude Code CLI (`claude -p`) Limitations
The `claude -p` headless mode CANNOT use tools (WebFetch, Bash, Read).
The bot must fetch all data (prices, news, market data) FIRST using Python,
then pass it to `claude -p` as context in the prompt. The bot researches,
Claude thinks.

## Key Files
- `config/settings.yaml` — Strategy parameters (edge thresholds, risk limits)
- `data/reports/market_scan.json` — Latest market opportunities (updated every 60s)
- `data/reports/signals.json` — Trade signals for bot to execute
- `data/reports/trade_log.json` — Current positions and recent trades
- `data/trades.db` — Full trade history database
- `.claude/skills/` — Research tools (prices, news, market analysis)
