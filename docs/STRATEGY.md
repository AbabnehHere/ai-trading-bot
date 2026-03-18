# Strategy Documentation

## Philosophy

This bot is a **conservative, patient trader** optimizing for long-term compound growth.

**Core principles:**
- High win rate (60-70%) over high returns
- Edge-based only — never trade without quantifiable edge
- Small position sizes — max 3% of bankroll per trade
- Diversification across uncorrelated markets
- Better to make zero trades than one bad trade

## Strategy 1: Edge Detection (Primary)

**Goal**: Find markets where our probability estimate differs significantly from the market price.

**Process**:
1. Compile external probability estimate from multiple sources
2. Compare to Polymarket price (which IS the market's implied probability)
3. Calculate edge = (our estimate - market price)
4. Only trade when edge > 8% AND confidence > 70% AND liquidity > $5,000

**Entry**: Buy YES if our probability > market price, buy NO if lower
**Exit**: Edge disappears, stop-loss hit, take-profit hit, or market resolves

## Strategy 2: News-Reactive (Secondary)

**Goal**: React to breaking news before the market fully adjusts.

**Process**:
1. Monitor RSS feeds continuously
2. When relevant news detected, analyze sentiment
3. Require at least 2 independent sources confirming
4. Only trade within 15 minutes of news breaking
5. Higher edge threshold (10%) for speed trades

**Key rule**: Accuracy over speed. Better late and right than fast and wrong.

## Strategy 3: Convergence (Tertiary)

**Goal**: Buy near-certain outcomes at a discount.

**Process**:
1. Find markets resolving within 14 days
2. Identify outcomes with >95% certainty
3. Buy if price offers >3 cent spread from $1.00
4. Hold to resolution

**Risk/Reward**: Very low risk, very consistent, small profit per trade.

## Position Sizing: Fractional Kelly

```
Full Kelly: f = (p * b - q) / b
Fractional: actual_size = f * 0.25  (quarter Kelly)
```

Quarter Kelly sacrifices some growth for much smoother returns.
Position always capped at 3% of total bankroll regardless of Kelly output.

## Configuration

All parameters are in `config/settings.yaml` under the `strategy:` section.
Risk limits are in `config/risk_limits.yaml`.
