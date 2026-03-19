# Lessons Learned

Accumulated from trading reviews. Updated by Claude Code during every review cycle.

## Market Analysis
- Sports markets are efficient — always skip, no edge possible
- Musk tweet-count markets are pure noise — skip permanently
- External military pressure consolidates regimes (rally-around-flag effect) — don't bet on regime change just because of war
- Crude oil 52-week high was $119 — so $110 is historically possible, monitor carefully
- Thin edges (<5% after fees) aren't worth the capital lockup
- Always fetch live prices before assessing commodity/crypto markets — without current price, you're blind
- Markets price in wars within hours — late reactions have no edge
- NEVER trust news headline prices as "current price" — a headline saying "$110" could mean forecast, target, historical, or actual. Headlines are ambiguous.
- Trust structured API prices (Yahoo Finance, CoinGecko) over news headlines for the actual number. APIs return specific data fields, news returns unstructured text.
- If API price and news price conflict, DO NOT panic-trade. Flag it for manual review. The API is more likely correct — stale by minutes, not by $15.
- NEVER issue a stop-loss based on a single unverified price source. The crude oil false alarm ($96 API vs "$110" news headline) would have caused a real loss.

## Fee Awareness
- 2% taker fee on entry AND exit eats small edges
- A 1-cent price move is unprofitable after fees
- Convergence trades ($0.95→$1.00) only yield ~$0.01/share after both-way fees
- Always calculate edge AFTER fees before signaling

## Rate Limiting
- Yahoo Finance returns 429 after ~45 calls in a session — don't price-check every 60s cycle
- Limit price checks to top 5 asset markets per cycle, not 15
- Limit Google News fetches to top 8 markets per cycle — 15 was too many, caused stuck cycles

## Position Management
- ALWAYS include open position markets in every scan — even if they drop out of top volume rankings
- A position that disappears from the scan can't be monitored for stop-loss/take-profit
- The Iran regime market dropped out of top 20 by volume and we stopped tracking it — dangerous

## Bot Operations
- Don't pkill the bot during git commits — it dies
- Ghost trades appear if PositionManager reloads from DB during tests (use skip_db_reload)
- Metaculus API returns 403 — circuit breaker disables it after first failure
- Bot cycle time must stay under 60 seconds — RSS/API calls for 200 markets caused 3+ min cycles
- Position state is lost on restart unless reloaded from DB

## Strategy
- Conservative is correct — 2 trades in 3 hours is the right pace
- Only trade when edge > 10% after fees AND high confidence
- Maintain 90%+ cash reserve during paper trading
- The bot should be the eyes (data), Claude should be the brain (analysis)
