# TradeAgent 🤖📈

A professional algorithmic trading system supporting both cryptocurrency and stock trading with intelligent risk management, comprehensive backtesting, and real-time monitoring.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)]()

## ⚠️ Important Disclaimers

**TRADING INVOLVES SIGNIFICANT RISK OF LOSS**

- This software is for educational and personal use only
- Past performance does not guarantee future results
- Always start with paper trading before risking real money
- Never invest more than you can afford to lose
- The authors are not responsible for any financial losses

## 🎯 Quick Overview

TradeAgent is a complete algorithmic trading platform with:

- **Multi-Asset Trading:** Crypto (Binance) and stocks (Alpaca)
- **Advanced Backtesting:** Walk-forward analysis, Monte Carlo simulation, 40+ metrics
- **Risk Management:** Position sizing, stop losses, portfolio limits, circuit breakers
- **Real-Time Monitoring:** Web dashboard and multi-channel notifications
- **Production Ready:** ~16,600+ lines of tested code, 100% test pass rate

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/TradeAgent.git
cd TradeAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your API keys (paper trading recommended)
```

### First Run (Paper Trading)

```bash
# Start the trading engine
python main.py start

# Check status
python main.py status

# Launch web dashboard
python main.py dashboard

# View logs
tail -f logs/tradeagent.log

# Stop trading
python main.py stop
```

📖 **For detailed setup instructions, see [QUICKSTART.md](docs/QUICKSTART.md)**

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 15 minutes
- **[User Manual](docs/USER_MANUAL.md)** - Complete usage guide
- **[Dashboard Guide](docs/DASHBOARD_GUIDE.md)** - Using the web interface

### Development & Architecture
- **[Development Guide](docs/CLAUDE.md)** - For AI assistants and developers
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Workflow](docs/WORKFLOW.md)** - Operational procedures

### Technical Documentation
- [Advanced Backtesting](docs/phase6_advanced_backtesting.md)
- [Integration & Testing](docs/phase7_integration_testing.md)
- [Broker Integration](docs/phase8_broker_integration.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)

## 🌟 Key Features

### Trading Capabilities
✅ Cryptocurrency trading (Binance, testnet & live)
✅ Stock trading (Alpaca, US markets)
✅ Multiple strategies (RSI, MA Crossover, Momentum)
✅ Paper trading mode for safe testing
✅ Automatic order execution with validation

### Risk Management
✅ Position sizing (5 methods including Kelly Criterion)
✅ Stop-loss and take-profit automation
✅ Portfolio-level risk limits
✅ Daily loss limits and drawdown protection
✅ Emergency stop and circuit breakers

### Backtesting & Analysis
✅ Walk-forward analysis (prevent overfitting)
✅ Monte Carlo simulation (robustness testing)
✅ Strategy optimization (grid search, random search)
✅ 40+ performance metrics
✅ Comprehensive reports and visualizations

### Monitoring & Alerts
✅ Real-time web dashboard (Streamlit)
✅ Multi-channel notifications (Telegram, Email, Console)
✅ Position and P&L tracking
✅ Performance analytics
✅ System health monitoring

## 🏗️ System Architecture

```
TradeAgent/
├── core/                  # Trading engine and bot orchestration
├── cryptobot/            # Cryptocurrency trading strategies
├── stockbot/             # Stock trading strategies
├── shared/               # Risk management, indicators, portfolio
├── backtesting/          # Advanced backtesting framework
├── exchanges/            # Exchange connectors (Binance, Alpaca)
├── monitoring/           # Notifications and logging
├── dashboard/            # Streamlit web interface
├── config/               # Configuration files
├── tests/                # Comprehensive test suite
└── docs/                 # Documentation
```

## 💻 Command-Line Interface

```bash
# Trading operations
python main.py start              # Start the trading engine
python main.py stop               # Stop all trading
python main.py status             # Check system status
python main.py pause              # Pause trading (keep running)
python main.py resume             # Resume trading

# Monitoring
python main.py dashboard          # Launch web dashboard

# Configuration
python main.py config             # Show current configuration
python main.py help               # Show all commands
```

## 📊 Dashboard

Access the web dashboard at `http://localhost:8501` to view:

- **Overview:** Portfolio value, equity curve, asset allocation, open positions
- **Positions & Trades:** Detailed position tracking and trade history
- **Performance:** Returns analysis, risk metrics, strategy comparison
- **Risk Management:** Position limits, emergency controls, risk gauges

## 🔐 Configuration

Main configuration files in `config/`:

- **trading.yaml** - Trading settings, strategies, risk parameters
- **exchanges.yaml** - Exchange/broker API settings
- **risk.yaml** - Risk management rules
- **strategies.yaml** - Strategy parameters

Environment variables in `.env`:

```bash
# Binance (Crypto)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true  # Use testnet for paper trading

# Alpaca (Stocks)
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
ALPACA_PAPER=true  # Use paper trading

# Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/test_integration.py
pytest tests/test_backtesting.py
pytest tests/test_exchanges.py

# Run with coverage
pytest --cov=. tests/
```

**Test Coverage:** 100% pass rate across all modules

## 📈 Current Status

- **Development:** ✅ Complete (8/8 phases)
- **Testing:** ✅ All tests passing
- **Code Quality:** ✅ Production-grade (~16,600+ lines)
- **Documentation:** ✅ Comprehensive
- **Paper Trading:** ✅ Ready
- **Live Trading:** ⚠️ Requires 30-day paper trading validation

## 🛡️ Safety Features

- **Never skip paper trading** - System defaults to paper trading mode
- **Automatic risk checks** - All trades validated before execution
- **Position limits** - Maximum 5 concurrent positions
- **Stop losses** - Mandatory on every position
- **Daily loss limit** - Auto-pause at 5% daily loss
- **Emergency stop** - Manual kill switch available
- **Health monitoring** - Auto-reconnection on connection failures

## 🤝 Support & Contributing

- **Issues:** [GitHub Issues](https://github.com/yourusername/TradeAgent/issues)
- **Documentation:** See [docs/](docs/) directory
- **Questions:** See [User Manual](docs/USER_MANUAL.md)
- **Development:** See [CLAUDE.md](docs/CLAUDE.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FreqTrade](https://www.freqtrade.io/) - Inspiration for crypto trading framework
- [Alpaca](https://alpaca.markets/) - Commission-free stock trading API
- [Binance](https://www.binance.com/) - Cryptocurrency exchange
- All open-source contributors in the algo trading community

## 📚 Learning Resources

### Recommended Reading
- "Algorithmic Trading" by Ernie Chan
- "The New Trading for a Living" by Dr. Alexander Elder
- "Position Sizing" by Van K. Tharp

### Online Resources
- [FreqTrade Documentation](https://www.freqtrade.io/)
- [Alpaca API Docs](https://alpaca.markets/docs/)
- [Binance API Docs](https://binance-docs.github.io/apidocs/)

---

## ⚡ Next Steps

1. **Read the [Quick Start Guide](docs/QUICKSTART.md)** - 15 minutes
2. **Configure paper trading** - Set up API keys in `.env`
3. **Run paper trading for 30 days** - Validate strategies
4. **Review performance** - Analyze results in dashboard
5. **Consider live trading** - Only after successful paper trading

---

**Remember:** Start small, test thoroughly, and never risk more than you can afford to lose.

Happy Trading! 🚀📊
