# TradeAgent Architecture Design

## 🎯 System Overview

TradeAgent is a hybrid algorithmic trading system that supports both cryptocurrency and stock trading for personal use. The system was originally designed to leverage FreqTrade for crypto trading and includes a custom stock trading module. Both modules are unified through shared risk management and portfolio management layers.

**Implementation Note:** The system includes a custom CryptoBot implementation (Phases 2-3) that provides crypto trading capabilities. FreqTrade can be optionally installed and integrated for users who prefer the battle-tested FreqTrade framework. Both approaches are supported by the architecture.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TradeAgent System                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
         ┌──────────▼──────────┐    ┌──────────▼──────────┐
         │   CRYPTO MODULE     │    │   STOCK MODULE      │
         │ (Custom/FreqTrade)  │    │   (Custom)          │
         └──────────┬──────────┘    └──────────┬──────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    SHARED COMPONENTS      │
                    ├───────────────────────────┤
                    │ • Risk Management         │
                    │ • Portfolio Manager       │
                    │ • Technical Indicators    │
                    │ • Notification System     │
                    │ • Logging & Monitoring    │
                    └───────────────────────────┘
```

---

## 📦 Component Architecture

### 1. **Crypto Trading Module (Custom + FreqTrade Compatible)**

**Purpose:** Handle all cryptocurrency trading operations with flexible implementation options.

**Implementation Options:**

#### Option A: Custom CryptoBot (Current Implementation - Phases 2-3)
```python
core/crypto_bot.py          # Custom crypto trading bot
cryptobot/strategies/       # Custom strategy implementations
cryptobot/data/            # Mock data generators
```

**Features:**
- Lightweight custom implementation
- Integrated with shared risk management (Phase 4)
- Works with Phase 8 exchange connectors
- RSI, MA Crossover, and custom strategies
- Full integration with portfolio manager

#### Option B: FreqTrade Integration (Optional - Available)
**Components:**
- **FreqTrade Core:** Battle-tested trading engine (install via pip)
- **Strategy Layer:** Use FreqTrade's extensive strategy library
- **Exchange Connectors:** Via CCXT library (100+ exchanges)
- **Data Provider:** Real-time and historical crypto market data

**Key Features:**
- Pre-built strategy templates
- Hyperparameter optimization
- Built-in backtesting
- Paper trading mode
- Telegram bot integration
- Large community support

**Installation:**
```bash
pip install freqtrade ccxt
```

**Both implementations:**
- Use the same shared risk management (Phase 4)
- Connect to the same portfolio manager
- Support the same exchanges (Binance, Coinbase, etc.)
- Integrate with notification system (Phase 5)

---

### 2. **Stock Trading Module (Custom Implementation)**

**Purpose:** Provide stock trading capabilities mirroring FreqTrade's architecture.

**Components:**

#### 2.1 **Exchange Layer**
```python
stockbot/exchange/
├── base_exchange.py      # Abstract exchange interface
├── alpaca_exchange.py    # Alpaca implementation
└── ib_exchange.py        # Interactive Brokers (future)
```

**Responsibilities:**
- Connect to broker APIs (Alpaca, IBKR)
- Fetch market data (quotes, bars, fundamentals)
- Execute orders (market, limit, stop)
- Manage positions and account info

#### 2.2 **Strategy Layer**
```python
stockbot/strategies/
├── base_strategy.py      # Abstract strategy class
├── rsi_strategy.py       # RSI mean reversion
├── ma_crossover.py       # Moving average crossover
└── momentum_strategy.py  # Momentum-based
```

**Strategy Interface:**
```python
class BaseStrategy:
    def populate_indicators(df: DataFrame) -> DataFrame
    def entry_signal(df: DataFrame) -> bool
    def exit_signal(df: DataFrame) -> bool
    def confirm_trade(df: DataFrame) -> bool
```

#### 2.3 **Order Manager**
```python
stockbot/order_manager.py
```
- Order validation
- Position tracking
- Partial fill handling
- Order state management

---

### 3. **Shared Components**

#### 3.1 **Risk Management System**
```python
shared/risk_management/
├── position_sizer.py     # Calculate position sizes
├── stop_loss_manager.py  # Dynamic stop losses
├── portfolio_limits.py   # Portfolio-level limits
└── risk_calculator.py    # Risk metrics
```

**Key Features:**
- **Position Sizing:** Never risk more than 1-2% per trade
- **Stop Loss:** Automatic trailing stops, ATR-based stops
- **Portfolio Limits:** Max positions, sector exposure, correlation limits
- **Risk Metrics:** Sharpe ratio, max drawdown, win rate

**Position Sizing Formula:**
```python
position_size = (account_size * risk_percent) / (entry_price - stop_loss_price)
# Constrained by:
# - Max position size (e.g., 10% of portfolio)
# - Available capital
# - Exchange limits
```

#### 3.2 **Portfolio Manager**
```python
shared/portfolio/
├── manager.py            # Unified portfolio view
├── performance.py        # Track P&L, metrics
└── rebalancer.py         # Portfolio rebalancing
```

**Features:**
- Cross-asset portfolio view (crypto + stocks)
- Real-time P&L tracking
- Performance analytics
- Asset allocation management
- Rebalancing logic

#### 3.3 **Technical Indicators**
```python
shared/indicators/
├── trend.py              # MA, EMA, MACD
├── momentum.py           # RSI, Stochastic, ROC
├── volatility.py         # Bollinger Bands, ATR
└── volume.py             # Volume indicators
```

Uses `pandas-ta` or `ta-lib` as foundation, with custom wrappers.

#### 3.4 **Notification System**
```python
shared/notifications/
├── telegram_notifier.py  # Telegram alerts
├── email_notifier.py     # Email alerts
└── webhook_notifier.py   # Custom webhooks
```

**Alert Types:**
- Trade execution (entry/exit)
- Error notifications
- Daily performance summary
- Risk limit breaches

---

### 4. **Configuration Management**

```python
config/
├── config.yaml           # Main configuration
├── exchanges.yaml        # Exchange API credentials
├── strategies.yaml       # Strategy parameters
└── risk.yaml             # Risk parameters
```

**Configuration Structure:**
```yaml
# config.yaml
trading:
  mode: paper  # paper, live
  crypto_enabled: true
  stocks_enabled: true

portfolio:
  initial_capital: 10000
  max_positions: 5

risk:
  max_risk_per_trade: 0.02  # 2%
  max_portfolio_risk: 0.10   # 10%
  max_drawdown: 0.15         # 15%

crypto:
  exchanges:
    - binance
    - coinbase
  strategies:
    - rsi_bb_strategy

stocks:
  broker: alpaca
  market: us_equity
  strategies:
    - momentum_strategy
```

---

### 5. **Backtesting Framework**

```python
backtest/
├── engine.py             # Backtesting engine
├── data_loader.py        # Historical data loader
├── metrics.py            # Performance metrics
└── visualizer.py         # Plot results
```

**Features:**
- Historical data replay
- Strategy performance evaluation
- Multiple timeframe testing
- Walk-forward analysis
- Monte Carlo simulation

---

### 6. **Monitoring & Logging**

```python
monitoring/
├── logger.py             # Centralized logging
├── metrics_collector.py  # System metrics
└── dashboard.py          # Web dashboard (Streamlit)
```

**Logging Levels:**
- **DEBUG:** Detailed execution flow
- **INFO:** Trade signals, orders, fills
- **WARNING:** Risk warnings, API issues
- **ERROR:** Execution failures, exceptions
- **CRITICAL:** System failures

---

## 🔄 Data Flow Architecture

### Trade Execution Flow

```
1. MARKET DATA
   ├─> Crypto Exchange (Binance/Coinbase)
   └─> Stock Broker (Alpaca)
        │
        ▼
2. STRATEGY ENGINE
   ├─> Calculate Indicators (RSI, MACD, etc.)
   ├─> Generate Signals (Entry/Exit)
   └─> Confirm Trade
        │
        ▼
3. RISK MANAGEMENT
   ├─> Check Portfolio Limits
   ├─> Calculate Position Size
   └─> Set Stop Loss / Take Profit
        │
        ▼
4. ORDER EXECUTION
   ├─> Create Order
   ├─> Submit to Exchange/Broker
   └─> Monitor Fill Status
        │
        ▼
5. POSITION MANAGEMENT
   ├─> Update Portfolio
   ├─> Monitor Stop Loss
   └─> Track P&L
        │
        ▼
6. NOTIFICATION & LOGGING
   ├─> Send Trade Alert
   ├─> Log Trade Details
   └─> Update Dashboard
```

---

## 🔐 Security Architecture

### API Key Management
```python
# .env file (NEVER commit to git)
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=xxx
ALPACA_API_KEY=xxx
ALPACA_API_SECRET=xxx
TELEGRAM_BOT_TOKEN=xxx
```

### Security Measures:
1. **Environment Variables:** All secrets in `.env`
2. **Read-Only Keys:** Use read-only API keys for monitoring
3. **IP Whitelist:** Restrict API access by IP
4. **2FA:** Enable on all exchange accounts
5. **Withdrawal Protection:** Disable withdrawals via API
6. **Encrypted Storage:** Encrypt sensitive config files

---

## 📊 Database Schema (Optional - Phase 2)

For persistence (SQLite initially, PostgreSQL for production):

```sql
-- Trades table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    asset_type VARCHAR(10),  -- 'crypto' or 'stock'
    symbol VARCHAR(20),
    side VARCHAR(10),        -- 'buy' or 'sell'
    quantity DECIMAL,
    price DECIMAL,
    fee DECIMAL,
    pnl DECIMAL,
    strategy VARCHAR(50),
    notes TEXT
);

-- Portfolio snapshots
CREATE TABLE portfolio_snapshots (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    total_value DECIMAL,
    cash DECIMAL,
    positions JSON,
    metrics JSON
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY,
    date DATE,
    daily_return DECIMAL,
    cumulative_return DECIMAL,
    sharpe_ratio DECIMAL,
    max_drawdown DECIMAL
);
```

---

## 🚀 Deployment Architecture

### Development Environment
```
Local Machine
├─> Python 3.10+
├─> Virtual Environment
└─> SQLite Database
```

### Production Environment (Future)
```
Cloud VPS (AWS EC2 / DigitalOcean)
├─> Docker Containers
├─> PostgreSQL Database
├─> Redis Cache
├─> Nginx Reverse Proxy
└─> Systemd Service
```

### Docker Architecture
```yaml
version: '3.8'
services:
  crypto-bot:
    build: ./freqtrade
    environment:
      - MODE=live

  stock-bot:
    build: ./stockbot
    environment:
      - MODE=live

  dashboard:
    build: ./dashboard
    ports:
      - "8501:8501"

  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
```

---

## 📈 Technology Stack

### Core Technologies
- **Language:** Python 3.10+
- **Crypto Trading:** FreqTrade (as dependency)
- **Crypto Exchanges:** CCXT library
- **Stock Trading:** Alpaca Trade API
- **Technical Analysis:** pandas-ta, TA-Lib
- **Data Processing:** Pandas, NumPy
- **Backtesting:** Custom engine + FreqTrade backtest
- **Web Framework:** Flask/FastAPI
- **Dashboard:** Streamlit
- **Notifications:** python-telegram-bot
- **Configuration:** PyYAML, python-dotenv
- **Logging:** Python logging module
- **Testing:** pytest, unittest
- **Database:** SQLite (dev), PostgreSQL (prod)
- **Task Queue:** Celery (optional)
- **Caching:** Redis (optional)

### External APIs
- **Crypto:** Binance, Coinbase Pro, Kraken
- **Stocks:** Alpaca, Interactive Brokers
- **Market Data:** Yahoo Finance (free), Alpha Vantage

---

## 🔄 State Management

### Application States
```python
class TradingMode(Enum):
    BACKTEST = "backtest"    # Testing on historical data
    PAPER = "paper"          # Simulated trading
    LIVE = "live"            # Real money trading

class BotState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
```

### Position State Machine
```
[NO_POSITION]
    ├─> Entry Signal + Risk Check Pass
    └─> [PENDING_ENTRY]
            ├─> Order Filled
            └─> [POSITION_OPEN]
                    ├─> Exit Signal / Stop Loss Hit
                    └─> [PENDING_EXIT]
                            ├─> Order Filled
                            └─> [NO_POSITION]
```

---

## 🧪 Testing Strategy

### Unit Tests
- Risk calculations
- Position sizing
- Indicator calculations
- Order validation

### Integration Tests
- Exchange connectivity
- Strategy execution
- Database operations
- Notification system

### Backtesting
- Strategy performance on historical data
- Edge case handling
- Extreme market conditions

### Paper Trading
- Live market conditions
- Order execution flow
- System stability
- 30-day minimum before live trading

---

## 🎯 Success Metrics

### System Metrics
- Uptime > 99%
- Order execution < 500ms
- API response time < 100ms
- Zero data loss

### Trading Metrics
- Win rate > 50%
- Average risk/reward > 1.5:1
- Max drawdown < 15%
- Sharpe ratio > 1.0
- Monthly return target: 2-5%

---

## 🚨 Risk Management Rules (CRITICAL)

### Portfolio Level
1. **Max Risk Per Trade:** 1-2% of portfolio
2. **Max Open Positions:** 5 concurrent positions
3. **Max Daily Loss:** 5% of portfolio
4. **Max Drawdown:** 15% (auto-stop trading)
5. **Max Leverage:** None (cash account only)

### Trade Level
1. **Stop Loss:** Mandatory on every trade
2. **Position Size:** Never exceed 10% of portfolio per position
3. **Correlation Check:** Avoid highly correlated positions
4. **Market Hours:** Only trade during liquid hours

### Emergency Controls
1. **Kill Switch:** Manual emergency stop
2. **Auto-Pause:** On consecutive losses (3 in a row)
3. **API Rate Limits:** Respect exchange limits
4. **Error Handling:** Fail-safe defaults

---

## 📝 Development Principles

1. **Safety First:** Paper trade extensively before live
2. **Fail-Safe:** Default to closing positions on errors
3. **Idempotency:** Operations should be repeatable
4. **Observability:** Log everything
5. **Testing:** Test-driven development
6. **Documentation:** Keep docs updated
7. **Version Control:** Commit often, meaningful messages
8. **Code Review:** Review all strategy changes

---

## 🗺️ Future Enhancements (Phase 2+)

1. **Machine Learning:**
   - Integrate FreqAI for crypto
   - Build ML models for stock prediction
   - Sentiment analysis from news/Twitter

2. **Advanced Features:**
   - Multi-timeframe analysis
   - Portfolio optimization
   - Options trading
   - Forex support

3. **Infrastructure:**
   - High-availability deployment
   - Load balancing
   - Auto-scaling
   - Advanced monitoring (Grafana, Prometheus)

4. **Analytics:**
   - Advanced portfolio analytics
   - Attribution analysis
   - Tax reporting
   - Compliance tracking

---

This architecture provides a solid foundation for a personal trading system that can scale from paper trading to live trading with confidence.
