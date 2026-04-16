import streamlit as st
import yfinance as yf
import pandas as pd
import ta

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
        'AALI.JK', 'ARTO.JK', 'ASGR.JK', 'ASII.JK', 'AUTO.JK',
        'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BBTN.JK', 'BDMN.JK',
        'BJBR.JK', 'BJTM.JK', 'BMRI.JK', 'BNGA.JK', 'BNLI.JK',
        'BRIS.JK', 'BTPS.JK', 'BTPN.JK', 'HEAL.JK', 'ICBP.JK',
        'INDF.JK', 'KLBF.JK', 'MARK.JK', 'MIKA.JK', 'NISP.JK',
        'OMED.JK', 'PNBN.JK', 'POWR.JK', 'SIDO.JK', 'SMSM.JK',
        'TLKM.JK', 'TSPC.JK', 'UNTR.JK', 'MLBI.JK', 'DLTA.JK',
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

                bb_low = ta.volatility.bollinger_lband(
                    data['Close'],
                    window=params['bb_window'],
                    window_dev=params['bb_std']
                )

                obv = ta.volume.on_balance_volume(data['Close'], data['Volume'])
                obv_sma = obv.rolling(window=params['obv_sma_period']).mean()

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

        # Display results
        st.header("📊 Scan Results")

        # Create summary table with checkmarks
        st.subheader("Signal Summary Table")

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
                row['Trend Following'] = '✅' if any(
                    s['Ticker'] == ticker for s in all_signals['Trend Following']) else ''
                row['MACD'] = '✅' if any(s['Ticker'] == ticker for s in all_signals['MACD Crossover']) else ''
                row['Stochastic'] = '✅' if any(
                    s['Ticker'] == ticker for s in all_signals['Stochastic Oversold']) else ''
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
                            file_name=f"{strategy_name.lower().replace(' ', '_')}_{BACKTEST_END_DATE_STR}.csv",
                            mime="text/csv",
                            key=f"download_{strategy_name}"
                        )
                    else:
                        st.info(f"No {strategy_name} signals found")

            # Combined download button for all detailed data
            st.divider()
            all_detailed_data = []
            for strategy_name, signals in all_signals.items():
                for signal in signals:
                    signal_copy = signal.copy()
                    signal_copy['Strategy'] = strategy_name
                    signal_copy['Signal Date'] = signal_copy['Signal Date'].strftime('%Y-%m-%d')
                    all_detailed_data.append(signal_copy)

            if all_detailed_data:
                df_all_detailed = pd.DataFrame(all_detailed_data)
                csv_all = df_all_detailed.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Detailed Results as CSV",
                    data=csv_all,
                    file_name=f"all_signals_detailed_{BACKTEST_END_DATE_STR}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No signals found for any strategy in the current scan period.")

        # Display current tickers
        st.divider()
        st.caption(
            f"**Active Tickers ({len(st.session_state.tickers)}):** {', '.join(st.session_state.tickers[:10])}{'...' if len(st.session_state.tickers) > 10 else ''}")

else:
    # Show instructions when no scan has been run
    st.info("👈 Configure your settings in the sidebar and click 'Run Scan' to start scanning for signals.")

    # Display current configuration summary
    st.subheader("Current Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Tickers:**")
        st.write(f"Total: {len(st.session_state.tickers)} tickers")
        st.write("**Indicator Settings:**")
        params = st.session_state.indicator_params
        st.write(
            f"- RSI: Period {params['rsi_period']}, Oversold <{params['rsi_oversold']}, Trend >{params['rsi_trend']}")
        st.write(f"- Moving Averages: SMA{params['sma_short']} / SMA{params['sma_long']}")
        st.write(f"- MACD: {params['macd_fast']}/{params['macd_slow']}/{params['macd_signal']}")

    with col2:
        st.write("&nbsp;")
        st.write(
            f"- Stochastic: %K({params['stoch_window']},{params['stoch_smooth']}), Oversold <{params['stoch_oversold']}")
        st.write(f"- Bollinger Bands: Period {params['bb_window']}, Std {params['bb_std']}")
        st.write(f"- OBV: SMA{params['obv_sma_period']}")
        st.write(f"- Backtest: {params['backtest_days']} days")
        st.write(f"- Risk: TP +{params['take_profit_pct']}%, SL -{params['stop_loss_pct']}%")