---
name: Get Live Asset Prices
description: Fetch current prices for commodities, crypto, and financial assets
---

# Get Live Asset Prices

Use these endpoints with the WebFetch tool to get current prices:

## Crude Oil
```
URL: https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1d&range=1d
Prompt: What is the current crude oil price, today's high, and today's low?
```

## Gold
```
URL: https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=1d
Prompt: What is the current gold price?
```

## Natural Gas
```
URL: https://query1.finance.yahoo.com/v8/finance/chart/NG=F?interval=1d&range=1d
Prompt: What is the current natural gas price?
```

## Bitcoin
```
URL: https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
Prompt: What is the current bitcoin price?
```

## Ethereum
```
URL: https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd
Prompt: What is the current ethereum price?
```

## S&P 500
```
URL: https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d&range=1d
Prompt: What is the current S&P 500 level?
```

## Any Stock/ETF
```
URL: https://query1.finance.yahoo.com/v8/finance/chart/TICKER?interval=1d&range=1d
Replace TICKER with the symbol (e.g., AAPL, TSLA, SPY)
```

## Multiple Crypto at Once
```
URL: https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd
Prompt: List all crypto prices
```
