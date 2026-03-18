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
- **REST API Base**: `https://clob.polymarket.com`
- **Gamma API** (market data): `https://gamma-api.polymarket.com`
- **Authentication**: API key + HMAC signature using wallet private key
- **Key endpoints**:
  - `GET /markets` — List all markets
  - `GET /book` — Get orderbook for a token
  - `GET /midpoint` — Get midpoint price
  - `POST /order` — Place an order
  - `DELETE /order/{id}` — Cancel an order
  - `GET /orders` — Get open orders
  - `GET /positions` — Get current positions
- **Rate limits**: ~10 requests/second for REST, WebSocket for streaming

### Python SDK: `py-clob-client`
- Official Python SDK for the CLOB API
- Key class: `ClobClient` — handles auth, order signing, and API calls
- Order placement: `create_and_post_order(OrderArgs)`
- Supports order creation, cancellation, position queries
- Requires wallet private key for order signing

### Fee Structure
- **Maker fee**: 0% (fee-free for limit orders that add liquidity)
- **Taker fee**: ~1-2% (for orders that remove liquidity)
- **No deposit/withdrawal fees** on Polymarket itself (only Polygon gas ~$0.01)
- **Important**: Always use limit orders to avoid taker fees

### Resolution Mechanics
- Markets resolved by **UMA Optimistic Oracle**
- Resolution process: proposer asserts outcome → 2-hour challenge window → if undisputed, resolution is finalized
- **Edge cases**:
  - **Voided markets**: If a market can't be resolved, all shares refund at cost basis
  - **Disputed resolution**: Goes to UMA's DVM (Data Verification Mechanism) for a token holder vote
  - **Early resolution**: Markets can resolve before end date if outcome becomes certain
- **Risk**: Always account for resolution risk in position sizing

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

### Bot Activity on Polymarket
- Multiple sophisticated bots operate on Polymarket, particularly:
  - **Market makers** providing liquidity on major markets
  - **Arbitrage bots** keeping YES+NO prices near $1.00
  - **High-frequency news bots** reacting to events within seconds
- **Implication**: Pure speed-based strategies are difficult for a new bot

### Remaining Edges
- **Niche/low-liquidity markets**: Less bot competition, more mispricing
- **Multi-source analysis**: Most bots rely on single signals; combining multiple data sources creates an edge
- **Category expertise**: Deep knowledge in specific domains (politics, crypto) beats generic approaches
- **Patience**: Many bots are optimized for high frequency; our conservative approach avoids their competition

### Common Retail Trader Mistakes (Exploitable)
- Overreaction to news (mean reversion opportunity)
- Ignoring base rates and using recency bias
- Poor understanding of probability (buying YES at $0.85 thinking it's "safe" when it's actually poor risk/reward)
- Panic selling on negative news even when fundamentals haven't changed

---

## 4. Data Sources

### News & General Data
| Source | Type | Access | Update Frequency |
|--------|------|--------|------------------|
| Google News RSS | RSS | Free | Real-time |
| Reuters RSS | RSS | Free | Real-time |
| BBC RSS | RSS | Free | Real-time |
| AP News RSS | RSS | Free | Real-time |
| GDELT Project | API | Free | 15 minutes |
| NewsAPI.org | API | Free tier (100/day) | Real-time |

### Political Data
| Source | Type | Access |
|--------|------|--------|
| FiveThirtyEight | Polling aggregator | Free |
| RealClearPolitics | Polling aggregator | Free |
| 270toWin | Electoral maps | Free |
| PredictIt (comparison) | Prediction market | API |

### Sports Data
| Source | Type | Access |
|--------|------|--------|
| ESPN API | Scores/odds | Free |
| Odds API | Bookmaker odds | Free tier |
| Sports Reference | Historical stats | Free |

### Crypto/Financial Data
| Source | Type | Access |
|--------|------|--------|
| CoinGecko | Crypto prices | Free API |
| Yahoo Finance | Financial data | Free API |
| FRED | Economic data | Free API |

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
