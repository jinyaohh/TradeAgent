"""
Risk Management Page

Risk monitoring and control panel
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np


def show():
    """Display risk management page"""

    st.markdown('<p class="main-header">⚠️ Risk Management</p>', unsafe_allow_html=True)

    # Risk level indicator
    show_risk_status()

    st.markdown("---")

    # Tabs for different risk views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Position Limits",
        "📊 Portfolio Limits",
        "🚨 Emergency Controls",
        "📈 Risk Metrics"
    ])

    with tab1:
        show_position_limits()

    with tab2:
        show_portfolio_limits()

    with tab3:
        show_emergency_controls()

    with tab4:
        show_risk_metrics_detail()


def show_risk_status():
    """Display overall risk status"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Overall risk level
        risk_level = "LOW"  # Mock data
        color = "green" if risk_level == "LOW" else "orange" if risk_level == "MODERATE" else "red"

        st.markdown(f"### Overall Risk Level")
        st.markdown(f"<h1 style='color:{color};text-align:center'>{risk_level}</h1>",
                   unsafe_allow_html=True)

    with col2:
        st.metric("Trading Status", "ACTIVE", delta="✅ Online")

    with col3:
        st.metric("Circuit Breakers", "0 Active", delta="✅ Normal")

    with col4:
        st.metric("Risk Violations", "0", delta="✅ Healthy")


def show_position_limits():
    """Display position-level limits"""

    st.subheader("Position Limits & Constraints")

    # Current vs Limits
    limits_data = pd.DataFrame({
        'Limit Type': [
            'Max Position Size',
            'Max Single Asset',
            'Max Positions',
            'Min Cash Reserve'
        ],
        'Current': ['10.2%', '18.5%', '4', '34.1%'],
        'Limit': ['20.0%', '30.0%', '10', '10.0%'],
        'Usage': [51, 62, 40, 0],
        'Status': ['✅ OK', '✅ OK', '✅ OK', '✅ OK']
    })

    st.dataframe(limits_data, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Visual representation
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Position Size Usage**")

        # Mock position sizes
        positions = ['BTC/USDT', 'ETH/USDT', 'AAPL', 'GOOGL']
        sizes = [18.5, 16.2, 10.2, 7.1]
        max_size = 20.0

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=positions,
            x=sizes,
            orientation='h',
            marker_color=['green' if s < max_size * 0.8 else 'orange' for s in sizes],
            text=[f'{s}%' for s in sizes],
            textposition='outside'
        ))

        fig.add_vline(x=max_size, line_dash="dash", line_color="red",
                     annotation_text=f"Max: {max_size}%")

        fig.update_layout(
            height=300,
            xaxis_title="Position Size (% of Portfolio)",
            yaxis_title="Symbol",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Position Count Status**")

        # Gauge chart for position count
        current_positions = 4
        max_positions = 10

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_positions,
            delta={'reference': max_positions},
            gauge={
                'axis': {'range': [None, max_positions]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_positions * 0.5], 'color': "lightgreen"},
                    {'range': [max_positions * 0.5, max_positions * 0.8], 'color': "yellow"},
                    {'range': [max_positions * 0.8, max_positions], 'color': "salmon"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_positions
                }
            },
            title={'text': "Open Positions"}
        ))

        fig.update_layout(height=300)

        st.plotly_chart(fig, use_container_width=True)


def show_portfolio_limits():
    """Display portfolio-level limits"""

    st.subheader("Portfolio-Level Risk Limits")

    # Portfolio limits status
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Daily Loss Limit", "-2.1%", delta="3.9% buffer", delta_color="normal")
        st.progress(42, text="42% of daily limit used")

    with col2:
        st.metric("Max Drawdown", "-5.8%", delta="9.2% buffer", delta_color="normal")
        st.progress(39, text="39% of max drawdown")

    with col3:
        st.metric("Portfolio Leverage", "1.0x", delta="No leverage", delta_color="normal")
        st.progress(0, text="0% leverage used")

    st.markdown("---")

    # Asset allocation vs limits
    st.write("**Asset Class Allocation vs Limits**")

    allocation_data = pd.DataFrame({
        'Asset Class': ['Cash', 'Crypto', 'Stocks', 'Total Invested'],
        'Current %': [34.1, 39.0, 26.9, 65.9],
        'Limit %': [10.0, 50.0, 80.0, 90.0],
        'Status': ['✅', '✅', '✅', '✅']
    })

    # Create grouped bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Current',
        x=allocation_data['Asset Class'],
        y=allocation_data['Current %'],
        marker_color='#1f77b4',
        text=[f'{x:.1f}%' for x in allocation_data['Current %']],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='Limit',
        x=allocation_data['Asset Class'],
        y=allocation_data['Limit %'],
        marker_color='lightgray',
        opacity=0.5
    ))

    fig.update_layout(
        height=400,
        xaxis_title="Asset Class",
        yaxis_title="Allocation (%)",
        barmode='overlay',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Concentration risk
    st.write("**Concentration Risk Analysis**")

    concentration = pd.DataFrame({
        'Type': ['Single Position', 'Single Symbol', 'Crypto Exposure', 'Stock Exposure'],
        'Current': ['18.5%', '18.5%', '39.0%', '26.9%'],
        'Max Allowed': ['20.0%', '30.0%', '50.0%', '80.0%'],
        'Risk Level': ['Moderate', 'Low', 'Low', 'Low']
    })

    st.dataframe(concentration, use_container_width=True, hide_index=True)


def show_emergency_controls():
    """Display emergency controls"""

    st.subheader("🚨 Emergency Controls & Circuit Breakers")

    # Trading controls
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Trading Status**")

        trading_active = True  # Mock status

        if trading_active:
            st.success("✅ Trading is ACTIVE")

            if st.button("⏸️ Pause Trading", type="secondary", use_container_width=True):
                st.warning("Trading would be paused (demo mode)")

            if st.button("🚨 EMERGENCY STOP", type="primary", use_container_width=True):
                st.error("Emergency stop would be activated (demo mode)")
        else:
            st.warning("⏸️ Trading is PAUSED")

            if st.button("▶️ Resume Trading", type="primary", use_container_width=True):
                st.success("Trading would resume (demo mode)")

    with col2:
        st.write("**Emergency Actions**")

        if st.button("💰 Close All Losing Positions", use_container_width=True):
            st.info("Would close all losing positions (demo mode)")

        if st.button("🔒 Close All Positions", use_container_width=True):
            st.warning("Would close ALL positions (demo mode)")

        if st.button("🔄 Reset Daily Limits", use_container_width=True):
            st.info("Would reset daily tracking (demo mode)")

    st.markdown("---")

    # Circuit breakers status
    st.write("**Circuit Breaker Status**")

    breakers = pd.DataFrame({
        'Circuit Breaker': [
            'Daily Loss Limit (-5%)',
            'Max Drawdown (-15%)',
            'Rapid Loss (-3% in 1h)',
            'Portfolio Correlation (>0.8)'
        ],
        'Current Value': ['-2.1%', '-5.8%', '-0.8%', '0.42'],
        'Threshold': ['-5.0%', '-15.0%', '-3.0%', '0.80'],
        'Status': ['✅ OK', '✅ OK', '✅ OK', '✅ OK'],
        'Activated': ['Never', 'Never', 'Never', 'Never']
    })

    st.dataframe(breakers, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Recent events
    st.write("**Recent Risk Events**")

    events = pd.DataFrame({
        'Time': ['2 hours ago', '5 hours ago', 'Yesterday'],
        'Event': ['Position Opened', 'Daily Limit Reset', 'Position Closed'],
        'Details': ['BTC/USDT opened at $52,000', 'Daily tracking reset to $0', 'AAPL closed with +2.5% profit'],
        'Severity': ['Info', 'Info', 'Info']
    })

    st.dataframe(events, use_container_width=True, hide_index=True)


def show_risk_metrics_detail():
    """Display detailed risk metrics"""

    st.subheader("Detailed Risk Metrics")

    # Risk metrics overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Value at Risk (VaR)**")
        st.metric("Daily VaR (95%)", "-$285", delta="-2.8% of portfolio")
        st.metric("Weekly VaR (95%)", "-$650", delta="-6.3% of portfolio")

    with col2:
        st.write("**Risk-Adjusted Returns**")
        st.metric("Sharpe Ratio", "1.85", delta="Excellent")
        st.metric("Sortino Ratio", "2.45", delta="Strong")

    with col3:
        st.write("**Volatility Metrics**")
        st.metric("Portfolio Volatility", "18.5%", delta="Annualized")
        st.metric("Downside Deviation", "12.3%", delta="Lower is better")

    st.markdown("---")

    # Risk contribution by position
    st.write("**Risk Contribution by Position**")

    risk_contribution = pd.DataFrame({
        'Symbol': ['BTC/USDT', 'ETH/USDT', 'AAPL', 'GOOGL'],
        'Position Size': ['18.5%', '16.2%', '10.2%', '7.1%'],
        'Volatility': ['45.2%', '52.1%', '22.5%', '28.3%'],
        'VaR Contribution': ['38.5%', '35.2%', '15.8%', '10.5%'],
        'Beta': [1.25, 1.35, 0.95, 1.05]
    })

    st.dataframe(risk_contribution, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Correlation matrix
    st.write("**Position Correlation Matrix**")

    # Mock correlation data
    symbols = ['BTC/USDT', 'ETH/USDT', 'AAPL', 'GOOGL']
    correlation = np.array([
        [1.00, 0.85, 0.32, 0.28],
        [0.85, 1.00, 0.38, 0.35],
        [0.32, 0.38, 1.00, 0.75],
        [0.28, 0.35, 0.75, 1.00]
    ])

    fig = go.Figure(data=go.Heatmap(
        z=correlation,
        x=symbols,
        y=symbols,
        colorscale='RdYlGn_r',
        zmid=0,
        text=correlation,
        texttemplate='%{text:.2f}',
        textfont={"size": 12},
        colorbar=dict(title="Correlation")
    ))

    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)

    st.info("💡 High correlation (>0.7) between positions increases portfolio risk. Consider diversification.")


if __name__ == "__main__":
    show()
