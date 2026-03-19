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
- NEVER trust a single price source — Yahoo Finance API returned $96.91 while actual crude was $110-115. Always cross-reference with news headlines
- Use Google News search for real-time price confirmation, not just financial APIs (APIs can be stale/delayed)

## Fee Awareness
- 2% taker fee on entry AND exit eats small edges
- A 1-cent price move is unprofitable after fees
- Convergence trades ($0.95→$1.00) only yield ~$0.01/share after both-way fees
- Always calculate edge AFTER fees before signaling

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
