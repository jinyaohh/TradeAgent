"""
Positions & Trades Page

Detailed view of open positions and trade history
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np


def show():
    """Display positions and trades page"""

    st.markdown('<p class="main-header">💼 Positions & Trades</p>', unsafe_allow_html=True)

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Open Positions", "📝 Trade History", "📈 Position Analysis"])

    with tab1:
        show_open_positions()

    with tab2:
        show_trade_history()

    with tab3:
        show_position_analysis()


def show_open_positions():
    """Display open positions"""

    st.subheader("Current Open Positions")

    # Mock open positions
    positions = pd.DataFrame({
        'Symbol': ['BTC/USDT', 'ETH/USDT', 'AAPL', 'GOOGL'],
        'Type': ['Crypto', 'Crypto', 'Stock', 'Stock'],
        'Side': ['LONG', 'LONG', 'LONG', 'LONG'],
        'Quantity': [0.08, 1.2, 15, 5],
        'Entry Price': [50000.00, 3000.00, 150.00, 140.00],
        'Current Price': [52000.00, 3100.00, 152.50, 142.00],
        'Stop Loss': [48500.00, 2910.00, 147.00, 136.50],
        'Take Profit': [55000.00, 3300.00, 157.50, 147.00],
        'Value': [4160.00, 3720.00, 2287.50, 710.00],
        'P&L': [160.00, 120.00, 37.50, 10.00],
        'P&L %': [4.00, 4.00, 1.67, 1.43],
        'Duration': ['2d 3h', '1d 5h', '18h', '5h']
    })

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Positions", len(positions))

    with col2:
        total_value = positions['Value'].sum()
        st.metric("Total Value", f"${total_value:,.2f}")

    with col3:
        total_pnl = positions['P&L'].sum()
        st.metric("Total P&L", f"${total_pnl:,.2f}",
                 delta=f"{(total_pnl/total_value)*100:.2f}%")

    with col4:
        winning = (positions['P&L'] > 0).sum()
        st.metric("Winning Positions", f"{winning}/{len(positions)}")

    st.markdown("---")

    # Detailed positions table
    def color_pnl(val):
        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {color}; font-weight: bold'

    styled_positions = positions.style.format({
        'Quantity': '{:.4f}',
        'Entry Price': '${:,.2f}',
        'Current Price': '${:,.2f}',
        'Stop Loss': '${:,.2f}',
        'Take Profit': '${:,.2f}',
        'Value': '${:,.2f}',
        'P&L': '${:,.2f}',
        'P&L %': '{:.2f}%'
    }).applymap(color_pnl, subset=['P&L', 'P&L %'])

    st.dataframe(styled_positions, use_container_width=True, hide_index=True, height=300)

    # Position details
    st.markdown("---")
    st.subheader("Position Details")

    selected_symbol = st.selectbox("Select Position", positions['Symbol'].tolist())
    position_detail = positions[positions['Symbol'] == selected_symbol].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Entry Information**")
        st.write(f"Symbol: {position_detail['Symbol']}")
        st.write(f"Type: {position_detail['Type']}")
        st.write(f"Side: {position_detail['Side']}")
        st.write(f"Quantity: {position_detail['Quantity']:.4f}")
        st.write(f"Entry Price: ${position_detail['Entry Price']:,.2f}")

    with col2:
        st.write("**Current Status**")
        st.write(f"Current Price: ${position_detail['Current Price']:,.2f}")
        st.write(f"Position Value: ${position_detail['Value']:,.2f}")
        pnl_color = "green" if position_detail['P&L'] > 0 else "red"
        st.markdown(f"P&L: <span style='color:{pnl_color};font-weight:bold'>${position_detail['P&L']:,.2f} ({position_detail['P&L %']:.2f}%)</span>",
                   unsafe_allow_html=True)
        st.write(f"Duration: {position_detail['Duration']}")

    with col3:
        st.write("**Risk Management**")
        st.write(f"Stop Loss: ${position_detail['Stop Loss']:,.2f}")
        stop_distance = abs(position_detail['Current Price'] - position_detail['Stop Loss'])
        st.write(f"Stop Distance: ${stop_distance:.2f}")
        st.write(f"Take Profit: ${position_detail['Take Profit']:,.2f}")
        target_distance = abs(position_detail['Take Profit'] - position_detail['Current Price'])
        st.write(f"Target Distance: ${target_distance:.2f}")


def show_trade_history():
    """Display trade history"""

    st.subheader("Trade History")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        date_range = st.selectbox("Time Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])

    with col2:
        asset_filter = st.multiselect("Asset Type", ["All", "Crypto", "Stock"], default=["All"])

    with col3:
        status_filter = st.multiselect("Result", ["All", "Profit", "Loss"], default=["All"])

    # Mock trade history
    trades = pd.DataFrame({
        'Date': pd.date_range(end=datetime.now(), periods=20, freq='6H')[::-1],
        'Symbol': np.random.choice(['BTC/USDT', 'ETH/USDT', 'AAPL', 'GOOGL', 'MSFT'], 20),
        'Type': np.random.choice(['Crypto', 'Stock'], 20),
        'Side': np.random.choice(['BUY', 'SELL'], 20),
        'Quantity': np.random.uniform(0.1, 2.0, 20),
        'Entry Price': np.random.uniform(100, 50000, 20),
        'Exit Price': np.random.uniform(100, 50000, 20),
        'P&L': np.random.uniform(-100, 200, 20),
        'P&L %': np.random.uniform(-5, 8, 20),
        'Strategy': np.random.choice(['RSI', 'MA Crossover', 'Momentum'], 20),
        'Exit Reason': np.random.choice(['Take Profit', 'Stop Loss', 'Manual'], 20)
    })

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Trades", len(trades))

    with col2:
        winning_trades = (trades['P&L'] > 0).sum()
        win_rate = winning_trades / len(trades) * 100
        st.metric("Win Rate", f"{win_rate:.1f}%")

    with col3:
        total_profit = trades[trades['P&L'] > 0]['P&L'].sum()
        st.metric("Total Profit", f"${total_profit:.2f}")

    with col4:
        total_loss = abs(trades[trades['P&L'] < 0]['P&L'].sum())
        st.metric("Total Loss", f"${total_loss:.2f}")

    with col5:
        net_pnl = trades['P&L'].sum()
        st.metric("Net P&L", f"${net_pnl:.2f}")

    st.markdown("---")

    # Trade history table
    styled_trades = trades.style.format({
        'Date': lambda x: x.strftime('%Y-%m-%d %H:%M'),
        'Quantity': '{:.4f}',
        'Entry Price': '${:,.2f}',
        'Exit Price': '${:,.2f}',
        'P&L': '${:,.2f}',
        'P&L %': '{:.2f}%'
    })

    st.dataframe(styled_trades, use_container_width=True, hide_index=True, height=400)

    # Download button
    csv = trades.to_csv(index=False)
    st.download_button(
        label="📥 Download Trade History (CSV)",
        data=csv,
        file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


def show_position_analysis():
    """Display position analysis"""

    st.subheader("Position Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**P&L Distribution by Symbol**")

        # Mock P&L by symbol
        pnl_by_symbol = pd.DataFrame({
            'Symbol': ['BTC/USDT', 'ETH/USDT', 'AAPL', 'GOOGL', 'MSFT'],
            'Total P&L': [450.00, 320.00, -120.00, 180.00, 90.00],
            'Trades': [8, 6, 5, 4, 3]
        })

        colors = ['green' if x > 0 else 'red' for x in pnl_by_symbol['Total P&L']]

        fig = go.Figure(data=[go.Bar(
            x=pnl_by_symbol['Symbol'],
            y=pnl_by_symbol['Total P&L'],
            marker_color=colors,
            text=pnl_by_symbol['Total P&L'].apply(lambda x: f'${x:.2f}'),
            textposition='outside'
        )])

        fig.update_layout(
            height=400,
            xaxis_title="Symbol",
            yaxis_title="Total P&L ($)",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Win Rate by Strategy**")

        # Mock win rate by strategy
        strategy_stats = pd.DataFrame({
            'Strategy': ['RSI', 'MA Crossover', 'Momentum'],
            'Win Rate': [65, 58, 72],
            'Trades': [15, 12, 8]
        })

        fig = go.Figure(data=[go.Bar(
            x=strategy_stats['Strategy'],
            y=strategy_stats['Win Rate'],
            marker_color='#1f77b4',
            text=strategy_stats['Win Rate'].apply(lambda x: f'{x}%'),
            textposition='outside'
        )])

        fig.update_layout(
            height=400,
            xaxis_title="Strategy",
            yaxis_title="Win Rate (%)",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Holding time analysis
    st.write("**Average Holding Time by Asset Type**")

    holding_time = pd.DataFrame({
        'Asset Type': ['Crypto', 'Stock'],
        'Avg Holding Time (hours)': [18.5, 12.3],
        'Min': [2, 1],
        'Max': [72, 48]
    })

    st.dataframe(holding_time, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    show()
