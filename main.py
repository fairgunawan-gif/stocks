import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Stock Screener - Mean Reversion & Trend Following",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📊 Technical Analysis Stock Screener")
st.markdown("""
This screener analyzes stocks using two distinct trading strategies:
- **📉 Mean Reversion**: Buys oversold dips (RSI < 30, Price < SMA20, Volume confirmation)
- **📈 Trend Following**: Buys momentum continuations (RSI > 50, Price > SMA20, SMA20 > SMA50)
""")

# Initialize session state for tickers
if 'tickers' not in st.session_state:
    # Default tickers
    st.session_state.tickers = [
        'BBCA.JK', 'BNGA.JK', 'NISP.JK', 'BMRI.JK', 'BBRI.JK', 'BBNI.JK', 'BRIS.JK', 'BBTN.JK',
        'ASII.JK', 'UNTR.JK', 'AALI.JK', 'ASGR.JK', 'AUTO.JK',
        'KLBF.JK', 'HEAL.JK', 'MIKA.JK', 'TSPC.JK', 'SIDO.JK',
        'TLKM.JK', 'INDF.JK', 'ICBP.JK'
    ]

# Sidebar - Ticker Management
st.sidebar.header("🔧 Ticker Management")

# Display current tickers
st.sidebar.subheader("Current Tickers")
current_tickers_text = st.sidebar.text_area(
    "Edit tickers (one per line):",
    value="\n".join(st.session_state.tickers),
    height=300,
    help="Add or remove tickers. Use one ticker per line."
)

# Update tickers button
if st.sidebar.button("🔄 Update Ticker List"):
    new_tickers = [t.strip().upper() for t in current_tickers_text.split('\n') if t.strip()]
    if new_tickers:
        st.session_state.tickers = new_tickers
        st.sidebar.success(f"Updated to {len(new_tickers)} tickers")
        st.rerun()
    else:
        st.sidebar.error("Please enter at least one ticker")

# Add single ticker
st.sidebar.subheader("➕ Add Single Ticker")
new_ticker = st.sidebar.text_input("Ticker symbol:", placeholder="e.g., AAPL, BBCA.JK")
if st.sidebar.button("Add Ticker"):
    if new_ticker and new_ticker.strip().upper() not in st.session_state.tickers:
        st.session_state.tickers.append(new_ticker.strip().upper())
        st.sidebar.success(f"Added {new_ticker.strip().upper()}")
        st.rerun()
    elif new_ticker and new_ticker.strip().upper() in st.session_state.tickers:
        st.sidebar.warning("Ticker already exists")
    else:
        st.sidebar.warning("Please enter a ticker")

# Remove ticker
st.sidebar.subheader("❌ Remove Ticker")
remove_ticker = st.sidebar.selectbox("Select ticker to remove:", ["None"] + st.session_state.tickers)
if st.sidebar.button("Remove Ticker") and remove_ticker != "None":
    st.session_state.tickers.remove(remove_ticker)
    st.sidebar.success(f"Removed {remove_ticker}")
    st.rerun()

# Parameters
st.sidebar.header("⚙️ Analysis Parameters")
period = st.sidebar.selectbox("Data period:", ["1y", "6mo", "3mo", "2y", "max"], index=0)
rsi_period = st.sidebar.number_input("RSI Period:", min_value=5, max_value=30, value=14)
sma_short = st.sidebar.number_input("Short SMA Period:", min_value=5, max_value=50, value=20)
sma_long = st.sidebar.number_input("Long SMA Period (Trend Following):", min_value=20, max_value=200, value=50)

# Mean Reversion parameters
st.sidebar.subheader("📉 Mean Reversion Parameters")
rsi_oversold = st.sidebar.number_input("RSI Oversold Threshold:", min_value=10, max_value=40, value=30)
volume_multiplier = st.sidebar.number_input("Volume Multiplier ( > avg):", min_value=0.5, max_value=3.0, value=1.0,
                                            step=0.1)
mr_entry_offset = st.sidebar.number_input(
    "Entry Offset (% below SMA20):",
    min_value=0.0, max_value=10.0, value=2.0, step=0.5,
    help="Recommended buy price = SMA20 minus this percentage (for better risk/reward)"
)

# Trend Following parameters
st.sidebar.subheader("📈 Trend Following Parameters")
rsi_momentum = st.sidebar.number_input("RSI Momentum Threshold:", min_value=40, max_value=70, value=50)
tf_entry_offset = st.sidebar.number_input(
    "Entry Offset (% below current price):",
    min_value=0.0, max_value=5.0, value=0.0, step=0.5,
    help="Recommended buy price = current price minus this percentage (0 = buy at market)"
)

# Stop Loss parameters
st.sidebar.subheader("🛑 Risk Management")
mr_stop_loss_pct = st.sidebar.number_input(
    "Mean Reversion Stop Loss (%):",
    min_value=1.0, max_value=15.0, value=5.0, step=0.5,
    help="Stop loss below recommended buy price"
)
tf_stop_loss_pct = st.sidebar.number_input(
    "Trend Following Stop Loss (%):",
    min_value=1.0, max_value=15.0, value=7.0, step=0.5,
    help="Stop loss below recommended buy price"
)

# Advanced options
st.sidebar.subheader("🔍 Advanced Options")
request_delay = st.sidebar.number_input(
    "Delay between requests (seconds):",
    min_value=0.0, max_value=2.0, value=0.3, step=0.1,
    help="Add delay to avoid rate limiting from Yahoo Finance"
)
debug_mode = st.sidebar.checkbox("Debug mode", value=False, help="Show detailed error messages")

# Run analysis button
run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)


# Helper function to calculate recommended prices
def calculate_recommended_price(strategy, current_close, sma_short, sma_long=None):
    if strategy == "mean_reversion":
        # Buy at a discount to SMA20 for better risk/reward
        recommended_price = sma_short * (1 - mr_entry_offset / 100)
        # Don't recommend buying above current price
        if recommended_price > current_close:
            recommended_price = current_close
        return round(recommended_price, 2)
    else:  # trend_following
        # Momentum strategy - buy at market or slight pullback
        if tf_entry_offset > 0:
            recommended_price = current_close * (1 - tf_entry_offset / 100)
        else:
            recommended_price = current_close
        return round(recommended_price, 2)


# Main content area
if run_analysis:
    if not st.session_state.tickers:
        st.error("Please add at least one ticker to analyze")
        st.stop()

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Containers for results
    mean_reversion_signals = []
    trend_following_signals = []
    errors = []
    debug_info = []

    # Analyze each ticker
    for idx, ticker in enumerate(st.session_state.tickers):
        status_text.text(f"Analyzing {ticker}... ({idx + 1}/{len(st.session_state.tickers)})")
        progress_bar.progress((idx + 1) / len(st.session_state.tickers))

        # Add delay to avoid rate limiting
        if idx > 0 and request_delay > 0:
            time.sleep(request_delay)

        try:
            # Fetch data
            data = yf.Ticker(ticker).history(period=period)

            # Debug info
            if debug_mode:
                debug_info.append(f"{ticker}: Retrieved {len(data)} rows of data")

            # Check if data is empty
            if data.empty:
                errors.append(f"{ticker}: No data returned from Yahoo Finance")
                continue

            # Minimum data requirement - 30 days is usually enough for most indicators
            if len(data) < 30:
                errors.append(f"{ticker}: Only {len(data)} days of data available (need at least 30)")
                continue

            # Calculate indicators
            rsi = ta.momentum.rsi(data['Close'], window=rsi_period)
            sma_short_val = data['Close'].rolling(window=sma_short).mean()
            sma_long_val = data['Close'].rolling(window=sma_long).mean()
            volume_sma = data['Volume'].rolling(window=20).mean()

            # Get last values - handle NaN properly
            last_close = data['Close'].iloc[-1]
            last_volume = data['Volume'].iloc[-1]

            # Find last non-NaN RSI value
            rsi_valid = rsi.dropna()
            if len(rsi_valid) == 0:
                errors.append(f"{ticker}: No valid RSI values (need at least {rsi_period + 1} data points)")
                continue
            last_rsi = rsi_valid.iloc[-1]

            # Find last non-NaN SMA short value
            sma_short_valid = sma_short_val.dropna()
            if len(sma_short_valid) == 0:
                errors.append(f"{ticker}: No valid SMA{sma_short} values (need at least {sma_short} data points)")
                continue
            last_sma_short = sma_short_valid.iloc[-1]

            # For SMA long, we need enough data but it's optional for mean reversion
            last_sma_long = None
            if sma_long <= len(data):
                sma_long_valid = sma_long_val.dropna()
                if len(sma_long_valid) > 0:
                    last_sma_long = sma_long_valid.iloc[-1]

            # Volume SMA - more flexible
            volume_sma_valid = volume_sma.dropna()
            if len(volume_sma_valid) > 0:
                last_volume_sma = volume_sma_valid.iloc[-1]
            else:
                last_volume_sma = data['Volume'].mean()  # Fallback to simple average

            # Check for NaN values in critical indicators
            if pd.isna(last_rsi) or pd.isna(last_sma_short) or pd.isna(last_volume_sma):
                errors.append(f"{ticker}: Critical indicators contain NaN values")
                if debug_mode:
                    debug_info.append(
                        f"{ticker}: RSI NaN: {pd.isna(last_rsi)}, SMA{sma_short} NaN: {pd.isna(last_sma_short)}")
                continue

            # Debug output
            if debug_mode:
                debug_info.append(
                    f"{ticker}: RSI={last_rsi:.2f}, Close={last_close:.2f}, SMA{sma_short}={last_sma_short:.2f}")

            # ============================================================
            # STRATEGY 1: MEAN REVERSION
            # ============================================================
            mean_reversion_conditions = (
                    last_rsi < rsi_oversold and
                    last_close < last_sma_short and
                    last_volume > (last_volume_sma * volume_multiplier)
            )

            if mean_reversion_conditions:
                # Calculate recommended buy price
                recommended_buy = calculate_recommended_price(
                    "mean_reversion", last_close, last_sma_short
                )

                # Calculate stop loss
                stop_loss = round(recommended_buy * (1 - mr_stop_loss_pct / 100), 2)

                # Calculate potential upside to SMA20
                upside_to_sma20 = ((last_sma_short - recommended_buy) / recommended_buy) * 100
                risk_reward = round(upside_to_sma20 / mr_stop_loss_pct, 1) if upside_to_sma20 > 0 else 0

                mean_reversion_signals.append({
                    'Ticker': ticker,
                    'Current Price': round(last_close, 2),
                    '🎯 Recommended Buy': recommended_buy,
                    'RSI': round(last_rsi, 2),
                    f'SMA{sma_short}': round(last_sma_short, 2),
                    'Volume Ratio': round(last_volume / last_volume_sma, 2),
                    '🛑 Stop Loss': stop_loss,
                    'Risk/Reward': f"1:{risk_reward}" if risk_reward > 0 else "N/A",
                    'Price vs SMA': f"{((last_close / last_sma_short) - 1) * 100:.1f}%"
                })

            # ============================================================
            # STRATEGY 2: TREND FOLLOWING
            # ============================================================
            if last_sma_long is not None:
                trend_conditions = (
                        last_rsi > rsi_momentum and
                        last_close > last_sma_short and
                        last_sma_short > last_sma_long
                )

                if trend_conditions:
                    # Calculate recommended buy price
                    recommended_buy = calculate_recommended_price(
                        "trend_following", last_close, last_sma_short, last_sma_long
                    )

                    # Calculate stop loss
                    stop_loss = round(recommended_buy * (1 - tf_stop_loss_pct / 100), 2)

                    # Calculate potential upside to recent high (momentum target)
                    recent_high = data['High'].rolling(window=20).max().iloc[-1]
                    if pd.isna(recent_high):
                        recent_high = last_close * 1.05  # Default 5% target
                    upside_target = round(recent_high, 2)
                    potential_return = ((upside_target - recommended_buy) / recommended_buy) * 100

                    trend_following_signals.append({
                        'Ticker': ticker,
                        'Current Price': round(last_close, 2),
                        '🎯 Recommended Buy': recommended_buy,
                        'RSI': round(last_rsi, 2),
                        f'SMA{sma_short}': round(last_sma_short, 2),
                        f'SMA{sma_long}': round(last_sma_long, 2),
                        '🛑 Stop Loss': stop_loss,
                        '🎯 Target': upside_target,
                        'Potential Return': f"{potential_return:.1f}%",
                        'Trend Strength': f"{((last_sma_short / last_sma_long) - 1) * 100:.1f}%"
                    })
            elif debug_mode:
                debug_info.append(f"{ticker}: Insufficient data for SMA{sma_long} (need {sma_long} days)")

        except Exception as e:
            errors.append(f"{ticker}: {str(e)}")
            if debug_mode:
                debug_info.append(f"{ticker}: Exception details - {type(e).__name__}: {str(e)}")

    # Clear progress indicators
    status_text.empty()
    progress_bar.empty()

    # ============================================================
    # DISPLAY RESULTS
    # ============================================================

    st.markdown("---")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tickers Analyzed", len(st.session_state.tickers))
    with col2:
        st.metric("📉 Mean Reversion Signals", len(mean_reversion_signals),
                  delta="Buy" if len(mean_reversion_signals) > 0 else None,
                  delta_color="normal")
    with col3:
        st.metric("📈 Trend Following Signals", len(trend_following_signals),
                  delta="Buy" if len(trend_following_signals) > 0 else None,
                  delta_color="normal")
    with col4:
        total_signals = len(mean_reversion_signals) + len(trend_following_signals)
        st.metric("Total Opportunities", total_signals)

    st.markdown("---")

    # Display Mean Reversion Results
    st.header("📉 Mean Reversion Signals")
    st.caption(f"""
    **Strategy**: Buy when RSI < {rsi_oversold} (oversold) AND Price < SMA{sma_short} AND Volume > {volume_multiplier}x average
    **Entry Rule**: Recommended buy = SMA{sma_short} - {mr_entry_offset}% (or current price if lower)
    **Stop Loss**: {mr_stop_loss_pct}% below recommended buy price
    """)

    if mean_reversion_signals:
        df_mr = pd.DataFrame(mean_reversion_signals)

        # Display as formatted dataframe
        st.dataframe(df_mr, use_container_width=True, hide_index=True)

        # Download button
        csv_mr = df_mr.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Mean Reversion Signals (CSV)",
            data=csv_mr,
            file_name=f"mean_reversion_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="mr_download"
        )

        # Display explanation
        with st.expander("ℹ️ How to use Mean Reversion signals"):
            st.markdown(f"""
            - **Recommended Buy**: Place a limit order at this price or lower
            - **Stop Loss**: Set at {mr_stop_loss_pct}% below your entry price
            - **Take Profit**: Consider taking profits when price reaches SMA{sma_short} or higher
            - **Risk/Reward**: The ratio shows potential profit vs stop loss distance
            - **Volume Ratio**: Higher values indicate stronger institutional interest
            """)
    else:
        st.info("No mean reversion buy signals found with current parameters")

    st.markdown("---")

    # Display Trend Following Results
    st.header("📈 Trend Following Signals")
    st.caption(f"""
    **Strategy**: Buy when RSI > {rsi_momentum} (momentum) AND Price > SMA{sma_short} AND SMA{sma_short} > SMA{sma_long}
    **Entry Rule**: {'Market price' if tf_entry_offset == 0 else f'{tf_entry_offset}% below current price'}
    **Stop Loss**: {tf_stop_loss_pct}% below recommended buy price
    **Target**: Recent 20-day high
    """)

    if trend_following_signals:
        df_tf = pd.DataFrame(trend_following_signals)

        # Display as formatted dataframe
        st.dataframe(df_tf, use_container_width=True, hide_index=True)

        # Download button
        csv_tf = df_tf.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Trend Following Signals (CSV)",
            data=csv_tf,
            file_name=f"trend_following_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="tf_download"
        )

        # Display explanation
        with st.expander("ℹ️ How to use Trend Following signals"):
            st.markdown(f"""
            - **Recommended Buy**: {'Buy at market price' if tf_entry_offset == 0 else f'Place limit order {tf_entry_offset}% below current price'}
            - **Stop Loss**: Set at {tf_stop_loss_pct}% below your entry price
            - **Take Profit**: Target recent 20-day high or trail stop loss as trend continues
            - **Position Sizing**: Consider smaller positions as momentum strategies can have larger drawdowns
            - **Trend Strength**: Positive values indicate strong uptrend confirmation
            """)
    else:
        st.info("No trend following buy signals found with current parameters")

    # Display errors if any
    if errors:
        st.markdown("---")
        st.warning(f"⚠️ Errors encountered ({len(errors)} out of {len(st.session_state.tickers)} tickers):")
        with st.expander("Show error details"):
            for error in errors[:20]:  # Show first 20 errors
                st.code(error)
            if len(errors) > 20:
                st.caption(f"... and {len(errors) - 20} more errors")

    # Display debug info if enabled
    if debug_mode and debug_info:
        st.markdown("---")
        with st.expander("🐛 Debug Information"):
            for info in debug_info[:30]:
                st.text(info)
            if len(debug_info) > 30:
                st.caption(f"... and {len(debug_info) - 30} more debug entries")

    # Display timestamp
    st.markdown("---")
    st.caption(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption(f"Data period: {period} | RSI period: {rsi_period} | SMA periods: {sma_short}/{sma_long}")

else:
    # Initial state - no analysis run yet
    st.info("👈 Configure your tickers and parameters in the sidebar, then click 'Run Analysis'")

    # Show default tickers
    with st.expander("📋 Current Ticker List"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Banking & Finance**")
            st.write("\n".join(
                [t for t in st.session_state.tickers if any(bank in t for bank in ['BBCA', 'BNGA', 'BBRI', 'BBNI'])]))
        with col2:
            st.write("**Others**")
            st.write("\n".join([t for t in st.session_state.tickers if
                                not any(bank in t for bank in ['BBCA', 'BNGA', 'BBRI', 'BBNI'])]))

    # Quick guide
    with st.expander("ℹ️ How to use this screener"):
        st.markdown("""
        ### Getting Started
        1. **Manage tickers** in the sidebar (add/remove stocks)
        2. **Adjust parameters** including:
           - Entry offsets (buy at discount vs market)
           - Stop loss percentages
           - RSI thresholds and SMA periods
        3. **Click 'Run Analysis'** to scan all tickers

        ### Strategy Explanations

        **📉 Mean Reversion** (Buying dips):
        - Looks for oversold conditions (RSI < 30)
        - Price below moving average suggests potential bounce
        - Volume confirmation helps identify genuine reversals
        - **Recommended Buy**: SMA20 minus offset (buying at discount)

        **📈 Trend Following** (Buying momentum):
        - Confirms uptrend (RSI > 50, price above SMAs)
        - SMA20 above SMA50 indicates bullish structure
        - **Recommended Buy**: Market price or slight pullback

        ### Tips
        - Start with default parameters, then adjust based on backtesting
        - Use stop losses to manage risk
        - Consider market conditions (range-bound = mean reversion, trending = trend following)
        - Enable debug mode if you encounter issues with data retrieval

        ### Disclaimer
        This tool is for educational purposes only. Past performance doesn't guarantee future results. Always do your own research before trading.
        """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ **Disclaimer**: For educational purposes only. Not financial advice. Recommended prices are suggestions, not guarantees.")
st.sidebar.caption(f"🕐 Last session: {datetime.now().strftime('%Y-%m-%d %H:%M')}")