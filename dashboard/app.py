"""
TradeAgent Dashboard

Streamlit-based web dashboard for monitoring trading operations
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="TradeAgent Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .profit {
        color: #00c853;
        font-weight: bold;
    }
    .loss {
        color: #d32f2f;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=TradeAgent",
             use_column_width=True)

    st.title("TradeAgent")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["📊 Overview", "💼 Positions & Trades", "📈 Performance", "⚠️ Risk Management"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Status indicators
    st.subheader("System Status")

    # Trading status (mock data for now)
    trading_active = st.checkbox("Trading Active", value=True, disabled=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Crypto Bot", "●", delta="Online", delta_color="normal")
    with col2:
        st.metric("Stock Bot", "●", delta="Online", delta_color="normal")

    st.markdown("---")

    # Quick stats
    st.subheader("Quick Stats")
    st.metric("Portfolio Value", "$10,000")
    st.metric("Today's P&L", "+$250", delta="+2.5%")
    st.metric("Open Positions", "3")

    st.markdown("---")

    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# Main content area
if "📊 Overview" in page:
    from pages import overview
    overview.show()
elif "💼 Positions" in page:
    from pages import positions
    positions.show()
elif "📈 Performance" in page:
    from pages import performance
    performance.show()
elif "⚠️ Risk" in page:
    from pages import risk
    risk.show()
