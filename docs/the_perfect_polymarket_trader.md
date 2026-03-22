# The Perfect Polymarket Trader

A blueprint for building the optimal autonomous prediction market trading system, synthesized from research on the most profitable bots, academic papers, on-chain whale analysis, and hard-won lessons from live trading.

**Revised 2026-03-19** — Updated after critical review against empirical evidence. Major corrections to intelligence layer (single model beats ensemble), news pipeline (simplified), and risk management (stop-loss removed, Kelly adjusted).

---

## Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [Where the Money Actually Is](#where-the-money-actually-is)
3. [Architecture](#architecture)
4. [Intelligence Layer](#intelligence-layer)
5. [News & Information Pipeline](#news--information-pipeline)
6. [Strategy Portfolio](#strategy-portfolio)
7. [Risk Management](#risk-management)
8. [Execution Engine](#execution-engine)
9. [Learning & Adaptation](#learning--adaptation)
10. [Infrastructure](#infrastructure)
11. [Economics](#economics)

---

## Core Philosophy

The perfect Polymarket trader operates on three principles:

1. **Calibration is the edge.** Raw LLM outputs are overconfident. The difference between profitable and unprofitable AI traders is not which model they use or how many — it is whether their probability estimates are historically accurate. A well-calibrated single model beats an uncalibrated ensemble every time.

2. **Data quality beats model sophistication.** A simple moving average on clean, fast data outperforms a neural network trained on garbage. Primary sources (APIs, official filings, structured data) always beat secondary sources (headlines, social media, commentary). The bottleneck is interpretation, not ingestion.

3. **Survive first, profit second.** 14 of the top 20 most profitable Polymarket wallets are bots. The ones that lasted long enough to reach the top 20 did so because they never blew up. But "survive" means smart risk management — not mechanical stop-losses that lock in losses on binary contracts.

---

## Where the Money Actually Is

Before designing a system, understand where Polymarket profits actually come from. The $40M in documented bot profits (April 2024 - April 2025) breaks down:

| Strategy | Share of Profits | AI Required? | Capital Required |
|----------|-----------------|-------------|-----------------|
| Latency arbitrage (exchange price lag) | ~50% | No | High + co-location |
| Cross-platform arbitrage (Polymarket vs Kalshi) | ~23% | No | Medium |
| YES+NO arbitrage (sum < $1.00) | ~5% | No | Low |
| High-probability bonds (buy >$0.95) | ~5% | No | Low |
| AI-driven directional betting | ~10% | Yes | Low |
| Market making | ~7% | No | Medium |

**The uncomfortable truth:** 73% of arbitrage profits go to sub-100ms execution bots. The average arbitrage opportunity now lasts 2.7 seconds (down from 12.3s in 2024). Unless you have co-located infrastructure, pure arbitrage is not accessible.

**Where our bot fits:** AI-driven directional betting and edge detection. This is a smaller slice of total profits but has lower infrastructure requirements and is less crowded. The edge comes from **interpreting information better than the market**, not from being faster.

**What the top whales teach us:** On-chain analysis of 27,000 trades from the top 10 wallets reveals:
- SeriouslySirius ($3.29M/month): 53.3% win rate, 2.52x profit-loss ratio
- DrPufferfish: 50.9% win rate, 8.62x profit-loss ratio
- Over 90% of large orders (>$10K) are at prices above $0.95 — they are buying near-certain outcomes

**The lesson:** Win rate barely matters. What separates winners from losers is **how much they make when right vs. how much they lose when wrong** (profit-loss ratio). The perfect trader lets winners run and cuts losers through judgment, not mechanical rules.

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │       INTELLIGENCE LAYER         │
                    │                                  │
                    │  Single Strong Model             │
                    │  (Claude Opus or GPT-4.5)        │
                    │              ↓                    │
                    │     Calibration Pipeline          │
                    │     (Platt scaling, evidence      │
                    │      penalties, historical fit)   │
                    └──────────────┬────────────────────┘
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                              │                              │
    ▼                              ▼                              ▼
┌─────────────┐             ┌─────────────┐              ┌──────────────┐
│    NEWS &   │             │  STRATEGY   │              │   MARKET     │
│    DATA     │────────────→│  ENGINE     │←─────────────│   DATA       │
│             │             │             │              │              │
│ Google RSS  │             │ Edge Finder │              │ Polymarket   │
│ Gov Feeds   │             │ News React  │              │ Kalshi       │
│ Tavily (bk) │             │ Convergence │              │ Exchange WS  │
│ Yahoo/CGko  │             │ Arb Scanner │              │ Whale Feeds  │
│ Sonar (ntly)│             │ Whale Follow│              │              │
└─────────────┘             └──────┬──────┘              └──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       RISK MANAGER           │
                    │                              │
                    │  9 pre-trade gates            │
                    │  Info-based exit triggers     │
                    │  Graduated drawdown sizing    │
                    │  Profit-loss ratio tracking   │
                    │  Correlation limits           │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     EXECUTION ENGINE          │
                    │                              │
                    │  Limit orders (0% maker fee)  │
                    │  Sub-minute for directional   │
                    │  Smart order routing          │
                    │  Position manager             │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     LEARNING SYSTEM           │
                    │                              │
                    │  Brier score tracking         │
                    │  Profit-loss ratio analysis   │
                    │  Calibration retraining       │
                    │  Strategy tuner               │
                    │  Nightly deep review          │
                    └──────────────────────────────┘
```

---

## Intelligence Layer

### Single Strong Model (Not an Ensemble)

The initial version of this document recommended a multi-LLM ensemble (Claude 35% + GPT-4o 40% + Gemini 25%). **The evidence says this is wrong.**

**"Wisdom of the Silicon Crowd" (Science Advances)** tested 12 LLMs against 925 human forecasters:

| System | Brier Score |
|--------|------------|
| GPT-4 alone | **0.15** |
| 12-model ensemble (median) | **0.20** (worse) |
| Human crowd (925 people) | **0.19** |

The ensemble was **worse** than the best single model. Why? LLM errors are strongly correlated — they share training data, RLHF methodology, and similar architectures. A paper ("Don't Always Pick the Highest-Performing Model," Turkmen et al. 2026) formally proves there is an information-theoretic saturation floor: beyond a certain point, adding more models cannot reduce error because the shared difficulty component dominates.

**ForecastBench** (the most rigorous ongoing benchmark): GPT-4.5 alone achieves Brier 0.101. No ensemble beats it. Superforecasters achieve 0.081. Linear extrapolation suggests LLMs match superforecasters around November 2026.

**The "Fully-Autonomous-Polymarket-AI-Trading-Bot"** that popularized the ensemble approach has **zero reported P&L** — no backtests, no live results, no win rates. It is a framework, not a proven system.

**What to use instead:**
- **Primary:** Claude Opus or GPT-4.5 — whichever scores best on ForecastBench at time of deployment
- **Via CLI when possible:** Claude Code CLI (`claude -p`) is free and sufficient for most analysis
- **Via API when needed:** For time-sensitive signals where CLI latency (~5-10s) is too slow
- **Never anchor to market price.** The model must estimate probability independently, then compare to market price to find edge

**When an ensemble DOES make sense:** If you have 30+ resolved markets with per-model Brier scores, AND one model consistently dominates certain categories while another dominates others, THEN a category-weighted ensemble can help. But start with one model and prove the edge first.

### Calibration Pipeline

This is the part of the original document that holds up. Raw LLM probability estimates are systematically overconfident. Calibration is empirically proven to help.

**"Calibrating Verbalized Probabilities for LLMs" (2024)** results:

| Model | Before Calibration (ECE) | After Calibration (ECE) |
|-------|-------------------------|------------------------|
| Claude-v3 | 5.2% | 1.0% |
| Mixtral 8x7B | 16.9% | 4.9% |
| Claude-v2 | 7.1% | 3.3% |

The calibration pipeline:

1. **Platt Scaling** — Logistic compression pulling extreme probabilities (>90% or <10%) toward 50%. Trained on historical resolved markets. Single most impactful correction.
2. **Evidence Quality Penalty** — If supporting evidence is thin (few sources, low domain authority, no primary sources), pull estimate toward 50%. Score: primary sources (1.0), major outlets (0.8), secondary (0.6), unknown (0.3). Minimum evidence quality threshold: 0.55.
3. **Contradiction Penalty** — If evidence contains strong arguments on both sides, reduce confidence proportionally to the strength of the opposing case.
4. **Historical Calibration** — Logistic regression mapping raw estimates to actual outcomes, retrained after every 30 resolved markets.

**Key requirement:** You need 30+ resolved markets to train calibration parameters. Before that, use conservative position sizing to compensate for uncalibrated estimates.

---

## News & Information Pipeline

### What Changed from v1

The original document proposed a 3-tier paid pipeline (Tavily → Grok X Search → Perplexity Sonar) costing ~$200/month. The evidence shows this is over-engineered:

- A developer built a profitable news bot using **free Google News RSS + GPT-4o mini**
- The bottleneck is **interpretation speed**, not data ingestion speed
- Tavily has real reliability issues (dead 404 links, silent empty results, rate limiting)
- No evidence that Grok X Search predicts prediction market moves specifically
- The actual profitable Polymarket bots don't use paid news APIs — they use price feeds

### The Revised Pipeline

#### Layer 1: Structured Data Feeds (continuous, free)

**Purpose:** Ground truth for price-based markets. This is the highest-value data source.

- **Yahoo Finance API** — Commodity prices (crude oil CL=F, gold GC=F, natural gas NG=F), stock prices, ETFs
- **CoinGecko API** — Crypto prices (BTC, ETH, SOL)
- **Exchange websockets** (Binance, Coinbase) — Real-time crypto prices for crypto-linked prediction markets. This is what the $438K bot used.
- **Official data feeds** — Fed funds rate, CPI releases, unemployment data from government sources

**Rule: API prices always override news headlines.** A headline saying "Oil hits $110" could mean a forecast, a target, or a historical reference. The API returns the actual current price.

#### Layer 2: Free News Scanning (every 60-120 seconds)

**Tool:** Google News RSS
**Cost:** Free
**Purpose:** Headline monitoring across all active markets

- Topic-specific Google News RSS: `https://news.google.com/rss/search?q=TOPIC`
- Reuters, AP News, BBC general feeds
- Filter by recency (last 2 hours only for trading, last 24h for context)
- Rate limit: scan max 8 markets per cycle to keep cycle time <60 seconds

**Why free RSS is sufficient:** The edge is not in getting the headline 50ms faster. It's in correctly interpreting what the headline means for probability before the market fully reprices (a 1-5 minute window). A $0/month RSS feed + good LLM interpretation beats a $23/month Tavily subscription + mediocre interpretation.

#### Layer 3: Authoritative Source Monitoring (continuous, free)

**Purpose:** Primary sources that move markets. This is the highest-alpha data source for political and economic markets.

- **Government feeds:** bls.gov (jobs, CPI), sec.gov (filings), fec.gov (election data), supremecourt.gov (rulings)
- **Central bank announcements:** Fed, ECB, BOJ — scheduled releases and emergency statements
- **Court dockets:** PACER for legal markets (indictments, rulings)
- **Official social accounts:** @POTUS, @SecDef, agency accounts for policy announcements

**Why this matters:** When the BLS releases a jobs report, there's a 1-5 minute window before prediction markets fully reprice economic markets. Government data is the highest-authority source possible — no domain scoring needed.

#### Layer 4: Paid Research (nightly + high-conviction, ~$15/month)

**Tool:** Perplexity Sonar
**When:** Nightly deep review of open positions + pre-trade analysis when edge >10%
**Purpose:** Cited, multi-source analysis that explicitly seeks disconfirming evidence

- ~50 requests/day max (10 open positions reviewed + a few pre-trade deep dives)
- Domain-restricted searches to authoritative sources
- Contrarian queries: after finding supporting evidence, explicitly ask "what evidence suggests this WON'T happen?"
- Used only for long-dated markets where speed doesn't matter but depth does

#### Optional: Social Sentiment (event-driven)

**Tool:** Grok API with X Search
**When:** Only for markets where Twitter/X is a primary signal source (crypto narratives, political drama, Musk-related markets)
**Cost:** Pay-per-use, budget cap $20/month

This is optional because the evidence for X/Twitter sentiment predicting Polymarket moves specifically is thin. It may help for crypto-adjacent markets but is unproven for political/economic markets. Start without it and add only if you identify a clear edge.

### Information Quality Rules

1. **Never trade on a single source.** Minimum 2 independent sources confirming the same signal.
2. **Read summaries, not just headlines.** "Oil $110" is ambiguous. The summary tells you if it's a forecast, current price, or historical reference.
3. **Domain authority matters.** Government data > wire services (Reuters, AP) > major outlets > blogs > social media.
4. **Freshness decays fast.** News older than 2 hours is priced in. The edge is in the first 5 minutes.
5. **Seek disconfirmation.** After finding evidence supporting a trade, explicitly search for evidence against it. Confirmation bias is the silent killer of trading systems.
6. **Trust structured data over unstructured text.** An API returning `{"price": 72.45}` is infinitely more reliable than a headline containing "$72."

---

## Strategy Portfolio

The perfect trader runs multiple uncorrelated strategies simultaneously. Strategies are ordered by evidence quality, not theoretical return.

### 1. YES+NO Arbitrage (Proven, Mechanical)

**Edge source:** When YES + NO prices on the same market sum to less than $1.00.
**Expected return:** Risk-free profit equal to the discount.
**Requirements:** Fast detection, immediate execution on both sides.
**Evidence quality:** Mathematical guarantee.

- Scan all active markets for YES + NO < $0.98 (after 2% taker fees)
- Buy both sides simultaneously
- Guaranteed profit at resolution regardless of outcome
- Increasingly rare as more bots compete, but still appears during volatility spikes

### 2. High-Probability Bonds (Proven, Low-Risk)

**Edge source:** Markets where outcome is >95% certain but price hasn't converged to $1.00.
**Expected return:** 2-5% in 1-14 days. Annualized 25-50% with compounding.
**Requirements:** Accurate resolution assessment, patience, limit orders.
**Evidence quality:** High — over 90% of large whale orders are at prices >$0.95.

- Identify markets within 14 days of resolution where outcome is >95% certain
- Buy at $0.93-0.97 using limit orders (0% maker fee)
- Collect $1.00 at resolution
- **Fee warning:** At 2% taker fee, buying at $0.97 yields only $0.01 profit. MUST use limit orders or target prices ≤ $0.95

### 3. Edge Detection / Mispricing (Our Primary Strategy)

**Edge source:** Markets where the crowd is systematically wrong due to cognitive biases, lack of information, or narrative-driven pricing.
**Expected return:** 5-15% per trade, holding period days to weeks.
**Requirements:** Independent probability estimation, strong calibration, information quality.
**Evidence quality:** Moderate — backtested at 50-60% win rate with proper calibration.

- Compile probability estimate from model + primary sources (never anchoring to market price)
- Apply calibration pipeline (Platt scaling, evidence penalties)
- Trade when calibrated edge > 8% after fees with evidence quality > 0.55
- Common bias patterns to exploit:
  - **Recency bias** — Markets overweight recent events (one bad poll moves a political market too far)
  - **Narrative bias** — Markets price stories, not probabilities ("AI will change everything" → overpriced)
  - **Neglect of base rates** — Markets ignore historical frequencies ("will X happen this month?" when base rate is 2%)
  - **Availability bias** — Dramatic events seem more likely than they are (plane crashes, wars, pandemics)

### 4. News-Reactive Trading (High-Skill, Time-Sensitive)

**Edge source:** The 30-second to 5-minute window between breaking news and market price adjustment.
**Expected return:** 5-20% per successful trade.
**Requirements:** Fast news pipeline, rapid probability estimation, pre-positioned limit orders.
**Evidence quality:** Moderate — documented cases of 13-cent captures on breaking news, but requires speed.

- News scanner detects market-moving headline from authoritative source
- Model rapidly estimates new probability (target: <30 seconds from headline to signal)
- If estimated probability diverges >10% from current market price, signal generated
- Place limit order at edge midpoint (halfway between current price and estimated fair value)
- **This is where calibration pays for itself** — an overconfident estimate on a fast-moving market is a quick loss

### 5. Cross-Platform Arbitrage (Proven, Infrastructure-Heavy)

**Edge source:** Price differences between Polymarket and Kalshi on identical markets.
**Expected return:** 1-5% per opportunity.
**Requirements:** Accounts on both platforms, sub-second execution, real-time price feeds.
**Evidence quality:** High — $40M extracted in one year. But edge is compressing (2.7s average opportunity duration).

- Monitor identical markets on both platforms
- When price difference exceeds fee threshold (~4% round-trip), buy cheap side and sell expensive side
- Pure mechanical edge — no prediction required
- **Warning:** Requires co-located infrastructure to compete with sub-100ms bots. Only pursue if you can invest in proper infrastructure.

### 6. Whale Following (Emerging, Signal-Based)

**Edge source:** Smart money signals from the most profitable wallets on Polymarket.
**Expected return:** Variable, depends on whale accuracy.
**Requirements:** Wallet tracking infrastructure, on-chain monitoring.
**Evidence quality:** Moderate — whales demonstrably outperform, but following them has latency and selection bias.

- Auto-discover top 50 wallets by historical profit on Polygonscan
- Monitor for large new positions (>$10K)
- Generate conviction score when 3+ top wallets converge on the same position
- Trade in the same direction with smaller size
- **Key insight:** When multiple independently profitable wallets reach the same conclusion, the information signal is strong

### 7. Market Making (Advanced, Capital-Intensive)

**Edge source:** Providing liquidity and earning the bid-ask spread.
**Expected return:** 1-3% monthly, 78-85% win rate.
**Requirements:** Continuous quoting, inventory management, adverse selection awareness.
**Evidence quality:** Proven in traditional markets, harder in prediction markets.

- Post limit orders on both sides of a market
- Earn spread when orders fill
- Manage inventory risk (avoid accumulating large directional positions)
- Withdraw quotes before known events (scheduled announcements, elections)
- **Warning:** Prediction markets are binary and information is lumpy. Market making here is harder than in equities or crypto spot.

---

## Risk Management

### What Changed from v1

The original document proposed 15 gates including a 30% stop-loss and quarter Kelly. On-chain evidence from top Polymarket wallets revealed:

1. **Mechanical stop-losses are counterproductive on binary contracts.** If you buy YES at $0.60 and it drops to $0.42 (triggering -30% stop-loss), you sell a contract that might still resolve to $1.00. Stop-losses in prediction markets systematically convert temporary paper losses into permanent real losses.

2. **Quarter Kelly is too conservative.** It captures only 44% of optimal growth. Academic research shows half Kelly (0.50) is the practitioner sweet spot, and even with 20% estimation uncertainty, the optimal fraction only drops from 0.40 to 0.36 — not to 0.25.

3. **Win rate doesn't matter. Profit-loss ratio does.** The top whale (SeriouslySirius) has a 53.3% win rate — barely above a coin flip. What makes them profitable is a 2.52x profit-loss ratio.

### Pre-Trade Gates (all must pass)

| # | Check | Threshold | Rationale |
|---|-------|-----------|-----------|
| 1 | Circuit breaker | Not activated | Hard stop, graduated (see below) |
| 2 | Bankroll minimum | ≥ $50 remaining | Never trade with money you can't lose |
| 3 | Daily loss limit | < 5% daily loss | Stop digging when in a hole |
| 4 | Daily trade count | < 20 trades/day | Prevent overtrading and churn |
| 5 | Post-loss cooldown | 5 min after loss | Brief pause, not a punishment |
| 6 | Position size | ≤ 5% of portfolio | Room for meaningful bets on small bankrolls |
| 7 | Concurrent positions | ≤ 10 open | Maintain focus and manageability |
| 8 | Trade size bounds | $5 - $100 | Floor prevents dust, ceiling prevents concentration |
| 9 | Edge after fees | > 5% net edge | 2% entry + 2% exit = 4% cost minimum |
| 10 | Evidence quality | ≥ 0.55 score | Don't trade on thin information |
| 11 | Correlation check | < 3 correlated positions | Don't bet the same thesis 5 ways |
| 12 | Liquidity check | > $5K market liquidity | Can't exit illiquid positions when wrong |
| 13 | Time to resolution | > 24 hours | Avoid last-minute volatility traps |

### Position Sizing: Kelly Criterion

```
kelly_fraction = (p * b - q) / b

where:
  p = calibrated probability of winning
  b = payout odds (1/price - 1 for prediction markets)
  q = 1 - p
```

**Use 40% Kelly** (multiply result by 0.40). This captures ~60% of optimal growth with substantial variance reduction. Academic research (Matthew Downey simulations) shows that even with significant probability estimation uncertainty (SD of 20%), the optimal practical fraction is 0.36-0.40, not 0.25.

**Graduated drawdown sizing** (replaces binary circuit breaker):
- 0-5% drawdown: Full 40%-Kelly sizing
- 5-10% drawdown: Half sizing (20%-Kelly)
- 10-15% drawdown: Quarter sizing (10%-Kelly)
- 15%+ drawdown: Stop trading, full review of all strategies and assumptions

This keeps you in the game during normal variance instead of shutting down entirely at 10%.

### Exit Rules: Information-Based, Not Mechanical

**The critical change:** No mechanical stop-loss. Prediction market contracts resolve to $0 or $1. Interim price drops reflect probability updates, not random walks. Selling because of a price drop means selling low on a contract that may still pay $1.00.

| Trigger | Action |
|---------|--------|
| **Thesis invalidated** (new information contradicts original analysis) | Close immediately regardless of P&L |
| **Position re-evaluation** (price drops >30% from entry) | Re-analyze market with fresh data. If original thesis still holds, HOLD or ADD. If thesis weakened, reduce or close. |
| Take-profit at +50% | Close 50% of position, let remainder ride to resolution |
| Max hold time 30 days | Re-evaluate. Close if no resolution in sight, hold if resolution imminent |
| Resolution imminent (<6h) | Final review: hold to resolution or exit based on current probability |

**Why this is better:** Instead of mechanically selling at -30% (which locks in losses), the system asks "has the underlying probability actually changed?" If YES dropped from $0.60 to $0.42 because of new information suggesting the event is less likely, selling is correct. If it dropped because of noise or a temporary liquidity crunch, selling is wrong. The LLM can distinguish between these cases; a mechanical rule cannot.

### Portfolio-Level Controls

- **Maximum portfolio heat:** ≤ 30% of bankroll in open positions during paper trading. Scale to 50% once live with proven edge over 30+ trades.
- **Cash reserve:** Maintain ≥ 50% cash. Dry powder for high-conviction opportunities.
- **Correlation limit:** No more than 3 positions correlated to the same underlying thesis.
- **Profit-loss ratio target:** Track this metric religiously. Target ≥ 2.0x (make 2x on winners what you lose on losers). If ratio drops below 1.5x over 20+ trades, review strategy.
- **Daily review:** If daily P&L exceeds ±5%, pause and review before continuing.

### Bankroll-Adjusted Parameters

Risk parameters should scale with bankroll size:

| Bankroll | Max Position % | Concurrent Positions | Kelly Fraction |
|----------|---------------|---------------------|---------------|
| $1,000 | 8% ($80) | 3-5 concentrated | 0.40 |
| $3,000 | 5% ($150) | 5-8 | 0.40 |
| $5,000 | 5% ($250) | 8-10 | 0.40 |
| $10,000+ | 3% ($300+) | 10-12 | 0.40 |

Smaller bankrolls need larger position percentages to deploy meaningful capital, offset by fewer concurrent positions to manage risk.

---

## Execution Engine

### Order Types

- **Always use limit orders** when possible. Maker fee is 0% vs 2% taker fee. This alone doubles your effective edge on many trades.
- Place limit orders slightly inside the spread. If you want to buy YES at $0.55 and the best ask is $0.56, place a limit buy at $0.55.
- Use IOC (immediate-or-cancel) orders only when speed is critical (arbitrage, breaking news reaction where the edge exceeds the 2% taker fee).

### Execution Speed Targets

| Strategy | Target Latency | Rationale |
|----------|---------------|-----------|
| YES+NO arbitrage | < 1 second | Must fill both sides before price moves |
| Cross-platform arbitrage | < 500ms | Opportunities last 2.7 seconds average |
| News-reactive | < 60 seconds | Profit window is 30s to 5 minutes |
| Edge detection | < 5 minutes | Slow-moving mispricing, no rush |
| High-probability bonds | < 1 hour | Prices converge over days |

### Smart Order Routing

- Check order book depth before placing. If your order would move the market >1%, split into smaller orders.
- Monitor fill rates. If limit orders fill < 30% of the time, pricing is too aggressive.
- Track slippage per strategy. If average slippage exceeds 1%, adjust order placement logic.

---

## Learning & Adaptation

### Brier Score Tracking

The Brier score is the gold standard for measuring prediction accuracy:

```
brier_score = (predicted_probability - actual_outcome)^2
```

Lower is better. Perfect predictions score 0. Random guessing scores 0.25. ForecastBench superforecasters achieve 0.081. GPT-4.5 achieves 0.101.

Track Brier scores:
- Per strategy (for allocation decisions)
- Per market category (geopolitics, crypto, economics)
- Over time (trend detection — are we getting better or worse?)
- Before and after calibration (to validate the pipeline is helping)

### Profit-Loss Ratio Tracking

More important than win rate. Calculate after every trade:

```
profit_loss_ratio = average_win_amount / average_loss_amount
```

| Ratio | Assessment |
|-------|-----------|
| < 1.0 | Losing money even with >50% win rate. Fix immediately. |
| 1.0 - 1.5 | Marginal. Need >45% win rate to profit after fees. |
| 1.5 - 2.5 | Good. This is where the top whales operate. |
| > 2.5 | Excellent. Either very skilled or not trading enough. |

### Calibration Retraining

Every 30 resolved markets:
1. Recalculate Brier score (overall and by category)
2. Retrain Platt scaling parameters on expanded dataset
3. Evaluate whether evidence quality thresholds should change
4. Log all parameter changes to strategy history

### Nightly Deep Review

At midnight UTC every day:
1. Full performance analysis (win rate, Sharpe, drawdown, profit-loss ratio)
2. Review every trade from the past 24 hours
3. For each open position: use Perplexity Sonar for deep research — has the thesis changed?
4. Categorize wins and losses by strategy and market type
5. Identify patterns (e.g., "we're consistently wrong on crypto markets")
6. Suggest parameter adjustments (raise edge thresholds, disable underperforming strategies)
7. Write findings to nightly review log

### Lessons Database

Every resolved trade generates a lesson:
- What was the thesis?
- Was it correct?
- What information was available that we missed?
- What information did we overweight?
- Would better calibration have caught the error?
- What was the profit-loss ratio on this trade?

Lessons are categorized and searchable. Before entering any new trade, the system checks for relevant lessons from similar past trades.

---

## Infrastructure

### Server Requirements

- **VPS co-located in US-East** (close to Polymarket's infrastructure) — only needed for arbitrage strategies
- For directional betting only: any reliable server with good uptime works
- Minimum: 2 vCPU, 4GB RAM, SSD storage (directional) or 4 vCPU, 8GB RAM (arbitrage)
- Uptime target: 99.9% (prediction markets never close)

### Data Storage

- **SQLite** for trade history, positions, performance snapshots, Brier scores, calibration data
- **JSON files** for inter-process communication (market scans, signals)
- **Log files** for audit trail and debugging
- **Daily backups** of database and configuration

### Monitoring & Alerting

- Bot health check every 60 seconds
- Alert on: bot crash, unusual P&L (>±5% daily), failed API calls, risk limit breaches
- Dashboard showing: open positions, daily P&L, profit-loss ratio, Brier score, strategy performance
- Dead man's switch: if bot hasn't produced a heartbeat in 5 minutes, send alert

### Security

- API keys and private keys in `.env` file, never in code or git
- Separate API keys for each service
- Wallet private key with minimal permissions (trade only, no withdrawals if possible)
- Rate limiting on all external API calls to avoid bans

---

## Economics

### Fee Structure

| Action | Fee |
|--------|-----|
| Limit order (maker) | 0% |
| Market order (taker) | 2% |
| Round-trip (limit entry + taker exit) | 2% |
| Round-trip (taker both sides) | 4% |

**Implication:** A trade with 5% raw edge yields 3% net with limit orders but only 1% net with market orders. Always prefer limit orders.

### Cost of Intelligence (Revised)

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| Claude Code CLI (primary analysis) | Unlimited | $0 (included in subscription) |
| Google News RSS (news scanning) | Unlimited | $0 |
| Yahoo Finance + CoinGecko (price data) | Unlimited | $0 |
| Perplexity Sonar (nightly deep review) | ~50 req/day | ~$15 |
| Tavily (backup search, optional) | ~500 req/day | ~$4 |
| Grok X Search (optional, crypto sentiment) | ~100 req/day | ~$8 |
| **Total (core)** | | **~$15/month** |
| **Total (with optional add-ons)** | | **~$27/month** |

vs. original recommendation of ~$200/month. **87% cost reduction** with no evidence of reduced performance.

### Break-Even Analysis

With $15/month in costs and a $1,000 starting bankroll:
- Need 1.5% monthly return to cover costs
- With $3,000 bankroll: need 0.5% monthly return
- With $5,000 bankroll: need 0.3% monthly return

This is dramatically more achievable than the original $200/month requiring 20% returns on a $1K bankroll.

### Expected Returns (Honest)

| Strategy | Monthly Return | Win Rate | Evidence Level |
|----------|---------------|----------|---------------|
| YES+NO arbitrage | 1-3% | 100% | Mathematical guarantee |
| High-probability bonds | 2-5% | 90%+ | On-chain whale data |
| Edge detection | 2-8% | 50-60% | Backtested, limited live |
| News-reactive | 3-10% | 55-65% | Documented cases, unaudited |
| Cross-platform arbitrage | 2-5% | 90%+ | $40M documented, requires infra |
| Market making | 1-3% | 78-85% | Proven in theory, hard in practice |

**Important caveats:**
- These are returns from the **best** bots. Median bot performance is **negative** after fees.
- No open-source LLM-based Polymarket bot has published verified live P&L.
- The $40M in documented profits came overwhelmingly from arbitrage, not AI directional betting.
- Start with paper trading. Graduate to small live positions only after demonstrating edge over 30+ trades.

---

## Summary: What Separates Winners from Losers

1. **Profit-loss ratio over win rate.** The top whale wins 53% of trades but makes 2.5x on winners vs. losers. Stop chasing high win rates. Focus on making more when right and losing less when wrong.

2. **Calibration discipline.** Raw LLM outputs are overconfident. Platt scaling + evidence quality penalties is empirically proven to reduce calibration error by 4-12 percentage points. This is the single biggest differentiator for AI-driven directional betting.

3. **No mechanical stop-losses on binary contracts.** When a position drops, re-analyze with fresh data. If the thesis still holds, the drop is a buying opportunity, not an exit signal.

4. **Simple beats complex.** One strong model beats a multi-model ensemble (Brier 0.15 vs 0.20). Free RSS beats paid news APIs. Quarter Kelly is too conservative; 40% Kelly is closer to optimal. Don't over-engineer.

5. **Fee awareness.** A 2% edge that costs 4% in fees is a losing trade. Always use limit orders (0% maker fee). Always account for round-trip costs before entering.

6. **Survive first.** Graduated drawdown sizing, correlation limits, and daily loss limits keep you in the game. But don't confuse "survive" with "never take risk." A $30 position on a $1,000 bankroll is too timid. Size meaningfully on high-conviction trades.

7. **Emotional absence.** The bot doesn't feel FOMO. It doesn't revenge trade. It doesn't double down on a losing thesis because of ego. It follows the math. This is its greatest advantage over human traders.

---

## Appendix: Key Sources

- "Wisdom of the Silicon Crowd" — Science Advances, Schoenegger et al. (LLM ensemble vs single model)
- "Approaching Human-Level Forecasting with Language Models" — Halawi et al., NeurIPS 2024
- "Don't Always Pick the Highest-Performing Model" — Turkmen et al. 2026 (correlated LLM errors)
- "Calibrating Verbalized Probabilities for LLMs" — 2024 (Platt scaling results)
- ForecastBench Leaderboard — forecastbench.org (ongoing LLM forecasting benchmark)
- Polymarket On-Chain Analysis — ChainCatcher, 95M transactions analyzed
- Top 10 Polymarket Whales — Gate.io Research, 27,000 trades analyzed
- Application of Kelly Criterion to Prediction Markets — arXiv 2412.14144
- Good and Bad Properties of the Kelly Criterion — UC Berkeley
- "Contra Papers Claiming Superhuman AI Forecasting" — LessWrong (methodological critique)

---

*This document is a living blueprint. Last revised 2026-03-19 after critical review against empirical evidence. Update as new data emerges and lessons are learned from live trading.*
