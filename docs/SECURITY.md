# Security Guide

## Credential Management

### Never Commit Secrets
- The `.gitignore` file is configured to exclude `.env` and all secret files
- **NEVER** hardcode API keys, private keys, or passwords in source code
- **NEVER** commit `.env` files to git, even to private repositories
- Before every commit, verify no secrets are staged: `git diff --cached`

### Environment Variables
All sensitive configuration is stored in environment variables via the `.env` file:

```bash
# Required
POLYMARKET_API_KEY=        # Polymarket API key
POLYMARKET_SECRET=         # Polymarket API secret
POLYMARKET_PASSPHRASE=     # Polymarket API passphrase
PRIVATE_KEY=               # Polygon wallet private key (for order signing)
WALLET_ADDRESS=            # Polygon wallet address

# Optional
TELEGRAM_BOT_TOKEN=        # For trade notifications
TELEGRAM_CHAT_ID=          # Telegram chat for alerts
```

### Pre-Commit Hooks
The project uses pre-commit hooks to catch accidental secret commits:
- **gitleaks**: Scans for API keys, tokens, and secrets in staged files
- **detect-private-key**: Catches PEM-encoded private keys

These hooks run automatically on every `git commit`. Do not bypass them with `--no-verify`.

---

## Wallet Security

### Use a Dedicated Trading Wallet
- Create a **separate wallet** exclusively for bot trading
- **Never** use your main wallet or a wallet holding significant assets
- Only transfer the amount you intend to trade with

### Principle of Least Privilege
- The bot wallet should only contain trading funds
- Do not store other tokens or NFTs in the bot wallet
- Keep the minimum necessary balance for trading + gas fees

### Private Key Protection
- Store private keys only in the `.env` file on the machine running the bot
- Consider using a hardware wallet for signing if available
- Restrict file permissions: `chmod 600 .env`
- On production servers, use a secrets manager (AWS Secrets Manager, HashiCorp Vault) instead of `.env` files

---

## Key Rotation

### When to Rotate Keys
- If you suspect a key has been compromised
- After revoking access for a team member
- Periodically (recommended: every 90 days)

### How to Rotate
1. Generate new API credentials on Polymarket
2. Update `.env` with new credentials
3. Restart the bot
4. Verify the bot connects successfully
5. Revoke the old credentials

---

## Network Security

### API Communication
- All API calls use HTTPS (TLS encrypted)
- The bot validates SSL certificates on all connections
- API rate limits are respected to avoid IP bans

### Server Deployment
- Run the bot on a trusted, private server
- Use firewall rules to restrict inbound access
- Keep the OS and Python packages up to date
- Monitor for unauthorized access attempts
- Use Docker for isolation (see `Dockerfile`)

---

## Incident Response

### If You Suspect a Compromise
1. **Immediately** revoke all API keys on Polymarket
2. Transfer remaining funds out of the bot wallet
3. Stop the bot
4. Review logs for unauthorized activity
5. Generate new wallet and API credentials
6. Investigate how the compromise occurred

### If the Bot Behaves Unexpectedly
1. Stop the bot (`Ctrl+C` or `docker stop`)
2. Cancel all open orders manually on Polymarket
3. Review recent trades in the trade journal
4. Check logs for errors or anomalies
5. Do not restart until the issue is understood
