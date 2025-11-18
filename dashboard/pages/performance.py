"""
Performance Analytics Page

Detailed performance metrics and analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np


def show():
    """Display performance analytics page"""

    st.markdown('<p class="main-header">📈 Performance Analytics</p>', unsafe_allow_html=True)

    # Time period selector
    col1, col2 = st.columns([3, 1])

    with col1:
        time_period = st.selectbox(
            "Select Time Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Year to Date", "All Time"]
        )

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Key Performance Indicators
    show_kpis()

    st.markdown("---")

    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Returns Analysis",
        "📉 Risk Metrics",
        "📈 Strategy Performance",
        "🎯 Trade Analytics"
    ])

    with tab1:
        show_returns_analysis()

    with tab2:
        show_risk_metrics()

    with tab3:
        show_strategy_performance()

    with tab4:
        show_trade_analytics()


def show_kpis():
    """Display key performance indicators"""

    st.subheader("Key Performance Indicators")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Return", "+2.51%", delta="+$250.50")

    with col2:
        st.metric("CAGR", "+15.2%", delta="Annualized")

    with col3:
        st.metric("Sharpe Ratio", "1.85", delta="Excellent")

    with col4:
        st.metric("Sortino Ratio", "2.45", delta="Strong")

    with col5:
        st.metric("Max Drawdown", "-8.2%", delta="Low")

    with col6:
        st.metric("Calmar Ratio", "1.85", delta="Good")


def show_returns_analysis():
    """Display returns analysis"""

    st.subheader("Returns Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Cumulative Returns**")

        # Generate mock cumulative returns
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        returns = np.random.randn(90).cumsum() * 0.005 + 0.025

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=returns * 100,
            mode='lines',
            name='Portfolio',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))

        # Add benchmark (mock)
        benchmark_returns = np.random.randn(90).cumsum() * 0.003 + 0.015
        fig.add_trace(go.Scatter(
            x=dates,
            y=benchmark_returns * 100,
            mode='lines',
            name='Benchmark (S&P 500)',
            line=dict(color='gray', width=1, dash='dash')
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Daily Returns Distribution**")

        # Generate mock daily returns
        daily_returns = np.random.randn(90) * 0.02

        fig = go.Figure(data=[go.Histogram(
            x=daily_returns * 100,
            nbinsx=30,
            marker_color='#1f77b4',
            opacity=0.7
        )])

        fig.add_vline(x=0, line_dash="dash", line_color="red",
                     annotation_text="Break-even")

        fig.update_layout(
            height=400,
            xaxis_title="Daily Return (%)",
            yaxis_title="Frequency",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Monthly returns heatmap
    st.write("**Monthly Returns Heatmap**")

    # Generate mock monthly returns
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_returns = np.random.randn(12) * 3 + 1

    fig = go.Figure(data=go.Bar(
        x=months,
        y=monthly_returns,
        marker_color=['green' if x > 0 else 'red' for x in monthly_returns],
        text=[f'{x:.1f}%' for x in monthly_returns],
        textposition='outside'
    ))

    fig.update_layout(
        height=300,
        xaxis_title="Month",
        yaxis_title="Return (%)",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def show_risk_metrics():
    """Display risk metrics"""

    st.subheader("Risk Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Drawdown Analysis**")

        # Generate mock drawdown data
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        equity = np.random.randn(90).cumsum() * 50 + 10000
        running_max = pd.Series(equity).expanding().max()
        drawdown = (equity - running_max) / running_max * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=drawdown,
            mode='lines',
            name='Drawdown',
            line=dict(color='red', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.1)'
        ))

        fig.add_hline(y=-8.2, line_dash="dash", line_color="darkred",
                     annotation_text="Max Drawdown (-8.2%)")

        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Volatility Analysis**")

        # Generate mock volatility
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        volatility = np.random.uniform(0.01, 0.03, 30)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=volatility * 100,
            mode='lines+markers',
            name='30-Day Volatility',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=6)
        ))

        fig.add_hline(y=np.mean(volatility) * 100, line_dash="dash",
                     line_color="gray",
                     annotation_text="Average")

        fig.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Volatility (%)",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Risk metrics table
    st.write("**Risk Metrics Summary**")

    risk_metrics = pd.DataFrame({
        'Metric': [
            'Annualized Volatility',
            'Downside Deviation',
            'Value at Risk (95%)',
            'Conditional VaR (95%)',
            'Beta (vs S&P 500)',
            'Maximum Drawdown',
            'Average Drawdown',
            'Recovery Factor'
        ],
        'Value': [
            '18.5%',
            '12.3%',
            '-2.8%',
            '-4.2%',
            '0.85',
            '-8.2%',
            '-3.1%',
            '3.06'
        ],
        'Assessment': [
            'Moderate',
            'Low',
            'Acceptable',
            'Good',
            'Lower risk',
            'Excellent',
            'Low',
            'Good'
        ]
    })

    st.dataframe(risk_metrics, use_container_width=True, hide_index=True)


def show_strategy_performance():
    """Display strategy performance comparison"""

    st.subheader("Strategy Performance Comparison")

    # Mock strategy performance data
    strategies = pd.DataFrame({
        'Strategy': ['RSI', 'MA Crossover', 'Momentum'],
        'Total Trades': [45, 32, 28],
        'Win Rate': [65.5, 56.2, 71.4],
        'Avg Profit': [1.85, 2.12, 2.45],
        'Avg Loss': [-1.20, -1.45, -1.10],
        'Profit Factor': [2.3, 1.9, 2.8],
        'Sharpe Ratio': [1.85, 1.42, 2.10],
        'Max Drawdown': [-6.5, -9.2, -5.8]
    })

    # Strategy comparison metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Win Rate by Strategy**")
        fig = go.Figure(data=[go.Bar(
            x=strategies['Strategy'],
            y=strategies['Win Rate'],
            marker_color='#1f77b4',
            text=[f'{x:.1f}%' for x in strategies['Win Rate']],
            textposition='outside'
        )])
        fig.update_layout(height=300, yaxis_title="Win Rate (%)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Profit Factor**")
        fig = go.Figure(data=[go.Bar(
            x=strategies['Strategy'],
            y=strategies['Profit Factor'],
            marker_color='#2ca02c',
            text=[f'{x:.2f}' for x in strategies['Profit Factor']],
            textposition='outside'
        )])
        fig.update_layout(height=300, yaxis_title="Profit Factor", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.write("**Sharpe Ratio**")
        fig = go.Figure(data=[go.Bar(
            x=strategies['Strategy'],
            y=strategies['Sharpe Ratio'],
            marker_color='#ff7f0e',
            text=[f'{x:.2f}' for x in strategies['Sharpe Ratio']],
            textposition='outside'
        )])
        fig.update_layout(height=300, yaxis_title="Sharpe Ratio", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detailed strategy table
    st.write("**Detailed Strategy Metrics**")

    styled_strategies = strategies.style.format({
        'Win Rate': '{:.1f}%',
        'Avg Profit': '{:.2f}%',
        'Avg Loss': '{:.2f}%',
        'Profit Factor': '{:.2f}',
        'Sharpe Ratio': '{:.2f}',
        'Max Drawdown': '{:.1f}%'
    })

    st.dataframe(styled_strategies, use_container_width=True, hide_index=True)


def show_trade_analytics():
    """Display trade analytics"""

    st.subheader("Trade Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Profit/Loss Distribution**")

        # Mock P&L distribution
        pnl_data = np.random.randn(100) * 50 + 10

        fig = go.Figure(data=[go.Histogram(
            x=pnl_data,
            nbinsx=30,
            marker_color=['green' if x > 0 else 'red' for x in pnl_data],
            opacity=0.7
        )])

        fig.add_vline(x=0, line_dash="dash", line_color="black",
                     annotation_text="Break-even")

        fig.update_layout(
            height=400,
            xaxis_title="P&L ($)",
            yaxis_title="Number of Trades",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Trade Duration Analysis**")

        # Mock duration data
        duration_labels = ['< 1h', '1-4h', '4-12h', '12-24h', '1-3d', '> 3d']
        duration_counts = [5, 15, 25, 20, 15, 10]

        fig = go.Figure(data=[go.Pie(
            labels=duration_labels,
            values=duration_counts,
            hole=0.4
        )])

        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Trade analytics summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Best Trade", "+$285.50", delta="+5.7%")

    with col2:
        st.metric("Worst Trade", "-$125.00", delta="-2.5%")

    with col3:
        st.metric("Avg Win", "+$62.40", delta="+2.1%")

    with col4:
        st.metric("Avg Loss", "-$38.20", delta="-1.3%")

    st.markdown("---")

    # Win/Loss streaks
    st.write("**Consecutive Wins/Losses**")

    streak_data = pd.DataFrame({
        'Type': ['Longest Win Streak', 'Longest Loss Streak', 'Current Streak'],
        'Count': [7, 3, 4],
        'Status': ['✅ Wins', '❌ Losses', '✅ Wins']
    })

    st.dataframe(streak_data, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    show()
