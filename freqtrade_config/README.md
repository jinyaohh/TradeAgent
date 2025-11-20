# FreqTrade Configuration for TradeAgent

This directory contains FreqTrade configuration files for use with TradeAgent's FreqTrade integration.

## Files

- **config.json** - Main FreqTrade configuration file
- **README.md** - This file

## Usage

### Option 1: Via TradeAgent (Recommended)

1. Set `crypto_bot_type: freqtrade` in `config/trading.yaml`
2. Configure FreqTrade strategy settings in the `crypto` section
3. Start TradeAgent normally: `python main.py start`

TradeAgent will automatically use FreqTrade for crypto trading while maintaining unified portfolio management and risk monitoring.

### Option 2: Standalone FreqTrade

You can also run FreqTrade directly using these config files:

```bash
# Install FreqTrade
pip install freqtrade ccxt

# Download data
freqtrade download-data -c freqtrade_config/config.json --timerange 20240101-

# Backtest a strategy
freqtrade backtesting -c freqtrade_config/config.json --strategy SampleStrategy --timerange 20240101-20240630

# Run FreqTrade trading bot
freqtrade trade -c freqtrade_config/config.json --strategy SampleStrategy
```

## Configuration Overview

### Key Settings

- **max_open_trades**: Maximum number of concurrent trades (default: 5)
- **stake_currency**: Base currency for trading (USDT)
- **dry_run**: Paper trading mode (true/false)
- **dry_run_wallet**: Starting capital for paper trading

### Exchange Configuration

The `exchange` section configures the exchange connection:

```json
{
  "exchange": {
    "name": "binance",
    "key": "",      // Set via BINANCE_API_KEY environment variable
    "secret": "",   // Set via BINANCE_API_SECRET environment variable
    "pair_whitelist": ["BTC/USDT", "ETH/USDT"]
  }
}
```

**Important**: Never commit API keys to version control. Set them via environment variables or .env file.

### Strategy Configuration

Strategies are loaded from the `freqtrade_strategies/` directory. The strategy is specified when running FreqTrade:

- Via TradeAgent: Set `freqtrade_strategy` in `config/trading.yaml`
- Standalone: Use `--strategy StrategyName` CLI argument

## Environment Variables

Required environment variables (same as TradeAgent):

```bash
# Binance
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=true

# Optional: Telegram notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Integration with TradeAgent

When using FreqTrade via TradeAgent:

✅ **Unified Portfolio Management**: All positions tracked in one place
✅ **Unified Risk Management**: TradeAgent's risk rules apply
✅ **Unified Notifications**: Alerts go through TradeAgent's notification system
✅ **Unified Dashboard**: View all positions (crypto + stocks) in one dashboard

## Available Strategies

See `freqtrade_strategies/` directory for available strategies:

- **SampleStrategy**: RSI-based mean reversion strategy (example)

You can add your own strategies by creating new files in `freqtrade_strategies/` that inherit from `IStrategy`.

## Testing Strategies

Before live trading, always backtest:

```bash
# Backtest with FreqTrade
freqtrade backtesting \
  -c freqtrade_config/config.json \
  --strategy SampleStrategy \
  --timerange 20240101-20240630

# Or use TradeAgent's backtesting system
python -m backtesting.run_backtest --strategy freqtrade_sample
```

## Switching Between Custom and FreqTrade

TradeAgent supports both implementations:

**Custom CryptoBot** (default):
- Lightweight and integrated
- Simple to use and modify
- Good for learning and customization

**FreqTrade** (optional):
- Battle-tested trading engine
- 100+ exchanges supported
- Large community and strategy library
- Advanced features (hyperopt, edge positioning, etc.)

To switch: Change `crypto_bot_type` in `config/trading.yaml`:

```yaml
# Use custom bot
crypto_bot_type: custom

# Or use FreqTrade
crypto_bot_type: freqtrade
```

## Documentation

- FreqTrade docs: https://www.freqtrade.io/
- TradeAgent docs: `docs/ARCHITECTURE.md`
- Strategy development: https://www.freqtrade.io/en/stable/strategy-customization/

## Support

For FreqTrade-specific questions:
- FreqTrade Discord: https://discord.gg/p7nuUNVfP7
- FreqTrade GitHub: https://github.com/freqtrade/freqtrade

For TradeAgent integration questions:
- See `docs/USER_MANUAL.md`
- See `docs/CLAUDE.md` for development
