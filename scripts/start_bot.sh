#!/bin/bash
# ============================================
# Polymarket Bot — Start Everything
# ============================================
# Usage: ./scripts/start_bot.sh [paper|live]
# Default: paper trading mode

set -e

MODE="${1:-paper-trade}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  Polymarket Bot — Starting Up"
echo "============================================"

# Check if bot is already running
if pgrep -f "main.py --mode" > /dev/null 2>&1; then
    echo -e "${YELLOW}Bot is already running. Stopping old instance...${NC}"
    pkill -f "main.py --mode" 2>/dev/null || true
    sleep 2
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}No virtual environment found. Run: python3 -m venv .venv && pip install -r requirements.txt${NC}"
    exit 1
fi

# Initialize database if needed
if [ ! -f "data/trades.db" ]; then
    echo "Initializing database..."
    python scripts/setup_db.py
fi

# Create directories
mkdir -p data/reports data/logs data/historical

# Initialize signals file
if [ ! -f "data/reports/signals.json" ]; then
    echo '{"signals": []}' > data/reports/signals.json
fi

# Start the bot
echo -e "${GREEN}Starting bot in ${MODE} mode...${NC}"
nohup python main.py --mode "$MODE" > data/logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot PID: $BOT_PID"

# Wait for first cycle
sleep 5

# Verify it's running
if kill -0 $BOT_PID 2>/dev/null; then
    echo -e "${GREEN}Bot is running successfully!${NC}"
else
    echo -e "${RED}Bot failed to start. Check data/logs/bot.log${NC}"
    tail -20 data/logs/bot.log
    exit 1
fi

echo ""
echo "============================================"
echo "  Bot is running in the background"
echo "============================================"
echo ""
echo "  Monitor:     tail -f data/logs/bot.log"
echo "  Dashboard:   python scripts/dashboard.py"
echo "  Stop:        pkill -f 'main.py --mode'"
echo ""
echo "  The bot will keep running even if you"
echo "  close this terminal."
echo ""
echo "  For Claude Code reviews, open Claude Code"
echo "  and say: 'start the bot reviews'"
echo "============================================"
