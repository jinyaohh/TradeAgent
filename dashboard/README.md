# TradeAgent Dashboard

Real-time web-based monitoring dashboard for the TradeAgent trading system.

## Features

### 📊 Overview Page
- Portfolio value and performance metrics
- Equity curve visualization (30-day)
- Asset allocation pie chart
- Open positions summary
- Recent trades and alerts
- System health indicators

### 💼 Positions & Trades Page
- **Open Positions Tab**
  - Detailed position information
  - P&L tracking
  - Stop loss and take profit levels
  - Position duration
  - Individual position drill-down

- **Trade History Tab**
  - Complete trade history
  - Filtering by date, asset type, result
  - Win rate and P&L statistics
  - CSV export functionality

- **Position Analysis Tab**
  - P&L distribution by symbol
  - Win rate by strategy
  - Holding time analysis

### 📈 Performance Analytics Page
- **Returns Analysis**
  - Cumulative returns vs benchmark
  - Daily returns distribution
  - Monthly returns heatmap

- **Risk Metrics**
  - Drawdown analysis
  - Volatility tracking
  - VaR and CVaR
  - Risk metrics summary

- **Strategy Performance**
  - Side-by-side strategy comparison
  - Win rate, profit factor, Sharpe ratio
  - Detailed strategy metrics table

- **Trade Analytics**
  - P&L distribution
  - Trade duration analysis
  - Best/worst trade tracking
  - Win/loss streak monitoring

### ⚠️ Risk Management Page
- **Position Limits**
  - Position size monitoring
  - Max positions tracker
  - Visual limit indicators

- **Portfolio Limits**
  - Daily loss limit
  - Max drawdown tracker
  - Asset allocation vs limits
  - Concentration risk analysis

- **Emergency Controls**
  - Trading pause/resume
  - Emergency stop button
  - Close positions controls
  - Circuit breaker status

- **Risk Metrics Detail**
  - Value at Risk (VaR)
  - Risk-adjusted returns
  - Position correlation matrix
  - Risk contribution by position

## Quick Start

### Prerequisites

- Python 3.10+
- TradeAgent installed (see main README)

### Installation

Dashboard dependencies are included in the main `requirements.txt`:

```bash
# Install from project root
pip install -r requirements.txt
```

### Running the Dashboard

From the project root directory:

```bash
# Start the dashboard
streamlit run dashboard/app.py
```

The dashboard will open automatically in your default web browser at `http://localhost:8501`

### Alternative Port

To run on a different port:

```bash
streamlit run dashboard/app.py --server.port 8502
```

## Configuration

The dashboard uses mock data by default for demonstration purposes. To connect to your live trading system:

1. Update `dashboard/app.py` to import your portfolio manager
2. Replace mock data with real data from your trading system
3. Configure data refresh intervals

## Usage Tips

### Navigation
- Use the sidebar radio buttons to switch between pages
- Click the 🔄 Refresh button to update data
- System status indicators show trading bot health

### Real-Time Monitoring
- Overview page provides at-a-glance portfolio health
- Risk Management page shows limit usage and violations
- Recent alerts section displays latest system events

### Performance Analysis
- Use time period selectors to analyze different timeframes
- Compare strategies on the Performance page
- Download trade history for offline analysis

### Risk Management
- Monitor position limits in real-time
- Circuit breakers activate automatically when limits are breached
- Emergency stop button for immediate trading halt

## Development

### Project Structure

```
dashboard/
├── app.py              # Main application entry point
├── pages/              # Dashboard pages
│   ├── __init__.py
│   ├── overview.py     # Portfolio overview
│   ├── positions.py    # Positions and trades
│   ├── performance.py  # Performance analytics
│   └── risk.py         # Risk management
└── README.md           # This file
```

### Adding New Pages

1. Create a new file in `dashboard/pages/`
2. Implement a `show()` function
3. Import and call in `dashboard/app.py`

Example:

```python
# dashboard/pages/new_page.py
import streamlit as st

def show():
    st.title("My New Page")
    st.write("Content here")

# dashboard/app.py
from pages import new_page

if "New Page" in page:
    new_page.show()
```

### Customizing Visualizations

The dashboard uses Plotly for interactive charts. Customize by modifying chart configurations in each page file.

## Integration with Live System

### Connecting to Portfolio Manager

To use real data instead of mock data:

```python
# In dashboard/app.py or individual pages
from shared.risk_management.portfolio_manager import PortfolioManager
from shared.risk_management.risk_monitor import RiskMonitor

# Initialize
@st.cache_resource
def init_system():
    portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
    monitor = RiskMonitor(portfolio)
    return portfolio, monitor

portfolio, monitor = init_system()

# Use real data
portfolio_metrics = portfolio.get_portfolio_metrics()
risk_report = monitor.get_risk_report()
```

### Auto-Refresh

Enable automatic data refresh:

```python
# Add to app.py
import time

# Auto-refresh every 30 seconds
st.sidebar.write("Auto-refresh enabled")
time_to_refresh = 30
time.sleep(time_to_refresh)
st.rerun()
```

## Troubleshooting

### Dashboard Won't Start

```bash
# Check Streamlit installation
streamlit --version

# Reinstall if needed
pip install --upgrade streamlit
```

### Port Already in Use

```bash
# Use a different port
streamlit run dashboard/app.py --server.port 8502
```

### Data Not Updating

- Click the 🔄 Refresh button in the sidebar
- Check that your trading system is running
- Verify data source connections

### Charts Not Displaying

```bash
# Ensure plotly is installed
pip install --upgrade plotly
```

## Screenshots

(Add screenshots here when available)

## Support

For issues or questions:
1. Check the main project README
2. Review Streamlit documentation: https://docs.streamlit.io
3. Open an issue on GitHub

## License

Same as main TradeAgent project.

---

**Note**: This dashboard currently uses mock data for demonstration. Integration with live trading data is planned for Phase 7.
