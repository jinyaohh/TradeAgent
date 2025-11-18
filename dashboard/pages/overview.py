"""
Overview Page

Main dashboard page showing portfolio overview and key metrics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np


def show():
    """Display overview page"""

    st.markdown('<p class="main-header">📊 Portfolio Overview</p>', unsafe_allow_html=True)

    # Mock data generation (will be replaced with real data later)
    portfolio_value = 10250.50
    initial_capital = 10000.00
    total_pnl = portfolio_value - initial_capital
    total_pnl_pct = (portfolio_value - initial_capital) / initial_capital

    cash = 3500.00
    positions_value = portfolio_value - cash

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Portfolio Value",
            value=f"${portfolio_value:,.2f}",
            delta=f"${total_pnl:,.2f} ({total_pnl_pct:.2%})"
        )

    with col2:
        st.metric(
            label="Cash Available",
            value=f"${cash:,.2f}",
            delta=f"{(cash/portfolio_value):.1%} of portfolio"
        )

    with col3:
        st.metric(
            label="Positions Value",
            value=f"${positions_value:,.2f}",
            delta=f"{(positions_value/portfolio_value):.1%} invested"
        )

    with col4:
        st.metric(
            label="Today's P&L",
            value="+$125.50",
            delta="+1.23%"
        )

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Equity Curve (Last 30 Days)")

        # Generate mock equity curve
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        equity = np.random.randn(30).cumsum() * 50 + 10000
        equity_df = pd.DataFrame({'Date': dates, 'Value': equity})

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=equity_df['Date'],
            y=equity_df['Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))

        fig.add_hline(y=initial_capital, line_dash="dash", line_color="gray",
                     annotation_text="Initial Capital")

        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode='x unified',
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🥧 Asset Allocation")

        # Mock allocation data
        allocation_data = pd.DataFrame({
            'Asset Class': ['Cash', 'Crypto', 'Stocks'],
            'Value': [cash, 4000, 2750.50],
            'Percentage': [34.1, 39.0, 26.9]
        })

        fig = go.Figure(data=[go.Pie(
            labels=allocation_data['Asset Class'],
            values=allocation_data['Value'],
            hole=0.4,
            marker=dict(colors=['#90caf9', '#ffb74d', '#81c784']),
            textinfo='label+percent',
            textfont_size=14
        )])

        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Open Positions Summary
    st.subheader("💼 Open Positions")

    # Mock positions data
    positions = pd.DataFrame({
        'Symbol': ['BTC/USDT', 'ETH/USDT', 'AAPL'],
        'Type': ['Crypto', 'Crypto', 'Stock'],
        'Quantity': [0.08, 1.2, 15],
        'Entry Price': [50000.00, 3000.00, 150.00],
        'Current Price': [52000.00, 3100.00, 152.50],
        'Value': [4160.00, 3720.00, 2287.50],
        'P&L': [160.00, 120.00, 37.50],
        'P&L %': [4.00, 4.00, 1.67]
    })

    # Format the dataframe
    def color_pnl(val):
        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {color}'

    styled_positions = positions.style.format({
        'Quantity': '{:.4f}',
        'Entry Price': '${:,.2f}',
        'Current Price': '${:,.2f}',
        'Value': '${:,.2f}',
        'P&L': '${:,.2f}',
        'P&L %': '{:.2f}%'
    }).applymap(color_pnl, subset=['P&L', 'P&L %'])

    st.dataframe(styled_positions, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Recent Activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Recent Trades")

        recent_trades = pd.DataFrame({
            'Time': ['10:30 AM', '09:15 AM', 'Yesterday'],
            'Symbol': ['BTC/USDT', 'AAPL', 'ETH/USDT'],
            'Action': ['BUY', 'SELL', 'BUY'],
            'Quantity': [0.08, 10, 1.2],
            'Price': [50000.00, 148.00, 3000.00],
            'P&L': ['+$160.00', '+$20.00', '+$120.00']
        })

        st.dataframe(recent_trades, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("🔔 Recent Alerts")

        alerts = pd.DataFrame({
            'Time': ['11:45 AM', '10:35 AM', '09:20 AM'],
            'Type': ['✅ Trade', '✅ Trade', '⚠️ Warning'],
            'Message': [
                'Position opened: BTC/USDT',
                'Position closed: AAPL (+1.35%)',
                'Portfolio allocation: 65% invested'
            ]
        })

        st.dataframe(alerts, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Performance Metrics Row
    st.subheader("📊 Performance Metrics")

    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

    with metric_col1:
        st.metric("Win Rate", "62.5%", delta="↑ 2.5%")

    with metric_col2:
        st.metric("Profit Factor", "2.3", delta="Good")

    with metric_col3:
        st.metric("Sharpe Ratio", "1.8", delta="Excellent")

    with metric_col4:
        st.metric("Max Drawdown", "-8.2%", delta="Low")

    with metric_col5:
        st.metric("Avg Trade", "+$45.20", delta="+1.5%")

    st.markdown("---")

    # System Health
    st.subheader("💚 System Health")

    health_col1, health_col2, health_col3, health_col4 = st.columns(4)

    with health_col1:
        st.success("✅ Crypto Bot: Online")

    with health_col2:
        st.success("✅ Stock Bot: Online")

    with health_col3:
        st.success("✅ Risk Management: Active")

    with health_col4:
        st.info("ℹ️ Last Update: Just now")

    # Footer with last update time
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    show()
