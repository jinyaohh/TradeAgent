# TradeAgent 🤖📈

A hybrid algorithmic trading system for personal use, supporting both cryptocurrency and stock trading with intelligent risk management.

## ⚠️ Important Disclaimers

**TRADING INVOLVES SIGNIFICANT RISK OF LOSS**

- This software is for educational and personal use only
- Past performance does not guarantee future results
- Always start with paper trading before risking real money
- Never invest more than you can afford to lose
- The authors are not responsible for any financial losses
- Use at your own risk

## 🎯 Project Overview

TradeAgent combines the battle-tested [FreqTrade](https://www.freqtrade.io/) framework for cryptocurrency trading with a custom-built stock trading module, unified through shared risk management and portfolio tracking.

### Key Features

- **Dual Asset Support:** Trade both cryptocurrencies and stocks from one system
- **Risk Management:** Built-in position sizing, stop losses, and portfolio limits
- **Multiple Strategies:** RSI, Moving Averages, Momentum, and more
- **Backtesting:** Test strategies on historical data before going live
- **Paper Trading:** Simulate live trading without risking real money
- **Real-time Monitoring:** Web dashboard and Telegram notifications
- **Portfolio Management:** Unified view across all assets and positions

## 🏗️ Architecture

```
TradeAgent
├── Crypto Module (FreqTrade)
│   ├── CCXT Exchange Integration
│   └── Pre-built Strategies
├── Stock Module (Custom)
│   ├── Alpaca API Integration
│   └── Custom Strategies
└── Shared Components
    ├── Risk Management
    ├── Portfolio Manager
    ├── Technical Indicators
    ├── Notifications
    └── Monitoring Dashboard
```

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed system architecture and design
- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - 8-week phased implementation plan
- **[WORKFLOW.md](./WORKFLOW.md)** - Operational workflows and procedures
- **[TASK_BREAKDOWN.md](./TASK_BREAKDOWN.md)** - Granular task list with time estimates

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip and virtualenv
- Git
- API accounts:
  - Binance (or other crypto exchange)
  - Alpaca (for US stocks)
  - Telegram bot (for notifications)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/TradeAgent.git
cd TradeAgent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

1. **Set up API keys** in `.env`:
```bash
# Crypto Exchange
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here

# Stock Broker
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
ALPACA_PAPER=true  # Use paper trading

# Notifications
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id
```

2. **Configure trading parameters** in `config/config.yaml`

3. **Set up risk limits** in `config/risk.yaml`

### Running the Bot

```bash
# Paper trading mode (recommended for beginners)
python main.py --mode paper

# Backtesting
python scripts/backtest.py --strategy RsiStrategy --start 2023-01-01 --end 2024-01-01

# Live trading (use with caution!)
python main.py --mode live
```

### Monitoring

```bash
# Start the web dashboard
streamlit run monitoring/dashboard.py
```

Access dashboard at: http://localhost:8501

## 🧪 Development Workflow

### Phase 1: Foundation (Week 1)
- ✅ Project structure setup
- ✅ Configuration management
- ✅ Logging infrastructure
- ⬜ Complete documentation

### Phase 2: Crypto Module (Week 2)
- ⬜ FreqTrade integration
- ⬜ Exchange connectivity
- ⬜ First strategy implementation
- ⬜ Paper trading launch

### Phase 3-8: See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

## 📊 Supported Exchanges & Brokers

### Cryptocurrencies
- Binance
- Coinbase Pro
- Kraken
- 100+ more via CCXT

### Stocks
- Alpaca (US Markets)
- Interactive Brokers (planned)

## 🛡️ Risk Management

Built-in safety features:

- **Position Sizing:** Never risk more than 1-2% per trade
- **Stop Losses:** Automatic stop loss on every position
- **Portfolio Limits:** Max 5 concurrent positions
- **Daily Loss Limit:** Auto-pause at 5% daily loss
- **Max Drawdown:** Emergency stop at 15% drawdown
- **Kill Switch:** Manual emergency stop button

## 📈 Strategies

### Included Strategies

1. **RSI Mean Reversion**
   - Entry: RSI < 30 (oversold)
   - Exit: RSI > 70 (overbought)
   - Stop: 2% fixed

2. **Moving Average Crossover**
   - Entry: Fast MA crosses above slow MA
   - Exit: Fast MA crosses below slow MA
   - Stop: ATR-based

3. **Momentum Strategy**
   - Entry: Price breakout + volume confirmation
   - Exit: Momentum reversal
   - Stop: Trailing 3%

### Creating Custom Strategies

See [Strategy Development Guide](./docs/strategy_development.md) (coming soon)

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run all tests with coverage
pytest --cov=. tests/
```

## 📱 Notifications

Receive alerts via Telegram for:

- Trade executions (entry/exit)
- Risk limit breaches
- System errors
- Daily performance summary

## 📊 Performance Metrics

The system tracks:

- Total Return & CAGR
- Sharpe Ratio & Sortino Ratio
- Maximum Drawdown
- Win Rate & Profit Factor
- Average Win/Loss
- Trade Statistics

## 🔧 Technology Stack

- **Language:** Python 3.10+
- **Crypto Trading:** FreqTrade, CCXT
- **Stock Trading:** Alpaca Trade API
- **Technical Analysis:** pandas-ta, TA-Lib
- **Data Processing:** Pandas, NumPy
- **Dashboard:** Streamlit
- **Notifications:** python-telegram-bot
- **Database:** SQLite (dev), PostgreSQL (prod)
- **Testing:** pytest

## 📝 Configuration Files

```
config/
├── config.yaml          # Main configuration
├── exchanges.yaml       # Exchange settings
├── strategies.yaml      # Strategy parameters
└── risk.yaml           # Risk management rules
```

## 🐛 Troubleshooting

### Common Issues

**API Connection Errors**
- Check API keys are correct
- Verify API permissions (read + trade)
- Check IP whitelist settings

**Strategy Not Trading**
- Check if in paper mode
- Verify strategy is enabled in config
- Check risk limits aren't blocking trades

**Data Fetching Fails**
- Check internet connection
- Verify exchange status
- Check API rate limits

For more help, see [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) (coming soon)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- [FreqTrade](https://www.freqtrade.io/) - Excellent crypto trading framework
- [Alpaca](https://alpaca.markets/) - Commission-free stock trading API
- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange integration
- All the open-source contributors in the algo trading community

## ⚖️ Legal & Compliance

- This software is for personal use only
- Not financial advice - do your own research
- Comply with your local trading regulations
- Report all trades for tax purposes
- Respect exchange terms of service

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/TradeAgent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/TradeAgent/discussions)
- **Email:** your.email@example.com

## 🎯 Roadmap

### Phase 1 (Current)
- [x] Architecture design
- [ ] Project setup
- [ ] Core infrastructure

### Phase 2
- [ ] Crypto module integration
- [ ] Stock module development
- [ ] Risk management system

### Phase 3
- [ ] Monitoring & notifications
- [ ] Backtesting framework
- [ ] Paper trading

### Phase 4
- [ ] Production deployment
- [ ] Live trading with small capital
- [ ] Performance optimization

### Future Enhancements
- [ ] Machine learning integration
- [ ] Options trading support
- [ ] Multi-account management
- [ ] Mobile app
- [ ] Advanced portfolio analytics

## 📚 Learning Resources

### For Beginners
- "Algorithmic Trading" by Ernie Chan
- FreqTrade documentation
- Alpaca learning resources

### For Risk Management
- "The New Trading for a Living" by Dr. Alexander Elder
- "Position Sizing" by Van K. Tharp

---

**Remember:** Always start with paper trading, never risk more than you can afford to lose, and thoroughly backtest any strategy before going live.

Happy Trading! 🚀📊
