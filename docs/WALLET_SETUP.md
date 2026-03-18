# Wallet Setup Guide

## Overview

Polymarket operates on the **Polygon blockchain** and uses **USDC** as its trading currency. If you currently hold SOL in a Phantom wallet, you'll need to convert and bridge funds before trading.

---

## Step 1: Convert SOL to USDC

### Option A: Swap Within Phantom (Simplest)
1. Open Phantom wallet
2. Select your SOL balance
3. Tap **Swap**
4. Select **USDC (Solana)** as the output token
5. Enter the amount of SOL to swap
6. Review the rate and confirm

**Estimated fees**: ~0.1-0.5% swap fee + negligible SOL gas (~$0.01)
**Time**: Instant

### Option B: Via Centralized Exchange
1. Send SOL from Phantom to Coinbase/Kraken/Binance
2. Sell SOL for USD/USDC on the exchange
3. Proceed to Step 2 using the exchange withdrawal

**Estimated fees**: Network fee (~$0.01) + exchange trading fee (0.1-0.5%)
**Time**: 1-5 minutes for SOL transfer + instant trade

---

## Step 2: Bridge USDC to Polygon

### Option A: Via Centralized Exchange (Recommended — Cheapest & Simplest)
1. If your USDC is on an exchange (Coinbase, Kraken, Binance):
   - Go to **Withdraw USDC**
   - Select **Polygon** as the withdrawal network
   - Enter your Polygon wallet address (MetaMask or Polymarket deposit address)
   - Confirm withdrawal

**Estimated fees**: $0.10 - $1.00 (varies by exchange)
**Time**: 5-15 minutes

### Option B: Cross-Chain Bridge (If USDC is in Phantom)
1. Use a bridge service:
   - **Portal (Wormhole)**: portal.wormhole.com
   - **Allbridge**: allbridge.io
   - **Jumper Exchange**: jumper.exchange
2. Connect Phantom wallet (source: Solana)
3. Connect MetaMask or destination wallet (destination: Polygon)
4. Bridge USDC from Solana → Polygon
5. Wait for confirmation

**Estimated fees**: $1-5 bridge fee + gas
**Time**: 5-20 minutes

### Recommended Path (Fastest & Cheapest)
**Phantom → Send SOL to Coinbase → Sell SOL → Withdraw USDC on Polygon → Deposit to Polymarket**

Total estimated cost: ~$1-2 in fees
Total estimated time: ~15-30 minutes

---

## Step 3: Set Up Polymarket Account

1. Go to [polymarket.com](https://polymarket.com)
2. Sign up / connect wallet:
   - **Email signup**: Polymarket creates a proxy wallet for you
   - **MetaMask**: Connect your MetaMask wallet (must be on Polygon network)
3. Polymarket also supports **direct deposits from Coinbase** — this may be the simplest option

---

## Step 4: Deposit USDC into Polymarket

1. On Polymarket, click **Deposit**
2. Follow the deposit instructions:
   - If using Coinbase: Use the direct Coinbase integration
   - If using MetaMask: Approve and transfer USDC to Polymarket's contract
3. Wait for the deposit to confirm (usually 1-2 minutes on Polygon)

---

## Step 5: Obtain API Credentials

1. Log in to your Polymarket account
2. Navigate to account settings or developer section
3. Generate an **API key**
4. You will need:
   - `POLYMARKET_API_KEY` — Your API key
   - `POLYMARKET_SECRET` — Your API secret
   - `POLYMARKET_PASSPHRASE` — Your API passphrase
   - `PRIVATE_KEY` — Your Polygon wallet private key (for signing orders)
   - `WALLET_ADDRESS` — Your Polygon wallet address

### Storing Credentials Securely
```bash
# Copy the example env file
cp .env.example .env

# Edit with your actual credentials
# NEVER commit .env to git — it's in .gitignore
```

---

## Important Notes

- **Only deposit funds you can afford to lose.** Trading bots carry risk.
- **Use a dedicated wallet** for bot trading, separate from your main holdings.
- **Start small** — deposit a small amount first to verify everything works.
- **Keep MATIC on Polygon** — You'll need a small amount (~$1) of MATIC/POL for gas fees on Polygon.
