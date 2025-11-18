# TradeAgent Quick Start Guide

Get TradeAgent up and running in 15 minutes. This guide will walk you through installation, configuration, and launching your first paper trading session.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** installed
- **Git** installed
- **Internet connection** for downloading dependencies
- **Optional:** Binance testnet account (for crypto paper trading)
- **Optional:** Alpaca paper trading account (for stock paper trading)

## Step 1: Installation (5 minutes)

### 1.1 Clone the Repository

```bash
git clone https://github.com/yourusername/TradeAgent.git
cd TradeAgent
```

### 1.2 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- pandas, numpy (data processing)
- streamlit, plotly (dashboard)
- requests (API calls)
- pytest (testing)

## Step 2: Configuration (5 minutes)

### 2.1 Create Environment File

```bash
cp .env.example .env
```

### 2.2 Edit `.env` File

Open `.env` in your favorite text editor and configure:

#### Option A: Mock Trading (No API Keys Needed)

For testing without real APIs, just leave the `.env` as is. The system will automatically use mock connectors.

#### Option B: Paper Trading with Real APIs

```bash
# Binance Testnet (Crypto Paper Trading)
BINANCE_API_KEY=your_testnet_key_here
BINANCE_API_SECRET=your_testnet_secret_here
BINANCE_TESTNET=true

# Alpaca Paper Trading (Stocks)
ALPACA_API_KEY=your_paper_key_here
ALPACA_API_SECRET=your_paper_secret_here
ALPACA_PAPER=true

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2.3 Get API Keys (Optional)

#### Binance Testnet (Free)
1. Go to [https://testnet.binance.vision/](https://testnet.binance.vision/)
2. Login with GitHub
3. Generate API keys
4. Save to `.env`

#### Alpaca Paper Trading (Free)
1. Sign up at [https://alpaca.markets/](https://alpaca.markets/)
2. Navigate to Paper Trading section
3. Generate API keys
4. Save to `.env`

#### Telegram Bot (Optional)
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Save bot token
4. Get your chat ID from `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 2.4 Verify Configuration

```bash
python main.py config
```

This should display your current configuration without errors.

## Step 3: First Run (5 minutes)

### 3.1 Start the Trading Engine

```bash
python main.py start
```

You should see output like:

```
[2025-11-18 10:00:00] INFO - Starting TradeAgent v1.0...
[2025-11-18 10:00:00] INFO - Initializing portfolio manager...
[2025-11-18 10:00:00] INFO - Initializing risk monitor...
[2025-11-18 10:00:00] INFO - Starting crypto bot...
[2025-11-18 10:00:00] INFO - Starting stock bot...
[2025-11-18 10:00:00] INFO - TradeAgent is running!
```

### 3.2 Check System Status

Open a new terminal (keep the first one running) and check status:

```bash
python main.py status
```

Output:
```
System Status: RUNNING
Uptime: 5 minutes
Portfolio Value: $10,000.00
Open Positions: 0
Active Strategies: 2
```

### 3.3 Launch the Dashboard

In the second terminal, launch the web dashboard:

```bash
python main.py dashboard
```

Then open your browser to: **http://localhost:8501**

You should see the TradeAgent dashboard with:
- Portfolio overview
- Equity curve
- Asset allocation
- Open positions (none yet)
- Performance metrics

## Step 4: Understanding What's Running

### Default Configuration

TradeAgent starts with:

- **Portfolio:** $10,000 initial capital
- **Crypto Bot:** Trading BTC/USDT with RSI strategy
- **Stock Bot:** Trading AAPL, MSFT, GOOGL with RSI strategy
- **Risk Limits:** Max 2% risk per trade, max 5 positions
- **Mode:** Paper trading (no real money)

### Monitoring Your System

#### View Logs

```bash
tail -f logs/tradeagent.log
```

#### Check for Trades

The bots check for trading signals every 5 minutes. You may not see trades immediately - this is normal. The strategies wait for the right market conditions.

#### View in Dashboard

The dashboard updates in real-time. Refresh to see:
- New trades
- Position updates
- P&L changes
- Risk metrics

## Step 5: Basic Operations

### Pause Trading

```bash
python main.py pause
```

This pauses new trade entries but keeps monitoring running.

### Resume Trading

```bash
python main.py resume
```

### Stop Everything

```bash
python main.py stop
```

This safely shuts down all trading and closes the engine.

### View Help

```bash
python main.py help
```

## Troubleshooting

### "ModuleNotFoundError"

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "Connection Error" with APIs

Check:
1. API keys are correct in `.env`
2. `BINANCE_TESTNET=true` and `ALPACA_PAPER=true` are set
3. Internet connection is active
4. API keys have read and trade permissions

**Note:** If API connection fails, the system automatically falls back to mock connectors.

### Dashboard Won't Start

```bash
# Check if streamlit is installed
pip install --upgrade streamlit plotly

# Check if port 8501 is available
# Try a different port:
streamlit run dashboard/app.py --server.port 8502
```

### No Trades Happening

This is normal! The strategies wait for specific market conditions:

- **RSI Strategy:** Waits for RSI < 30 (oversold) or RSI > 70 (overbought)
- **Market Hours:** Stock bot only trades during US market hours (9:30 AM - 4:00 PM ET)
- **Risk Limits:** Trades may be blocked if risk limits are reached

Check `logs/tradeagent.log` for details on why trades aren't being placed.

## Next Steps

### 1. Explore the Dashboard

Navigate through all 4 pages:
- **Overview:** See portfolio health
- **Positions & Trades:** View detailed trade history
- **Performance:** Analyze strategy performance
- **Risk Management:** Monitor risk metrics

### 2. Run a Backtest

Test strategies on historical data:

```bash
# Create a backtest script
python -c "
from backtesting import BacktestEngine, BacktestConfig
from cryptobot.strategies.rsi_strategy import RsiStrategy
import pandas as pd

# This is a simplified example
print('Backtesting RSI strategy...')
print('See docs/phase6_advanced_backtesting.md for full examples')
"
```

### 3. Customize Strategies

Edit strategy parameters in `config/trading.yaml`:

```yaml
strategies:
  rsi:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    stop_loss_pct: 0.02
    take_profit_pct: 0.04
```

Then restart the trading engine.

### 4. Set Up Notifications

Configure Telegram to get alerts:

1. Set up bot (see Step 2.3)
2. Edit `.env` with bot token and chat ID
3. Restart engine
4. You'll receive notifications for:
   - Trade executions
   - Risk limit breaches
   - System errors
   - Daily summaries

### 5. Read the Full User Manual

For comprehensive information, see [USER_MANUAL.md](USER_MANUAL.md):
- Detailed configuration options
- Strategy development guide
- Risk management setup
- Advanced features

## 30-Day Paper Trading Plan

Before considering live trading:

### Week 1: Learning
- Run paper trading continuously
- Monitor all trades in dashboard
- Understand why trades happen
- Learn the command-line interface

### Week 2: Optimization
- Adjust strategy parameters
- Test different risk limits
- Backtest alternative strategies
- Fine-tune notification settings

### Week 3: Validation
- Verify consistent performance
- Check risk metrics are acceptable
- Ensure no critical errors
- Document any issues

### Week 4: Decision
- Review 30 days of results
- Calculate key metrics:
  - Win rate > 45%?
  - Max drawdown < 15%?
  - Sharpe ratio > 0.5?
- Decide: continue paper trading or consider small live capital

## Safety Checklist

Before going live (after 30 days of paper trading):

- [ ] 30+ days of successful paper trading
- [ ] Win rate > 45%
- [ ] Max drawdown < 15%
- [ ] All risk limits working correctly
- [ ] Notifications functioning
- [ ] No critical errors in logs
- [ ] Understand all strategy rules
- [ ] Emergency stop procedures documented
- [ ] Starting with very small capital ($100-500)
- [ ] Can afford to lose entire amount

## Quick Reference

### Common Commands

```bash
# Start/Stop
python main.py start
python main.py stop
python main.py status

# Control
python main.py pause
python main.py resume

# Monitor
python main.py dashboard
tail -f logs/tradeagent.log

# Config
python main.py config
python main.py help
```

### Key Files

```
.env                      # API keys and secrets
config/trading.yaml       # Trading configuration
config/risk.yaml          # Risk management rules
logs/tradeagent.log       # System logs
```

### Dashboard URL

```
http://localhost:8501
```

### Default Credentials

No authentication required for local dashboard.

## Getting Help

- **User Manual:** [USER_MANUAL.md](USER_MANUAL.md)
- **Technical Docs:** [docs/](.) directory
- **Issues:** [GitHub Issues](https://github.com/yourusername/TradeAgent/issues)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)

## Summary

You've now:
✅ Installed TradeAgent
✅ Configured paper trading
✅ Started the trading engine
✅ Launched the dashboard
✅ Learned basic operations

**Next:** Let it run for a few hours, watch the logs, and explore the dashboard. Then read the full [User Manual](USER_MANUAL.md) for advanced features.

**Remember:** This is paper trading with no real money at risk. Use this time to learn the system thoroughly before ever considering live trading.

Happy Paper Trading! 🎉
