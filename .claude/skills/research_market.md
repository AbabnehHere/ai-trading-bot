---
name: Research a Polymarket Market
description: Deep research on a specific market to assess probability
---

# Research a Polymarket Market

When you need to deeply assess a specific Polymarket market, follow this process:

## Step 1: Get the market details
Read `data/reports/market_scan.json` and find the market by ID or question.

## Step 2: Fetch relevant news
Use the get_news skill with topic-specific search:
```
WebFetch URL: https://news.google.com/rss/search?q=RELEVANT+KEYWORDS
```

## Step 3: Fetch relevant prices (if applicable)
Use the get_prices skill for any asset-price markets.

## Step 4: Check Polymarket page for full description
```
WebFetch URL: https://polymarket.com/event/SLUG
Prompt: What is the full resolution criteria for this market? How is it resolved?
```

## Step 5: Check Wikipedia or reference sources
For political/geopolitical markets:
```
WebFetch URL: https://en.wikipedia.org/wiki/TOPIC
Prompt: What is the current status of TOPIC? Any recent developments?
```

## Step 6: Cross-reference with other prediction platforms
```
WebFetch URL: https://www.metaculus.com/questions/?search=KEYWORDS
Prompt: What is the community prediction for questions related to KEYWORDS?
```

## Step 7: Estimate probability
Based on all gathered evidence:
1. What is the base rate for this type of event?
2. What does the news suggest about direction?
3. What do other forecasters think?
4. What is your overall estimate?

## Step 8: Calculate edge
- Raw edge = your estimate - market price
- Entry cost = market price × 1.02 (2% taker fee)
- Expected payout = your probability × $1.00
- Edge after fees = expected payout - entry cost
- Only trade if edge after fees > $0.05 AND confidence is high
