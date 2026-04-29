import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Stock Signal Scanner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Stock Signal Scanner")
st.markdown("Scan stocks for technical analysis signals")

# Initialize session state for tickers
if 'tickers' not in st.session_state:
    st.session_state.tickers = [
        'AADI.JK', 'AALI.JK', 'ABMM.JK', 'ADMF.JK', 'ADRO.JK',
        'ARTO.JK', 'ASGR.JK', 'ASII.JK', 'AUTO.JK', 'BAYU.JK',
        'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BBTN.JK', 'BDMN.JK',
        'BFIN.JK', 'BIRD.JK', 'BJBR.JK', 'BJTM.JK', 'BMRI.JK',
        'BNGA.JK', 'BNLI.JK', 'BRIS.JK', 'BSDE.JK', 'BSSR.JK',
        'BTPN.JK', 'BTPS.JK', 'CITA.JK', 'CTRA.JK', 'DLTA.JK',
        'ELSA.JK', 'HEAL.JK', 'HEXA.JK', 'ICBP.JK', 'INDF.JK',
        'INKP.JK', 'IPCC.JK', 'ISSP.JK', 'JPFA.JK', 'KLBF.JK',
        'LSIP.JK', 'MAPI.JK', 'MARK.JK', 'MIKA.JK', 'MLBI.JK',
        'NISP.JK', 'OMED.JK', 'PNBN.JK', 'POWR.JK', 'SIDO.JK',
        'SMSM.JK', 'STAA.JK', 'TKIM.JK', 'TLKM.JK', 'TOTO.JK',
        'TOWR.JK', 'TSPC.JK', 'UNTR.JK', 'UNVR.JK'
    ]
    st.session_state.tickers.sort()

# Initialize session state for indicator parameters
if 'indicator_params' not in st.session_state:
    st.session_state.indicator_params = {
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_trend': 50,
        'sma_short': 20,
        'sma_long': 50,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'stoch_window': 14,
        'stoch_smooth': 3,
        'stoch_oversold': 20,
        'bb_window': 20,
        'bb_std': 2,
        'obv_sma_period': 10,
        'backtest_days': 120,
        'take_profit_pct': 3.0,
        'stop_loss_pct': 2.0
    }

# Initialize session state for scan results
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'all_signals' not in st.session_state:
    st.session_state.all_signals = None
if 'backtest_data' not in st.session_state:
    st.session_state.backtest_data = {}

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Ticker Management
    st.subheader("📋 Ticker Management")

    # Add new ticker
    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add new ticker", placeholder="e.g., GOTO.JK", key="new_ticker")
    with col2:
        if st.button("Add", use_container_width=True):
            if new_ticker and new_ticker.upper() not in st.session_state.tickers:
                st.session_state.tickers.append(new_ticker.upper())
                st.session_state.tickers.sort()
                st.rerun()
            elif new_ticker:
                st.warning("Ticker already exists!")

    # Edit ticker
    ticker_to_edit = st.selectbox("Select ticker to edit", st.session_state.tickers, key="edit_select")
    edited_ticker = st.text_input("Edit ticker", value=ticker_to_edit if ticker_to_edit else "", key="edit_ticker")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update", use_container_width=True):
            if edited_ticker and edited_ticker != ticker_to_edit:
                idx = st.session_state.tickers.index(ticker_to_edit)
                st.session_state.tickers[idx] = edited_ticker.upper()
                st.session_state.tickers.sort()
                st.rerun()
    with col2:
        if st.button("Delete", use_container_width=True):
            if ticker_to_edit in st.session_state.tickers:
                st.session_state.tickers.remove(ticker_to_edit)
                st.rerun()

    st.divider()

    # Indicator Parameters
    st.subheader("📊 Indicator Parameters")

    with st.expander("RSI Settings", expanded=False):
        st.session_state.indicator_params['rsi_period'] = st.number_input(
            "RSI Period", min_value=2, max_value=50,
            value=st.session_state.indicator_params['rsi_period']
        )
        st.session_state.indicator_params['rsi_oversold'] = st.slider(
            "RSI Oversold Threshold", min_value=10, max_value=40,
            value=st.session_state.indicator_params['rsi_oversold']
        )
        st.session_state.indicator_params['rsi_trend'] = st.slider(
            "RSI Trend Threshold", min_value=40, max_value=70,
            value=st.session_state.indicator_params['rsi_trend']
        )

    with st.expander("Moving Averages", expanded=False):
        st.session_state.indicator_params['sma_short'] = st.number_input(
            "Short SMA Period", min_value=5, max_value=50,
            value=st.session_state.indicator_params['sma_short']
        )
        st.session_state.indicator_params['sma_long'] = st.number_input(
            "Long SMA Period", min_value=20, max_value=200,
            value=st.session_state.indicator_params['sma_long']
        )

    with st.expander("MACD Settings", expanded=False):
        st.session_state.indicator_params['macd_fast'] = st.number_input(
            "MACD Fast", min_value=5, max_value=20,
            value=st.session_state.indicator_params['macd_fast']
        )
        st.session_state.indicator_params['macd_slow'] = st.number_input(
            "MACD Slow", min_value=15, max_value=40,
            value=st.session_state.indicator_params['macd_slow']
        )
        st.session_state.indicator_params['macd_signal'] = st.number_input(
            "MACD Signal", min_value=5, max_value=15,
            value=st.session_state.indicator_params['macd_signal']
        )

    with st.expander("Stochastic Settings", expanded=False):
        st.session_state.indicator_params['stoch_window'] = st.number_input(
            "Stochastic %K Period", min_value=5, max_value=30,
            value=st.session_state.indicator_params['stoch_window']
        )
        st.session_state.indicator_params['stoch_smooth'] = st.number_input(
            "Stochastic %K Smooth", min_value=2, max_value=5,
            value=st.session_state.indicator_params['stoch_smooth']
        )
        st.session_state.indicator_params['stoch_oversold'] = st.slider(
            "Stochastic Oversold", min_value=10, max_value=30,
            value=st.session_state.indicator_params['stoch_oversold']
        )

    with st.expander("Bollinger Bands", expanded=False):
        st.session_state.indicator_params['bb_window'] = st.number_input(
            "BB Period", min_value=10, max_value=50,
            value=st.session_state.indicator_params['bb_window']
        )
        st.session_state.indicator_params['bb_std'] = st.slider(
            "BB Standard Deviations", min_value=1.0, max_value=3.0, step=0.5,
            value=float(st.session_state.indicator_params['bb_std'])
        )

    with st.expander("OBV Settings", expanded=False):
        st.session_state.indicator_params['obv_sma_period'] = st.number_input(
            "OBV SMA Period", min_value=5, max_value=30,
            value=st.session_state.indicator_params['obv_sma_period']
        )

    with st.expander("Backtest & Risk Settings", expanded=False):
        st.session_state.indicator_params['backtest_days'] = st.number_input(
            "Backtest Period (days)", min_value=30, max_value=365,
            value=st.session_state.indicator_params['backtest_days']
        )
        st.session_state.indicator_params['take_profit_pct'] = st.slider(
            "Take Profit %", min_value=1.0, max_value=10.0, step=0.5,
            value=float(st.session_state.indicator_params['take_profit_pct'])
        )
        st.session_state.indicator_params['stop_loss_pct'] = st.slider(
            "Stop Loss %", min_value=1.0, max_value=10.0, step=0.5,
            value=float(st.session_state.indicator_params['stop_loss_pct'])
        )

    # Scan button
    st.divider()
    scan_button = st.button("🔍 Run Scan", type="primary", use_container_width=True)

# Main content area
if scan_button:
    with st.spinner("Scanning stocks for signals..."):
        # Get parameters from session state
        params = st.session_state.indicator_params

        # Define the historical backtesting period
        BACKTEST_END_DATE = pd.Timestamp.now() - pd.Timedelta(days=1)
        BACKTEST_START_DATE = BACKTEST_END_DATE - pd.Timedelta(days=params['backtest_days'])
        BACKTEST_END_DATE_STR = BACKTEST_END_DATE.strftime('%Y-%m-%d')
        BACKTEST_START_DATE_STR = BACKTEST_START_DATE.strftime('%Y-%m-%d')

        # Signal containers
        all_signals = {
            'Mean Reversion': [],
            'Trend Following': [],
            'MACD Crossover': [],
            'Stochastic Oversold': [],
            'Bollinger Band Reversion': [],
            'OBV Accumulation': []
        }

        # Store backtest data for each ticker
        backtest_data = {}

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, ticker in enumerate(st.session_state.tickers):
            try:
                status_text.text(f"Processing {ticker}... ({idx + 1}/{len(st.session_state.tickers)})")

                # Fetch data
                data = yf.Ticker(ticker).history(start=BACKTEST_START_DATE_STR, end=BACKTEST_END_DATE_STR)

                if data.index.tz is not None:
                    data.index = data.index.tz_convert(None)

                min_periods = max(params['sma_long'], params['macd_slow'])
                if data.empty or len(data) < min_periods:
                    continue

                # Calculate indicators
                rsi = ta.momentum.rsi(data['Close'], window=params['rsi_period'])
                sma_short = data['Close'].rolling(window=params['sma_short']).mean()
                sma_long = data['Close'].rolling(window=params['sma_long']).mean()
                volume_sma = data['Volume'].rolling(window=params['sma_short']).mean()

                # MACD calculation
                macd_line = ta.trend.macd(
                    data['Close'],
                    window_slow=params['macd_slow'],
                    window_fast=params['macd_fast']
                )
                macd_signal_line = ta.trend.macd_signal(
                    data['Close'],
                    window_slow=params['macd_slow'],
                    window_fast=params['macd_fast'],
                    window_sign=params['macd_signal']
                )
                macd_histogram = ta.trend.macd_diff(
                    data['Close'],
                    window_slow=params['macd_slow'],
                    window_fast=params['macd_fast'],
                    window_sign=params['macd_signal']
                )

                stoch_k = ta.momentum.stoch(
                    data['High'], data['Low'], data['Close'],
                    window=params['stoch_window'],
                    smooth_window=params['stoch_smooth']
                )
                stoch_d = ta.momentum.stoch_signal(
                    data['High'], data['Low'], data['Close'],
                    window=params['stoch_window'],
                    smooth_window=params['stoch_smooth']
                )

                bb_upper = ta.volatility.bollinger_hband(
                    data['Close'],
                    window=params['bb_window'],
                    window_dev=params['bb_std']
                )
                bb_middle = ta.volatility.bollinger_mavg(
                    data['Close'],
                    window=params['bb_window']
                )
                bb_low = ta.volatility.bollinger_lband(
                    data['Close'],
                    window=params['bb_window'],
                    window_dev=params['bb_std']
                )

                obv = ta.volume.on_balance_volume(data['Close'], data['Volume'])
                obv_sma = obv.rolling(window=params['obv_sma_period']).mean()

                # Store backtest data
                backtest_data[ticker] = {
                    'data': data,
                    'rsi': rsi,
                    'sma_short': sma_short,
                    'sma_long': sma_long,
                    'volume_sma': volume_sma,
                    'macd_line': macd_line,
                    'macd_signal': macd_signal_line,
                    'macd_histogram': macd_histogram,
                    'stoch_k': stoch_k,
                    'stoch_d': stoch_d,
                    'bb_upper': bb_upper,
                    'bb_middle': bb_middle,
                    'bb_low': bb_low,
                    'obv': obv,
                    'obv_sma': obv_sma
                }

                # Latest values
                last_close = data['Close'].iloc[-1]
                last_rsi = rsi.iloc[-1]
                last_sma_short = sma_short.iloc[-1]
                last_sma_long = sma_long.iloc[-1]
                last_volume = data['Volume'].iloc[-1]
                last_volume_sma = volume_sma.iloc[-1]
                last_macd = macd_line.iloc[-1]
                last_macd_signal = macd_signal_line.iloc[-1]
                last_stoch_k = stoch_k.iloc[-1]
                last_stoch_d = stoch_d.iloc[-1]
                last_bb_low = bb_low.iloc[-1]
                last_obv = obv.iloc[-1]
                last_obv_sma = obv_sma.iloc[-1]

                take_profit_multiplier = 1 + (params['take_profit_pct'] / 100)
                stop_loss_multiplier = 1 - (params['stop_loss_pct'] / 100)

                signal_date = pd.to_datetime(BACKTEST_END_DATE_STR)

                # Strategy checks
                # Mean Reversion
                if (not pd.isna(last_rsi) and not pd.isna(last_close) and not pd.isna(last_sma_short) and
                        last_rsi < params[
                            'rsi_oversold'] and last_close < last_sma_short and last_volume > last_volume_sma):
                    all_signals['Mean Reversion'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Sell Price': round(last_close * take_profit_multiplier, 2),
                        'Stop Loss': round(last_close * stop_loss_multiplier, 2),
                        'RSI': round(last_rsi, 2),
                        f'SMA{params["sma_short"]}': round(last_sma_short, 2),
                        'Volume Ratio': round(last_volume / last_volume_sma, 2) if last_volume_sma != 0 else 0,
                        'Signal Date': signal_date
                    })

                # Trend Following
                if (not pd.isna(last_rsi) and not pd.isna(last_close) and not pd.isna(last_sma_short) and not pd.isna(
                        last_sma_long) and
                        last_rsi > params[
                            'rsi_trend'] and last_close > last_sma_short and last_sma_short > last_sma_long and last_volume > last_volume_sma):
                    all_signals['Trend Following'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Sell Price': round(last_close * take_profit_multiplier, 2),
                        'Stop Loss': round(last_close * stop_loss_multiplier, 2),
                        'RSI': round(last_rsi, 2),
                        f'SMA{params["sma_short"]}': round(last_sma_short, 2),
                        f'SMA{params["sma_long"]}': round(last_sma_long, 2),
                        'Signal Date': signal_date
                    })

                # MACD
                if (not pd.isna(last_macd) and not pd.isna(last_macd_signal) and
                        last_macd > last_macd_signal and last_macd < 0):
                    all_signals['MACD Crossover'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Sell Price': round(last_close * take_profit_multiplier, 2),
                        'Stop Loss': round(last_close * stop_loss_multiplier, 2),
                        'MACD': round(last_macd, 2),
                        'MACD Signal': round(last_macd_signal, 2),
                        'Signal Date': signal_date
                    })

                # Stochastic
                if (not pd.isna(last_stoch_k) and not pd.isna(last_stoch_d) and
                        last_stoch_k > last_stoch_d and last_stoch_k < params['stoch_oversold']):
                    all_signals['Stochastic Oversold'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Sell Price': round(last_close * take_profit_multiplier, 2),
                        'Stop Loss': round(last_close * stop_loss_multiplier, 2),
                        'Stoch %K': round(last_stoch_k, 2),
                        'Stoch %D': round(last_stoch_d, 2),
                        'Signal Date': signal_date
                    })

                # Bollinger Bands
                if not pd.isna(last_bb_low) and last_close < last_bb_low:
                    all_signals['Bollinger Band Reversion'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Sell Price': round(last_close * take_profit_multiplier, 2),
                        'Stop Loss': round(last_close * stop_loss_multiplier, 2),
                        'Close': round(last_close, 2),
                        'BB Lower': round(last_bb_low, 2),
                        'Signal Date': signal_date
                    })

                # OBV
                if (not pd.isna(last_obv) and not pd.isna(last_obv_sma) and
                        last_obv > last_obv_sma):
                    all_signals['OBV Accumulation'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Sell Price': round(last_close * take_profit_multiplier, 2),
                        'Stop Loss': round(last_close * stop_loss_multiplier, 2),
                        'OBV': round(last_obv, 2),
                        f'OBV SMA{params["obv_sma_period"]}': round(last_obv_sma, 2),
                        'Signal Date': signal_date
                    })

                progress_bar.progress((idx + 1) / len(st.session_state.tickers))

            except Exception as e:
                st.error(f"Error processing {ticker}: {e}")

        status_text.text("Scan complete!")
        progress_bar.empty()

        # Store results in session state
        st.session_state.scan_results = {
            'start_date': BACKTEST_START_DATE_STR,
            'end_date': BACKTEST_END_DATE_STR
        }
        st.session_state.all_signals = all_signals
        st.session_state.backtest_data = backtest_data

# Display results if available
if st.session_state.all_signals is not None:
    all_signals = st.session_state.all_signals
    backtest_data = st.session_state.backtest_data
    params = st.session_state.indicator_params

    # Backtesting Visualization Section
    st.header("📈 Backtesting Visualization")

    # Get tickers that have backtest data
    available_tickers = list(backtest_data.keys())

    if available_tickers:
        selected_ticker = st.selectbox(
            "Select Ticker for Backtesting View",
            available_tickers,
            key="backtest_ticker"
        )

        if selected_ticker and selected_ticker in backtest_data:
            bt_data = backtest_data[selected_ticker]
            data = bt_data['data']

            # Create tabs for different indicator groups
            viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                "Price & Moving Averages",
                "RSI & Stochastic",
                "MACD",
                "Bollinger Bands & OBV"
            ])

            with viz_tab1:
                st.subheader(f"{selected_ticker} - Price and Moving Averages")

                fig1 = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f"Price Action", "Volume")
                )

                # Price and MAs
                fig1.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name="Price"
                    ),
                    row=1, col=1
                )

                fig1.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['sma_short'],
                        name=f"SMA {params['sma_short']}",
                        line=dict(color='blue', width=1)
                    ),
                    row=1, col=1
                )

                fig1.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['sma_long'],
                        name=f"SMA {params['sma_long']}",
                        line=dict(color='red', width=1)
                    ),
                    row=1, col=1
                )

                # Volume
                colors = ['green' if close >= open_ else 'red'
                          for close, open_ in zip(data['Close'], data['Open'])]
                fig1.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['Volume'],
                        name="Volume",
                        marker_color=colors
                    ),
                    row=2, col=1
                )

                fig1.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['volume_sma'],
                        name=f"Volume SMA {params['sma_short']}",
                        line=dict(color='orange', width=1)
                    ),
                    row=2, col=1
                )

                fig1.update_layout(
                    height=600,
                    showlegend=True,
                    xaxis_rangeslider_visible=False
                )

                st.plotly_chart(fig1, use_container_width=True)

                # Signal summary for this ticker
                st.subheader("Active Signals")
                signals_for_ticker = []
                for strategy_name, signals in all_signals.items():
                    for signal in signals:
                        if signal['Ticker'] == selected_ticker:
                            signals_for_ticker.append({
                                'Strategy': strategy_name,
                                'Buy Price': signal['Buy Price'],
                                'Sell Price': signal['Sell Price'],
                                'Stop Loss': signal['Stop Loss']
                            })

                if signals_for_ticker:
                    df_ticker_signals = pd.DataFrame(signals_for_ticker)
                    st.dataframe(df_ticker_signals, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No active signals for {selected_ticker}")

            with viz_tab2:
                st.subheader(f"{selected_ticker} - RSI and Stochastic Oscillator")

                fig2 = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.15,
                    row_heights=[0.5, 0.5],
                    subplot_titles=("RSI", "Stochastic Oscillator")
                )

                # RSI
                fig2.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['rsi'],
                        name="RSI",
                        line=dict(color='purple', width=2)
                    ),
                    row=1, col=1
                )

                # RSI levels
                fig2.add_hline(
                    y=70, line_dash="dash", line_color="red",
                    row=1, col=1
                )
                fig2.add_hline(
                    y=30, line_dash="dash", line_color="green",
                    row=1, col=1
                )
                fig2.add_hline(
                    y=50, line_dash="dot", line_color="gray",
                    row=1, col=1
                )

                # Stochastic
                fig2.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['stoch_k'],
                        name="%K",
                        line=dict(color='blue', width=2)
                    ),
                    row=2, col=1
                )

                fig2.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['stoch_d'],
                        name="%D",
                        line=dict(color='red', width=2)
                    ),
                    row=2, col=1
                )

                # Stochastic levels
                fig2.add_hline(
                    y=80, line_dash="dash", line_color="red",
                    row=2, col=1
                )
                fig2.add_hline(
                    y=20, line_dash="dash", line_color="green",
                    row=2, col=1
                )

                fig2.update_layout(
                    height=600,
                    showlegend=True
                )

                st.plotly_chart(fig2, use_container_width=True)

            with viz_tab3:
                st.subheader(f"{selected_ticker} - MACD")

                fig3 = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f"Price", "MACD")
                )

                # Price
                fig3.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name="Price"
                    ),
                    row=1, col=1
                )

                # MACD
                fig3.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['macd_line'],
                        name="MACD",
                        line=dict(color='blue', width=2)
                    ),
                    row=2, col=1
                )

                fig3.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['macd_signal'],
                        name="Signal",
                        line=dict(color='red', width=2)
                    ),
                    row=2, col=1
                )

                # MACD Histogram
                colors_hist = ['green' if val >= 0 else 'red' for val in bt_data['macd_histogram']]
                fig3.add_trace(
                    go.Bar(
                        x=data.index,
                        y=bt_data['macd_histogram'],
                        name="Histogram",
                        marker_color=colors_hist
                    ),
                    row=2, col=1
                )

                fig3.add_hline(y=0, line_dash="solid", line_color="black", row=2, col=1)

                fig3.update_layout(
                    height=600,
                    showlegend=True,
                    xaxis_rangeslider_visible=False
                )

                st.plotly_chart(fig3, use_container_width=True)

            with viz_tab4:
                st.subheader(f"{selected_ticker} - Bollinger Bands and OBV")

                fig4 = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.15,
                    row_heights=[0.6, 0.4],
                    subplot_titles=("Bollinger Bands", "On-Balance Volume")
                )

                # Bollinger Bands
                fig4.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        name="Close",
                        line=dict(color='black', width=2)
                    ),
                    row=1, col=1
                )

                fig4.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['bb_upper'],
                        name="Upper Band",
                        line=dict(color='gray', width=1, dash='dash')
                    ),
                    row=1, col=1
                )

                fig4.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['bb_middle'],
                        name="Middle Band",
                        line=dict(color='blue', width=1)
                    ),
                    row=1, col=1
                )

                fig4.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['bb_low'],
                        name="Lower Band",
                        line=dict(color='gray', width=1, dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(128, 128, 128, 0.1)'
                    ),
                    row=1, col=1
                )

                # OBV
                fig4.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['obv'],
                        name="OBV",
                        line=dict(color='green', width=2)
                    ),
                    row=2, col=1
                )

                fig4.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=bt_data['obv_sma'],
                        name=f"OBV SMA {params['obv_sma_period']}",
                        line=dict(color='orange', width=2)
                    ),
                    row=2, col=1
                )

                fig4.update_layout(
                    height=600,
                    showlegend=True
                )

                st.plotly_chart(fig4, use_container_width=True)

    # Summary Table Section
    st.header("📊 Signal Summary Table")

    # Get all tickers that have at least one signal
    tickers_with_signals = set()
    for strategy_name, signals in all_signals.items():
        for signal in signals:
            tickers_with_signals.add(signal['Ticker'])

    if tickers_with_signals:
        # Create summary DataFrame
        summary_data = []
        for ticker in sorted(tickers_with_signals):
            row = {'Ticker': ticker}

            # Check each strategy
            row['Mean Reversion'] = '✅' if any(s['Ticker'] == ticker for s in all_signals['Mean Reversion']) else ''
            row['Trend Following'] = '✅' if any(s['Ticker'] == ticker for s in all_signals['Trend Following']) else ''
            row['MACD'] = '✅' if any(s['Ticker'] == ticker for s in all_signals['MACD Crossover']) else ''
            row['Stochastic'] = '✅' if any(s['Ticker'] == ticker for s in all_signals['Stochastic Oversold']) else ''
            row['Bollinger'] = '✅' if any(
                s['Ticker'] == ticker for s in all_signals['Bollinger Band Reversion']) else ''
            row['OBV'] = '✅' if any(s['Ticker'] == ticker for s in all_signals['OBV Accumulation']) else ''

            # Count total signals for this ticker
            total_signals = sum([
                any(s['Ticker'] == ticker for s in all_signals['Mean Reversion']),
                any(s['Ticker'] == ticker for s in all_signals['Trend Following']),
                any(s['Ticker'] == ticker for s in all_signals['MACD Crossover']),
                any(s['Ticker'] == ticker for s in all_signals['Stochastic Oversold']),
                any(s['Ticker'] == ticker for s in all_signals['Bollinger Band Reversion']),
                any(s['Ticker'] == ticker for s in all_signals['OBV Accumulation'])
            ])
            row['Total'] = total_signals

            summary_data.append(row)

        df_summary = pd.DataFrame(summary_data)
        df_summary = df_summary.sort_values('Total', ascending=False)

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tickers with Signals", len(tickers_with_signals))
        with col2:
            total_signals_count = sum(len(signals) for signals in all_signals.values())
            st.metric("Total Signals", total_signals_count)
        with col3:
            avg_signals = total_signals_count / len(tickers_with_signals) if tickers_with_signals else 0
            st.metric("Avg Signals per Ticker", f"{avg_signals:.1f}")

        # Display summary table
        st.dataframe(
            df_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Ticker': st.column_config.TextColumn('Ticker', width='medium'),
                'Mean Reversion': st.column_config.TextColumn('Mean Reversion', width='small'),
                'Trend Following': st.column_config.TextColumn('Trend Following', width='small'),
                'MACD': st.column_config.TextColumn('MACD', width='small'),
                'Stochastic': st.column_config.TextColumn('Stochastic', width='small'),
                'Bollinger': st.column_config.TextColumn('Bollinger', width='small'),
                'OBV': st.column_config.TextColumn('OBV', width='small'),
                'Total': st.column_config.NumberColumn('Total Signals', width='small')
            }
        )

        # Detailed view by strategy
        st.subheader("Detailed View by Strategy")

        strategy_tabs = st.tabs(list(all_signals.keys()))

        for tab, (strategy_name, signals) in zip(strategy_tabs, all_signals.items()):
            with tab:
                if signals:
                    df_strategy = pd.DataFrame(signals)
                    df_strategy['Signal Date'] = df_strategy['Signal Date'].dt.strftime('%Y-%m-%d')
                    st.dataframe(df_strategy, use_container_width=True, hide_index=True)
                    st.caption(f"Total: {len(signals)} signals")

                    # Download button for individual strategy
                    csv_strategy = df_strategy.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {strategy_name} Results",
                        data=csv_strategy,
                        file_name=f"{strategy_name.lower().replace(' ', '_')}_{st.session_state.scan_results['end_date']}.csv",
                        mime="text/csv",
                        key=f"download_{strategy_name}"
                    )
                else:
                    st.info(f"No {strategy_name} signals found")

        # Combined download button
        st.divider()
        all_detailed_data = []
        for strategy_name, signals in all_signals.items():
            for signal in signals:
                signal_copy = signal.copy()
