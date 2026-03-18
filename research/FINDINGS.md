# Research Findings — Phase 1

## 1. Polymarket Fundamentals

### What Polymarket Is
Polymarket is a decentralized prediction market platform where users trade on the outcomes of real-world events. Markets resolve to $0 or $1. Profit comes from buying shares below their true probability and selling or holding to resolution.

### Technical Architecture
- **Blockchain**: Runs on the **Polygon** network (chain ID 137)
- **Currency**: USDC (USD Coin) for all trading
- **Market structure**: Each market has YES and NO shares. Prices represent implied probability (0-1)
- **Settlement**: On-chain settlement on Polygon via CTF (Conditional Token Framework)
- **Oracle**: Markets are resolved by **UMA's Optimistic Oracle** — a decentralized dispute resolution system

### CLOB (Central Limit Order Book)
- Polymarket uses a **hybrid model**: off-chain order book with on-chain settlement
- Orders are placed off-chain via the CLOB API for speed
- Settlement and token transfers happen on-chain
- Supports **limit orders** (preferred) and effectively market orders (aggressive limits)
- Maker/taker model for fees

### API Surface

#### Authentication (Two-Layer)
1. **API Key Auth**: Derive API credentials (key, secret, passphrase) by signing with your Polygon wallet private key. Headers: `POLY_API_KEY`, `POLY_API_SECRET`, `POLY_PASSPHRASE`, `POLY_TIMESTAMP`, `POLY_SIGNATURE` (HMAC-SHA256)
2. **Order Signing**: Orders signed with wallet private key using EIP-712 typed data (CTF Exchange order struct)

#### REST Endpoints

| Base URL | Purpose |
|----------|---------|
| `https://clob.polymarket.com` | Trading API (auth required for writes) |
| `https://gamma-api.polymarket.com` | Market data (public, richer metadata) |

**Public (no auth):**
- `GET /markets` — List all markets (paginated with `next_cursor`)
- `GET /markets/{condition_id}` — Single market
- `GET /book?token_id=X` — Order book
- `GET /midpoint?token_id=X` — Midpoint price
- `GET /spread?token_id=X` — Spread
- `GET /prices` — Current mid-market prices
- `GET /last-trade-price` — Last trade price

**Trading (auth required):**
- `POST /order` — Place order (GTC, GTD, FOK, IOC)
- `DELETE /order/{id}` — Cancel single order
- `POST /cancel-orders` — Cancel multiple orders
- `POST /cancel-all` — Cancel all orders
- `POST /cancel-market-orders` — Cancel all for a market
- `GET /orders` — List open orders
- `GET /trades` — Trade history
- `GET /positions` — Current positions
- `GET /balance` — USDC balance

**Order types**: GTC (Good Till Cancelled), GTD (Good Till Date), FOK (Fill or Kill), IOC (Immediate or Cancel)

#### WebSocket API
- **URL**: `wss://ws-subscriptions-clob.polymarket.com/ws`
- **Channels**: `market` (price changes), `book` (orderbook deltas), `trades` (executions), `user` (auth — order updates)
- Standard ping/pong for keepalive

#### Rate Limits
- ~100 requests per 10 seconds (~10 req/s) per API key
- Public endpoints: ~10 req/s
- HTTP 429 with `Retry-After` header on limit

### Python SDK: `py-clob-client`
- **Install**: `pip install py-clob-client`
- **Key class**: `ClobClient(host, key, chain_id, signature_type)`
  - `signature_type=0` for EOA wallets, `=2` for Polymarket proxy wallets
- **Auth**: `client.derive_api_key()` → `ApiCreds(api_key, api_secret, api_passphrase)`
- **Trading**: `client.create_and_post_order(OrderArgs(price, size, side, token_id), OrderType.GTC)`
- **Queries**: `client.get_markets()`, `client.get_order_book(token_id)`, `client.get_positions()`, `client.get_balance()`
- **Cancel**: `client.cancel(order_id)`, `client.cancel_all()`
- **GitHub**: https://github.com/Polymarket/py-clob-client

### Fee Structure
- **Maker fee**: **0%** (limit orders that add liquidity — free!)
- **Taker fee**: **~2%** (orders that remove liquidity / cross the spread)
- **No deposit/withdrawal fees** on Polymarket itself (only Polygon gas ~$0.01)
- **Strategy implication**: Always use limit orders to avoid taker fees

### Resolution Mechanics
- Binary outcome tokens via **Gnosis Conditional Token Framework (CTF)**
- YES + NO always = $1.00 (complementary tokens)
- Resolved by **UMA Optimistic Oracle**:
  1. Proposer submits resolution (YES=1, NO=0)
  2. 2-hour challenge window
  3. If undisputed → finalized
  4. If disputed → UMA DVM token holder vote (multi-day)

**Resolution outcomes:**
| Outcome | YES value | NO value |
|---------|-----------|----------|
| YES | $1.00 | $0.00 |
| NO | $0.00 | $1.00 |
| Voided/Invalid | $0.50 | $0.50 |

**Edge cases:**
- **Voided markets**: Ambiguous question → both tokens at $0.50
- **Disputed resolution**: Multi-day DVM voting period, trading continues with uncertainty
- **Early resolution**: Can resolve before end date if outcome becomes known
- **Redemption**: Call `redeemPositions()` on CTF contract after resolution

### Key Reference Links
- **Docs**: https://docs.polymarket.com
- **CLOB API**: https://docs.polymarket.com/#clob-api
- **py-clob-client**: https://github.com/Polymarket/py-clob-client
- **Gamma API**: https://gamma-api.polymarket.com

---

## 2. Successful Prediction Market Strategies

### Strategy Analysis for Our Conservative Approach

| Strategy | Risk | Reward | Automatable | Recommendation |
|----------|------|--------|-------------|----------------|
| **Edge Detection** | Medium | Medium | High | **PRIMARY** — Core strategy |
| **News-Reactive** | High | High | Medium | **SECONDARY** — With caution |
| **Convergence** | Low | Low | High | **TERTIARY** — Steady income |
| Market Making | High | Low-Med | High | Not recommended — capital intensive |
| Arbitrage | Low | Very Low | High | Limited opportunities remaining |
| Mean Reversion | Medium | Medium | Medium | Not enough data to validate |

### Primary: Edge Detection (Probability Mispricing)
- **Approach**: Compare Polymarket prices to independently compiled probability estimates
- **Sources**: Polling aggregators, bookmaker odds, news sentiment, expert consensus
- **Minimum edge**: 8-10% to account for fees and estimation error
- **Strengths**: Systematic, data-driven, can be validated
- **Weaknesses**: Requires reliable external probability sources, edge may be small

### Secondary: News-Reactive Trading
- **Approach**: Monitor news feeds for events that shift market probabilities before the market adjusts
- **Speed vs accuracy**: Better to be 2 minutes late and right than 10 seconds fast and wrong
- **Multiple source confirmation**: Require at least 2 independent sources
- **Strengths**: Can capture large moves, high conviction trades
- **Weaknesses**: Speed competition with other bots, risk of false signals

### Tertiary: Convergence Trading
- **Approach**: Buy near-certain outcomes at a discount (e.g., 95% probability at $0.93)
- **Criteria**: >95% confidence, <14 days to resolution, >3 cent spread
- **Strengths**: Low risk, high win rate, very consistent
- **Weaknesses**: Small profit per trade, requires high volume to be meaningful

---

## 3. Competitive Landscape

### Bot Tiers on Polymarket

**Tier 1: Professional (est. 5-15 operators)**
- Professional market-making firms (likely Jump Trading, Wintermute, etc.) providing liquidity with tight spreads
- AI-powered multi-agent systems (e.g., Autonolas/Olas agents)
- Well-funded individual traders with private polling data (e.g., "Theo" — the French whale who reportedly made ~$50M on 2024 election using commissioned private polls)

**Tier 2: Semi-Automated (est. 50-200 operators)**
- Model-driven traders running polling/statistical models with scripted execution
- Arbitrage scanners checking overround across multi-outcome markets
- News-reactive bots using Twitter API + LLM parsing

**Tier 3: Simple Bots (est. 200-1000+)**
- Basic scripts using py-clob-client for order placement
- Copy-trading bots following large wallets
- Simple rule-based bots ("buy if price < X")

### Market Reaction Speed
- **Major breaking news** (AP calls, official announcements): 30 seconds to 2 minutes for 80%+ adjustment
- **Polling releases**: 5-30 minutes (requires model interpretation)
- **Rumors / unconfirmed**: 1-5 minutes with potential reversion
- **Niche / non-English news**: Hours to days — **real edge for specialized data**
- **Crypto-related markets**: Seconds (heavy crypto trader overlap)

### Edges Arbitraged Away
- Simple YES/NO complement mispricing (persists only seconds)
- Stale quote picking on major news for high-volume markets
- Basic cross-outcome arbitrage on popular markets (tight 1-3% overround)

### Edges That Remain
- **Niche/low-liquidity markets**: Thin books, less efficient, model-driven mispricing
- **Multi-outcome overround on smaller markets**: 3-8% violations persist
- **Cross-platform arbitrage** (Polymarket vs. Kalshi): Requires capital on both platforms
- **News-reactive on non-obvious news**: State-level polling, regulatory filings, scientific publications
- **Favorite-longshot bias**: Longshot outcomes (<10%) are systematically overpriced — selling is +EV
- **New market mispricing**: Initial prices on newly launched markets are often poor
- **Late-stage convergence**: 3-8% returns on near-certain outcomes
- **Correlation / conditional markets**: Related markets mispriced relative to each other

### Exploitable Retail Trader Mistakes
1. **Overreacting to news** — panic buy/sell on headlines without assessing probability impact
2. **Favorite-longshot bias** — overpaying for longshot outcomes (<10%)
3. **Ignoring overround** — buying YES on all outcomes without realizing total > $1.00
4. **Market orders in thin books** — crossing wide spreads, giving market makers free money
5. **Anchoring to stale prices** — small adjustments vs. re-evaluating from first principles
6. **Ignoring time value** — locking capital in 95c positions for months
7. **Confirmation bias** — overweighting information confirming existing beliefs
8. **Fee ignorance** — not factoring ~2% taker fee into expected value calculations
9. **Correlation blindness** — not pricing correlated events properly

---

## 4. Data Sources

### Real-Time News
| Source | URL | Access | Notes |
|--------|-----|--------|-------|
| AP News RSS | rss.ap.org | Free | Gold standard for verified breaking news |
| Reuters RSS | reuters.com/arc/outboundfeeds | Free | Comprehensive global news |
| Google News RSS | news.google.com/rss | Free | Aggregated, filterable by topic |
| BBC RSS | feeds.bbci.co.uk/news/rss.xml | Free | International coverage |
| NewsAPI | newsapi.org | Free tier (100/day) | 80k+ sources aggregated |
| GDELT Project | gdeltproject.org | Free | Global event monitoring, 15-min cycles |
| Newscatcher API | newscatcherapi.com | Free tier | Structured news data |

### Political Data
| Source | URL | Notes |
|--------|-----|-------|
| FiveThirtyEight/538 | projects.fivethirtyeight.com/polls | Polling database with CSV downloads |
| RealClearPolitics | realclearpolitics.com/epolls | Polling averages (scraping required) |
| 270toWin | 270towin.com | Electoral maps, polling aggregation |
| Race to the WH | racetothewh.com | State-level polling averages |
| Congress API | api.congress.gov | Bills, votes, legislative data |

### Sports Data
| Source | URL | Notes |
|--------|-----|-------|
| ESPN API (unofficial) | site.api.espn.com/apis/site/v2/sports | Scores, schedules, odds |
| Odds API | the-odds-api.com | Free tier (500 req/mo), aggregated bookmaker odds |
| API-Football | api-football.com | Free tier, comprehensive soccer |
| nba_api (Python) | github.com/swar/nba_api | Free NBA stats |

### Crypto / Financial Data
| Source | URL | Notes |
|--------|-----|-------|
| CoinGecko API | coingecko.com/en/api | Free (30 calls/min), prices/volumes |
| CoinMarketCap | coinmarketcap.com/api | Free tier (10k credits/mo) |
| Binance API | binance-docs.github.io/apidocs | Free, real-time prices + websockets |
| FRED (Federal Reserve) | fred.stlouisfed.org/docs/api | Free, economic data (GDP, CPI, jobs) |
| DeFiLlama | defillama.com/docs/api | Free, DeFi TVL and protocol data |
| Yahoo Finance | finance.yahoo.com | Free API for stock/financial data |

### Weather Data
| Source | URL | Notes |
|--------|-----|-------|
| Open-Meteo | open-meteo.com | Free, no API key needed |
| NWS API (US) | api.weather.gov | Free, US weather forecasts |
| OpenWeatherMap | openweathermap.org/api | Free tier (60 calls/min) |

### Official Government Sources
| Source | URL | Notes |
|--------|-----|-------|
| SEC EDGAR | sec.gov/edgar | Corporate filings |
| BLS (Bureau of Labor Statistics) | bls.gov/developers | Jobs, CPI data |
| Federal Register API | federalregister.gov/developers | Regulatory actions |
| WHO Disease Outbreak News | who.int/emergencies | Global health events |

### Prediction Market Comparison
| Source | URL | Notes |
|--------|-----|-------|
| Polymarket Gamma API | gamma-api.polymarket.com | Market metadata, resolution sources |
| Kalshi API | trading-api.readme.io | Competitor prices for cross-platform analysis |
| Metaculus API | metaculus.com/api | Community forecasts (good calibration benchmark) |

---

## 4.5 Open-Source Polymarket Repos

| Repository | URL | Approach |
|---|---|---|
| **py-clob-client** | github.com/Polymarket/py-clob-client | Official Python SDK |
| **clob-client** | github.com/Polymarket/clob-client | Official TypeScript SDK |
| **Polymarket Examples** | github.com/Polymarket/examples | Example scripts for orders/data |
| **Autonolas Trader Agent** | github.com/valory-xyz/trader | Sophisticated multi-agent AI trading system |
| **clob-order-utils** | github.com/Polymarket/clob-order-utils | TypeScript order signing utilities |

### Relevant Academic Papers
- Wolfers & Zitzewitz (2004) — "Prediction Markets: Theory and Applications" (foundational)
- Snowberg & Wolfers (2010) — "The Favorite-Longshot Bias" (longshots are overpriced — tradable edge)
- Hanson, Oprea & Porter (2006) — "Manipulating Prediction Markets" (manipulation is self-correcting)
- Berg, Nelson & Rietz (2008) — "Prediction Market Accuracy in the Long Run"

---

## 5. Recommended Strategy

### Conservative Composite Approach
1. **Primary engine**: Edge detection using multi-source probability compilation
2. **Opportunistic**: News-reactive trading with strict confirmation requirements
3. **Steady income**: Convergence trading on near-resolution markets
4. **Risk management**: Quarter Kelly sizing, 3% max per trade, 10% drawdown circuit breaker

### Key Implementation Decisions
- **Start with high-liquidity markets only** (>$5,000 liquidity)
- **Use limit orders exclusively** to avoid taker fees
- **Require minimum 8% edge** before entering any position
- **Diversify across 5-10 uncorrelated markets**
- **Maintain 40% cash reserve** at all times
- **Paper trade for 14 days minimum** before any live trading

---

## 6. Identified Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API downtime | Can't trade or exit | Cancel open orders on detection, graceful degradation |
| Bad probability estimates | Losing trades | Multiple source confirmation, conservative edge threshold |
| Market resolution disputes | Funds locked | Diversify, limit per-market exposure to 3% |
| Liquidity crisis | Can't exit positions | Min liquidity filter, avoid illiquid markets |
| Regulatory changes | Platform shutdown | Keep majority of funds off-platform, monitor news |
| Smart contract risk | Loss of funds | Only deposit trading funds, not main holdings |
| Oracle manipulation | Wrong resolution | Diversify, monitor UMA disputes |
| Overfit strategies | Poor live performance | Paper trading validation, out-of-sample testing |
