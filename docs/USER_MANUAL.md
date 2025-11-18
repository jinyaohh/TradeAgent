# TradeAgent User Manual

**Version:** 1.0
**Last Updated:** 2025-11-18

Complete guide to using the TradeAgent algorithmic trading system.

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Trading Operations](#trading-operations)
6. [Dashboard & Monitoring](#dashboard--monitoring)
7. [Backtesting](#backtesting)
8. [Risk Management](#risk-management)
9. [Strategies](#strategies)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Introduction

### What is TradeAgent?

TradeAgent is a professional-grade algorithmic trading system that supports both cryptocurrency and stock trading. It features:

- **Multi-asset trading** across crypto (Binance) and stocks (Alpaca)
- **Advanced risk management** with position sizing, stop losses, and portfolio limits
- **Comprehensive backtesting** with walk-forward analysis and Monte Carlo simulation
- **Real-time monitoring** via web dashboard and notifications
- **Production-ready code** with 100% test coverage

### Who Should Use This?

- **Algorithmic traders** wanting a complete trading framework
- **Developers** building custom trading strategies
- **Traders** moving from manual to automated trading
- **Learners** studying algorithmic trading concepts

### Important Notes

⚠️ **Always start with paper trading**
⚠️ **Never risk more than you can afford to lose**
⚠️ **Thoroughly backtest before live trading**
⚠️ **Monitor continuously during first month**

---

## System Architecture

### Components

```
TradeAgent/
├── Trading Engine        # Orchestrates all trading operations
├── Crypto Bot            # Cryptocurrency trading (Binance)
├── Stock Bot             # Stock trading (Alpaca)
├── Risk Monitor          # Enforces risk limits and safety
├── Portfolio Manager     # Tracks positions and P&L
├── Notification System   # Alerts via Telegram/Email
├── Dashboard             # Web-based monitoring interface
└── Backtesting Engine    # Strategy validation and optimization
```

### Data Flow

```
Market Data → Strategies → Risk Monitor → Order Execution
                                ↓
                         Portfolio Manager
                                ↓
                    Notifications & Dashboard
```

### Trading Loop

1. **Data Fetch:** Get latest price data from exchanges
2. **Signal Generation:** Strategies analyze data and generate signals
3. **Risk Check:** Risk monitor validates trade against limits
4. **Order Execution:** If approved, place order with exchange
5. **Position Management:** Monitor positions for exit signals
6. **Reporting:** Update portfolio, send notifications

---

## Installation & Setup

### Quick Setup

See [QUICKSTART.md](QUICKSTART.md) for a 15-minute setup guide.

### Detailed Setup

#### 1. System Requirements

- **Operating System:** Linux, macOS, or Windows 10+
- **Python:** 3.10 or higher
- **RAM:** Minimum 2GB, recommended 4GB
- **Disk Space:** 500MB for code + data storage
- **Internet:** Stable connection required

#### 2. Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `pandas`, `numpy` - Data processing
- `streamlit`, `plotly` - Dashboard
- `ccxt` - Crypto exchange integration (optional)
- `alpaca-trade-api` - Stock broker integration (optional)
- `requests` - API calls
- `pytest` - Testing

#### 3. Exchange Accounts

**For Crypto Trading:**
- Binance account (or testnet for paper trading)
- API key with read and trade permissions

**For Stock Trading:**
- Alpaca account (free paper trading)
- API key and secret

**For Notifications:**
- Telegram bot (optional)
- Email SMTP credentials (optional)

---

## Configuration

### Configuration Files

TradeAgent uses multiple configuration files in `config/`:

#### `trading.yaml` - Main Configuration

```yaml
# Trading mode
mode: paper  # paper or live

# Initial capital
initial_capital: 10000.0

# Trading settings
trading:
  crypto:
    enabled: true
    symbols: [BTC/USDT, ETH/USDT]
    strategy: rsi
    interval: 5m  # Check every 5 minutes

  stock:
    enabled: true
    symbols: [AAPL, MSFT, GOOGL]
    strategy: rsi
    interval: 5m

# Risk management
risk:
  max_risk_per_trade: 0.02  # 2% max risk per trade
  max_positions: 5           # Max concurrent positions
  max_position_size: 0.10    # Max 10% of capital per position
  daily_loss_limit: 0.05     # Stop if 5% daily loss
  max_drawdown: 0.15         # Circuit breaker at 15% drawdown
```

#### `.env` - API Keys and Secrets

```bash
# Binance
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true

# Alpaca
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
ALPACA_PAPER=true

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

#### `strategies.yaml` - Strategy Parameters

```yaml
rsi:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  stop_loss_pct: 0.02
  take_profit_pct: 0.04

ma_crossover:
  fast_period: 10
  slow_period: 30
  stop_loss_pct: 0.025
  take_profit_pct: 0.05
```

### Environment Variables

All sensitive data goes in `.env`:

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Binance API key | For crypto trading |
| `BINANCE_API_SECRET` | Binance API secret | For crypto trading |
| `BINANCE_TESTNET` | Use testnet (`true`/`false`) | Recommended |
| `ALPACA_API_KEY` | Alpaca API key | For stock trading |
| `ALPACA_API_SECRET` | Alpaca API secret | For stock trading |
| `ALPACA_PAPER` | Use paper trading (`true`/`false`) | Recommended |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Optional |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Optional |

---

## Trading Operations

### Starting the System

```bash
# Start trading engine
python main.py start

# Expected output:
# [INFO] Starting TradeAgent...
# [INFO] Initializing components...
# [INFO] Starting crypto bot...
# [INFO] Starting stock bot...
# [INFO] TradeAgent is running!
```

The engine will:
1. Load configuration
2. Initialize portfolio manager
3. Connect to exchanges
4. Start risk monitoring
5. Launch trading bots
6. Begin monitoring loop

### Checking Status

```bash
python main.py status

# Output:
# System Status: RUNNING
# Uptime: 1 hour 23 minutes
# Portfolio Value: $10,245.50
# Cash: $7,500.00
# Positions Value: $2,745.50
# Open Positions: 2
#   - BTC/USDT: +$125.30 (+5.12%)
#   - AAPL: -$20.20 (-0.98%)
# P&L Today: +$245.50 (+2.46%)
```

### Pausing & Resuming

```bash
# Pause trading (no new entries, but keeps monitoring)
python main.py pause

# Resume trading
python main.py resume
```

When paused:
- No new positions opened
- Existing positions continue to be monitored
- Stop losses and take profits still active
- Risk monitoring continues

### Stopping the System

```bash
python main.py stop

# This will:
# 1. Stop opening new positions
# 2. Close all open positions (if configured)
# 3. Disconnect from exchanges
# 4. Save state and logs
# 5. Shut down gracefully
```

**Note:** By default, open positions are NOT automatically closed when stopping. Configure `close_on_stop: true` in `trading.yaml` to change this behavior.

### Emergency Stop

For immediate shutdown:

```bash
# Force stop (Ctrl+C if running in foreground)
# Or kill the process
kill $(cat logs/tradeagent.pid)
```

**Use emergency stop only when necessary**. It may not close positions cleanly.

---

## Dashboard & Monitoring

### Launching the Dashboard

```bash
python main.py dashboard

# Or directly:
streamlit run dashboard/app.py
```

Access at: **http://localhost:8501**

### Dashboard Pages

#### 1. Overview Page

Displays:
- **Key Metrics:** Portfolio value, cash, P&L
- **Equity Curve:** 30-day portfolio value history
- **Asset Allocation:** Pie chart of cash/crypto/stocks
- **Open Positions:** All current positions with P&L
- **Recent Activity:** Last 3 trades and alerts
- **Performance Metrics:** Win rate, Sharpe ratio, max drawdown
- **System Health:** Bot status, last update time

#### 2. Positions & Trades Page

**Open Positions Tab:**
- List of all open positions
- Entry price, current price, P&L
- Stop loss and take profit levels
- Position details and risk metrics

**Trade History Tab:**
- Complete trade history
- Filter by date, asset type, result
- Export to CSV
- Trade statistics

**Position Analysis Tab:**
- P&L distribution by symbol
- Win rate by strategy
- Average holding time
- Best/worst trades

#### 3. Performance Page

**Returns Analysis:**
- Cumulative returns chart
- Daily returns distribution
- Monthly performance

**Risk Metrics:**
- Drawdown analysis
- Volatility over time
- VaR, CVaR, Sharpe, Sortino

**Strategy Performance:**
- Compare strategies
- Win rate, profit factor
- Strategy-specific metrics

**Trade Analytics:**
- P&L distribution
- Trade duration breakdown
- Streak analysis

#### 4. Risk Management Page

**Position Limits:**
- Current vs. max position size
- Number of positions
- Cash reserve status

**Portfolio Limits:**
- Daily loss limit progress
- Max drawdown vs. limit
- Asset allocation vs. limits

**Emergency Controls:**
- Pause/Resume trading
- Emergency stop button
- Close all positions
- Circuit breaker status

### Notifications

Configure in `.env`:

**Telegram Notifications:**
```bash
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

You'll receive notifications for:
- Trade executions (entry/exit)
- Risk limit breaches
- System errors
- Daily performance summary

**Email Notifications:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Console Notifications:**
Always enabled, prints to terminal and logs.

### Logs

Logs are stored in `logs/tradeagent.log`:

```bash
# View live logs
tail -f logs/tradeagent.log

# Search logs
grep "ERROR" logs/tradeagent.log
grep "Trade executed" logs/tradeagent.log

# View last 100 lines
tail -n 100 logs/tradeagent.log
```

Log levels:
- **DEBUG:** Detailed information for debugging
- **INFO:** General information messages
- **WARNING:** Warning messages
- **ERROR:** Error messages
- **CRITICAL:** Critical issues requiring immediate attention

---

## Backtesting

### Quick Backtest

```python
from backtesting import BacktestEngine, BacktestConfig
from cryptobot.strategies.rsi_strategy import RsiStrategy
import pandas as pd

# Load historical data
data = pd.read_csv('data/BTC_USDT_1h.csv', index_col='timestamp', parse_dates=True)

# Configure backtest
config = BacktestConfig(
    initial_capital=10000.0,
    commission=0.001,  # 0.1% per trade
    slippage=0.0005    # 0.05% slippage
)

# Create engine and strategy
engine = BacktestEngine(config)
strategy = RsiStrategy()

# Run backtest
result = engine.run_backtest(data, strategy)

# Print results
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Win Rate: {result.win_rate:.2%}")
```

### Advanced Backtesting

See [phase6_advanced_backtesting.md](phase6_advanced_backtesting.md) for:
- Walk-forward analysis
- Monte Carlo simulation
- Strategy optimization
- Parameter tuning
- Performance reporting

### Optimization

```python
from backtesting import StrategyOptimizer

optimizer = StrategyOptimizer(engine, strategy)

# Define parameter ranges
param_ranges = {
    'rsi_period': [10, 14, 20],
    'rsi_oversold': [20, 25, 30],
    'rsi_overbought': [70, 75, 80]
}

# Grid search
results = optimizer.grid_search(data, param_ranges)

# Get best parameters
best = results.iloc[0]
print(f"Best parameters: {best['params']}")
print(f"Sharpe Ratio: {best['sharpe_ratio']:.2f}")
```

---

## Risk Management

### Position Sizing

Configure in `config/trading.yaml`:

```yaml
risk:
  position_sizing_method: risk_pct  # Options: risk_pct, fixed_pct, kelly, atr, fixed_amount
  max_risk_per_trade: 0.02          # 2% of capital
  max_position_size: 0.10           # 10% of capital
```

**Position Sizing Methods:**

1. **risk_pct:** Risk fixed % per trade (recommended)
2. **fixed_pct:** Fixed % of capital per trade
3. **kelly:** Kelly Criterion (aggressive)
4. **atr:** ATR-based volatility sizing
5. **fixed_amount:** Fixed dollar amount

### Stop Losses

All positions have mandatory stop losses:

```yaml
strategies:
  rsi:
    stop_loss_pct: 0.02  # 2% stop loss
    stop_loss_type: fixed  # fixed, trailing, or atr
```

**Stop Loss Types:**
- **fixed:** Fixed percentage from entry
- **trailing:** Trails price at fixed distance
- **atr:** Based on Average True Range

### Take Profits

```yaml
strategies:
  rsi:
    take_profit_pct: 0.04  # 4% take profit
    take_profit_type: fixed  # fixed or trailing
```

### Portfolio Limits

```yaml
risk:
  max_positions: 5              # Max concurrent positions
  max_position_size: 0.10       # Max 10% per position
  daily_loss_limit: 0.05        # Stop at 5% daily loss
  max_drawdown: 0.15            # Circuit breaker at 15% drawdown
  min_cash_reserve: 0.20        # Keep 20% in cash
```

### Circuit Breakers

Automatic trading halts when:
- Daily loss exceeds limit
- Max drawdown reached
- Too many consecutive losses
- System errors detected

Resume trading:
```bash
python main.py resume
```

---

## Strategies

### Built-in Strategies

#### 1. RSI Mean Reversion

**Logic:**
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Fixed stop loss and take profit

**Parameters:**
```yaml
rsi:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  stop_loss_pct: 0.02
  take_profit_pct: 0.04
```

**Best For:** Range-bound markets, mean-reverting assets

#### 2. Moving Average Crossover

**Logic:**
- Buy when fast MA crosses above slow MA
- Sell when fast MA crosses below slow MA
- ATR-based stop loss

**Parameters:**
```yaml
ma_crossover:
  fast_period: 10
  slow_period: 30
  stop_loss_atr_multiplier: 2.0
  take_profit_pct: 0.05
```

**Best For:** Trending markets

#### 3. Momentum Strategy

**Logic:**
- Buy on price breakout + volume confirmation
- Sell on momentum reversal
- Trailing stop loss

**Parameters:**
```yaml
momentum:
  lookback_period: 20
  breakout_threshold: 1.5  # Standard deviations
  volume_threshold: 1.2    # 20% above average
  stop_loss_pct: 0.03
  trailing_stop: true
```

**Best For:** Volatile, trending markets

### Creating Custom Strategies

See [CLAUDE.md](CLAUDE.md) for development guide.

Basic structure:

```python
from shared.indicators.technical import TechnicalIndicators

class MyStrategy:
    def __init__(self, param1=10, param2=20):
        self.param1 = param1
        self.param2 = param2
        self.indicators = TechnicalIndicators()

    def populate_indicators(self, df):
        """Add indicators to dataframe"""
        df['my_indicator'] = self.indicators.sma(df['close'], self.param1)
        return df

    def generate_signal(self, df):
        """Generate buy/sell signals"""
        if df['my_indicator'].iloc[-1] > df['close'].iloc[-1]:
            return 'buy'
        elif df['my_indicator'].iloc[-1] < df['close'].iloc[-1]:
            return 'sell'
        return 'hold'
```

---

## Troubleshooting

### Common Issues

#### System Won't Start

**Error:** `ModuleNotFoundError`

**Solution:**
```bash
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt  # Reinstall dependencies
```

#### No Trades Executing

**Possible Causes:**
1. **Risk limits reached:** Check dashboard risk page
2. **Wrong market hours:** Stocks only trade 9:30 AM - 4:00 PM ET
3. **No signals:** Strategies waiting for right conditions
4. **Paused:** System may be in paused state

**Check logs:**
```bash
grep "Trade blocked" logs/tradeagent.log
grep "Signal:" logs/tradeagent.log
```

#### API Connection Errors

**Error:** `Connection failed`

**Solution:**
1. Check API keys in `.env`
2. Verify `BINANCE_TESTNET=true` and `ALPACA_PAPER=true`
3. Check internet connection
4. Verify API key permissions (read + trade)

**Note:** System automatically falls back to mock connectors if APIs fail.

#### Dashboard Not Loading

**Error:** `Dashboard won't start`

**Solution:**
```bash
pip install --upgrade streamlit plotly
streamlit run dashboard/app.py --server.port 8502
```

### Debug Mode

Enable detailed logging:

```python
# In main.py or config
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. Check logs: `logs/tradeagent.log`
2. Read error message carefully
3. Search GitHub Issues
4. Consult [ARCHITECTURE.md](ARCHITECTURE.md)
5. Review [phase documentation](.)

---

## Best Practices

### Before Live Trading

- [ ] Run paper trading for 30+ days
- [ ] Achieve win rate > 45%
- [ ] Keep max drawdown < 15%
- [ ] Backtest on 1+ year of data
- [ ] Verify all risk limits working
- [ ] Test emergency stop procedures
- [ ] Set up notifications
- [ ] Start with very small capital ($100-500)

### During Operation

✅ **Monitor daily** for first month
✅ **Review trades** in dashboard
✅ **Check logs** for errors
✅ **Verify P&L** matches expectations
✅ **Adjust** based on performance
✅ **Document** any issues

### Risk Management

⚠️ **Never risk more than 2% per trade**
⚠️ **Never have more than 5 positions**
⚠️ **Always use stop losses**
⚠️ **Keep 20% cash reserve**
⚠️ **Set daily loss limits**
⚠️ **Use circuit breakers**

### Performance Review

**Weekly:**
- Review P&L
- Check win rate
- Analyze losing trades
- Verify risk limits

**Monthly:**
- Full performance review
- Strategy comparison
- Risk metric analysis
- Decide continue/adjust/stop

---

## Quick Reference

### Commands

```bash
python main.py start      # Start trading
python main.py stop       # Stop trading
python main.py status     # Check status
python main.py pause      # Pause (no new entries)
python main.py resume     # Resume trading
python main.py dashboard  # Launch dashboard
python main.py config     # Show configuration
python main.py help       # Show help
```

### Key Files

```
.env                    # API keys
config/trading.yaml     # Main config
config/risk.yaml        # Risk settings
config/strategies.yaml  # Strategy params
logs/tradeagent.log     # System logs
```

### Important URLs

```
Dashboard:  http://localhost:8501
Binance Testnet: https://testnet.binance.vision/
Alpaca Paper: https://app.alpaca.markets/paper/dashboard/overview
```

---

## Support

- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)
- **Development:** [CLAUDE.md](CLAUDE.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues:** [GitHub Issues](https://github.com/yourusername/TradeAgent/issues)

---

**Remember:** This is a powerful tool. Use it responsibly, always start with paper trading, and never risk more than you can afford to lose.

Happy Trading! 🚀📊
