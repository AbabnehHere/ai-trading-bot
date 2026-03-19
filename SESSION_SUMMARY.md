# Session Summary — March 19, 2026

## Active Cron Jobs

| Interval | ID | Purpose | Expires |
|----------|-----|---------|---------|
| Every 5 min | `d68c21b5` | Market review — analyze non-sports markets, fetch prices, find edges, write signals | 3 days |
| Every 15 min | `5e9726c6` | Strategy review — check bot health, fix bugs, assess workflow efficiency | 3 days |
| Midnight | `2dad470a` | Deep review — full performance analysis, parameter tuning, lessons update | 3 days |

**Note:** Crons die when this Claude Code session closes. Bot keeps running independently.

---

## Current Portfolio (as of 14:25 UTC)

| # | Position | Entry | Shares | Cost | Status | Exit Strategy |
|---|----------|-------|--------|------|--------|---------------|
| 6 | Iran regime Jun30 — NO | $0.725 | 20 | $14.79 | HOLD | Resolution Jun 30 / stop $0.60 |
| 11 | Crude Oil $120 Mar31 — NO | $0.775 | 20 | $15.81 | HOLD | Resolution Mar 31 / stop if oil >$115 |
| ~~7~~ | ~~Crude Oil $110 Mar31 — NO~~ | ~~$0.59~~ | ~~20~~ | ~~$12.05~~ | ~~CLOSED~~ | ~~Panic stop-loss (false alarm)~~ |

**Cash:** $998.92 | **Deployed:** ~$30 (3%) | **Total:** ~$998.92

---

## Timeline of Key Events

| Time (UTC) | Event |
|------------|-------|
| 08:26 | Session started. Phase 0-9 of bot already built |
| 10:41 | Identified critical flaws: circular odds compiler, no fee accounting, no tests |
| 10:55 | Rebuilt odds compiler with independent sources, fixed fees, wrote 54 real tests |
| 11:15 | First market review — 200 markets scanned, no edges found (keyword analysis too weak) |
| 11:30 | **TRADE #1:** BUY NO on "Iranian regime fall by June 30" @ $0.725 — edge 13.6% after fees |
| 11:31 | Signal executed by bot — first paper trade! |
| 11:35 | Fixed critical bottleneck: cycle time from 3+ minutes to 4 seconds (Metaculus 403 loop) |
| 11:55 | Integrated Claude Code as the brain — bot writes reports, Claude analyzes |
| 12:00 | Set up cron jobs: 5min news, 15min strategy, midnight deep review |
| 12:05 | Added live price fetching (Yahoo Finance, CoinGecko) — crude at $96.85 |
| 12:05 | **TRADE #2:** BUY NO on "Crude Oil $110 by March 31" @ $0.59 — edge 17% after fees |
| 12:08 | Trade executed. Portfolio: 2 positions, $999.47 |
| 13:00 | Fresh news via Google News: Day 20 of US-Israel war with Iran |
| 13:35 | New market: Bitcoin $65K dip at 53.4% — fairly priced, no edge |
| 13:55 | **PRICE SCARE:** News headlines said crude at $110-115, Yahoo API said $96. Panic stop-loss on Trade #2 |
| 14:00 | **LESSON LEARNED:** Never trust news headline prices. Trust APIs. Added price verification rules |
| 14:01 | Major upgrades: 3-source market scan (541→335 mkts), Google News per market, price cross-referencing |
| 14:08 | **TRADE #3:** BUY NO on "Crude Oil $120 by March 31" @ $0.775 — edge 11% after fees |
| 14:15 | News + summaries added. 24h window. Polymarket listing filter. All positions trending well |

---

## Bugs Found & Fixed

| Time | Bug | Impact | Fix |
|------|-----|--------|-----|
| 11:35 | Metaculus API 403 on every call (200/cycle) | 3+ min cycles | Circuit breaker after first 403 |
| 11:35 | Built-in strategies calling RSS for 200 markets | 3+ min cycles | Disabled — Claude Code is the brain |
| 11:59 | Positions lost on restart (in-memory only) | Lost track of trades | Reload from DB on startup |
| 12:01 | Empty token_id causing 400 error every cycle | Log spam | Skip midpoint check for empty IDs |
| 12:19 | Daily counter reset bug in risk manager | Would bypass daily limits | Initialize _current_day to today |
| 13:28 | Ghost trades from test suite using real DB | Corrupt trade history | skip_db_reload param for tests |
| 14:00 | Trusted news headline price ($110) over API ($96) | False stop-loss | Trust API, flag discrepancy |

---

## Lessons Learned (saved in .claude/lessons_learned.md)

1. Sports markets are efficient — always skip
2. Musk tweet-count markets are pure noise — skip permanently
3. External military pressure consolidates regimes (rally-around-flag)
4. Crude oil 52-week high was $119 — $110 is historically possible
5. Thin edges (<5% after fees) aren't worth capital lockup
6. Don't pkill the bot during git commits
7. NEVER trust news headline prices — trust structured APIs
8. NEVER issue stop-loss based on single unverified source
9. Always read news summaries, not just headlines
10. 12-hour news filter was too strict — use 24 hours
11. Google News returns Polymarket listings — filter them out

---

## System Architecture (Current)

```
Bot (Python, PID 31114)              Claude Code (this session)
─────────────────────                ──────────────────────────
Every 60s:                           Every 5 min:
  Scan 335 markets (3 sources)         Read market_scan.json
  Write market_scan.json               Fetch live prices (WebFetch)
  Write trade_log.json                 Fetch topic news (WebFetch)
  Read signals.json → execute          Analyze for edges
  Risk check all signals               Write signals.json if edge found

                                     Every 15 min:
                                       Check bot health
                                       Fix bugs if found
                                       Review strategy efficiency

                                     Midnight:
                                       Deep performance analysis
                                       Parameter tuning
                                       Lessons update
```

---

## To Restart Everything (new session)

1. **Start bot:** `./scripts/start_bot.sh` (from external terminal)
2. **Open Claude Code** and say: "start the bot reviews"
3. **Dashboard:** http://localhost:8050
