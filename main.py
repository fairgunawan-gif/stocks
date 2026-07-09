import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Enhanced Stock Signal Scanner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Enhanced Stock Signal Scanner")
st.markdown("Advanced Technical Analysis with Dynamic Risk Management - BUY & SELL Signals")

# Initialize session state
if 'tickers' not in st.session_state:
    st.session_state.tickers = [
        'AADI.JK', 'AALI.JK', 'ACES.JK', 'ADMR.JK', 'ADRO.JK',
        'AKRA.JK', 'AMMN.JK', 'AMRT.JK', 'ANTM.JK', 'ASGR.JK',
        'ASII.JK', 'AUTO.JK', 'BBCA.JK', 'BBNI.JK', 'BBRI.JK',
        'BBTN.JK', 'BIRD.JK', 'BMRI.JK', 'BNGA.JK', 'BTPS.JK',
        'CFIN.JK', 'CMRY.JK', 'CPIN.JK', 'DLTA.JK', 'EMTK.JK',
        'ESSA.JK', 'GJTL.JK', 'HEAL.JK', 'HRTA.JK', 'ICBP.JK',
        'INCO.JK', 'INDF.JK', 'INKP.JK', 'IPCC.JK', 'ISAT.JK',
        'ITMG.JK', 'JPFA.JK', 'KLBF.JK', 'MAPI.JK', 'MARK.JK',
        'MBMA.JK', 'MDKA.JK', 'MEDC.JK', 'MIKA.JK', 'NISP.JK',
        'OMED.JK', 'PGAS.JK', 'PGEO.JK', 'POWR.JK', 'PTBA.JK',
        'RALS.JK', 'SCMA.JK', 'SIDO.JK', 'SMSM.JK', 'SPTO.JK',
        'TLKM.JK', 'TOTO.JK', 'TOWR.JK', 'TSPC.JK', 'UNTR.JK',
        'UNVR.JK'
    ]
    st.session_state.tickers.sort()

if 'indicator_params' not in st.session_state:
    st.session_state.indicator_params = {
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'rsi_trend': 50,
        'sma_short': 20,
        'sma_long': 50,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'stoch_window': 14,
        'stoch_smooth': 3,
        'stoch_oversold': 20,
        'stoch_overbought': 80,
        'bb_window': 20,
        'bb_std': 2.0,
        'obv_sma_period': 10,
        'obv_trend_period': 5,
        'adx_period': 14,
        'adx_threshold': 25,
        'atr_period': 14,
        'atr_stop_multiple': 1.5,
        'atr_target_multiple': 2.0,
        'backtest_days': 90
    }

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'buy_signals' not in st.session_state:
    st.session_state.buy_signals = None
if 'sell_signals' not in st.session_state:
    st.session_state.sell_signals = None
if 'backtest_data' not in st.session_state:
    st.session_state.backtest_data = {}

# ============================================================
# TOP LEFT: Scan Button
# ============================================================
col_scan, col_empty = st.columns([1, 3])
with col_scan:
    st.divider()
    scan_button = st.button("🔍 Run Enhanced Scan", type="primary", use_container_width=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Ticker Management
    st.subheader("📋 Ticker Management")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add ticker", placeholder="e.g., GOTO.JK", key="new_ticker")
    with col2:
        if st.button("Add", use_container_width=True):
            if new_ticker and new_ticker.upper() not in st.session_state.tickers:
                st.session_state.tickers.append(new_ticker.upper())
                st.session_state.tickers.sort()
                st.rerun()

    # Edit/Delete ticker
    ticker_to_edit = st.selectbox("Edit/Delete ticker", st.session_state.tickers, key="edit_select")
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
            "RSI Period", 2, 50, st.session_state.indicator_params['rsi_period']
        )
        st.session_state.indicator_params['rsi_oversold'] = st.slider(
            "RSI Oversold (BUY)", 10, 40, st.session_state.indicator_params['rsi_oversold']
        )
        st.session_state.indicator_params['rsi_overbought'] = st.slider(
            "RSI Overbought (SELL)", 60, 90, st.session_state.indicator_params['rsi_overbought']
        )
        st.session_state.indicator_params['rsi_trend'] = st.slider(
            "RSI Trend Threshold", 40, 70, st.session_state.indicator_params['rsi_trend']
        )

    with st.expander("Moving Averages", expanded=False):
        st.session_state.indicator_params['sma_short'] = st.number_input(
            "Short SMA", 5, 50, st.session_state.indicator_params['sma_short']
        )
        st.session_state.indicator_params['sma_long'] = st.number_input(
            "Long SMA", 20, 200, st.session_state.indicator_params['sma_long']
        )

    with st.expander("MACD Settings", expanded=False):
        st.session_state.indicator_params['macd_fast'] = st.number_input(
            "MACD Fast", 5, 20, st.session_state.indicator_params['macd_fast']
        )
        st.session_state.indicator_params['macd_slow'] = st.number_input(
            "MACD Slow", 15, 40, st.session_state.indicator_params['macd_slow']
        )
        st.session_state.indicator_params['macd_signal'] = st.number_input(
            "MACD Signal", 5, 15, st.session_state.indicator_params['macd_signal']
        )

    with st.expander("Stochastic Settings", expanded=False):
        st.session_state.indicator_params['stoch_window'] = st.number_input(
            "Stoch %K Period", 5, 30, st.session_state.indicator_params['stoch_window']
        )
        st.session_state.indicator_params['stoch_smooth'] = st.number_input(
            "Stoch %K Smooth", 2, 5, st.session_state.indicator_params['stoch_smooth']
        )
        st.session_state.indicator_params['stoch_oversold'] = st.slider(
            "Stoch Oversold (BUY)", 10, 30, st.session_state.indicator_params['stoch_oversold']
        )
        st.session_state.indicator_params['stoch_overbought'] = st.slider(
            "Stoch Overbought (SELL)", 70, 90, st.session_state.indicator_params['stoch_overbought']
        )

    with st.expander("Bollinger Bands", expanded=False):
        st.session_state.indicator_params['bb_window'] = st.number_input(
            "BB Period", 10, 50, st.session_state.indicator_params['bb_window']
        )
        st.session_state.indicator_params['bb_std'] = st.slider(
            "BB Std Dev", 1.0, 3.0, float(st.session_state.indicator_params['bb_std']), 0.5
        )

    with st.expander("OBV Settings", expanded=False):
        st.session_state.indicator_params['obv_sma_period'] = st.number_input(
            "OBV SMA Period", 5, 30, st.session_state.indicator_params['obv_sma_period']
        )
        st.session_state.indicator_params['obv_trend_period'] = st.number_input(
            "OBV Trend Period", 3, 20, st.session_state.indicator_params['obv_trend_period']
        )

    with st.expander("ADX & ATR Settings", expanded=False):
        st.session_state.indicator_params['adx_period'] = st.number_input(
            "ADX Period", 7, 30, st.session_state.indicator_params['adx_period']
        )
        st.session_state.indicator_params['adx_threshold'] = st.slider(
            "ADX Threshold", 15, 40, st.session_state.indicator_params['adx_threshold']
        )
        st.session_state.indicator_params['atr_period'] = st.number_input(
            "ATR Period", 7, 30, st.session_state.indicator_params['atr_period']
        )
        st.session_state.indicator_params['atr_stop_multiple'] = st.slider(
            "ATR Stop Multiple", 1.0, 3.0, float(st.session_state.indicator_params['atr_stop_multiple']), 0.1
        )
        st.session_state.indicator_params['atr_target_multiple'] = st.slider(
            "ATR Target Multiple", 1.0, 4.0, float(st.session_state.indicator_params['atr_target_multiple']), 0.1
        )

    with st.expander("Backtest Settings", expanded=False):
        st.session_state.indicator_params['backtest_days'] = st.number_input(
            "Backtest Period (days)", 30, 365, st.session_state.indicator_params['backtest_days']
        )

# Main content
if scan_button:
    with st.spinner("Running enhanced technical analysis scan for BUY & SELL signals..."):
        params = st.session_state.indicator_params

        BACKTEST_END_DATE = pd.Timestamp.now() - pd.Timedelta(days=1)
        BACKTEST_START_DATE = BACKTEST_END_DATE - pd.Timedelta(days=params['backtest_days'])
        BACKTEST_END_DATE_STR = BACKTEST_END_DATE.strftime('%Y-%m-%d')
        BACKTEST_START_DATE_STR = BACKTEST_START_DATE.strftime('%Y-%m-%d')

        # BUY signals containers
        buy_signals = {
            'Mean Reversion': [],
            'Trend Following': [],
            'MACD Crossover': [],
            'Stochastic Oversold': [],
            'Bollinger Band Reversion': [],
            'OBV Accumulation': []
        }

        # SELL signals containers
        sell_signals = {
            'Mean Reversion': [],
            'Trend Reversal': [],
            'MACD Bearish Crossover': [],
            'Stochastic Overbought': [],
            'Bollinger Band Overbought': [],
            'OBV Distribution': []
        }

        backtest_data = {}

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, ticker in enumerate(st.session_state.tickers):
            try:
                status_text.text(f"Processing {ticker} ({idx + 1}/{len(st.session_state.tickers)})")

                data = yf.Ticker(ticker).history(start=BACKTEST_START_DATE_STR, end=BACKTEST_END_DATE_STR)

                if data.index.tz is not None:
                    data.index = data.index.tz_convert(None)

                min_periods = max(params['sma_long'], params['macd_slow'], params['bb_window'])
                if data.empty or len(data) < min_periods:
                    continue

                # Calculate all indicators
                rsi = ta.momentum.rsi(data['Close'], window=params['rsi_period'])
                sma_short = data['Close'].rolling(window=params['sma_short']).mean()
                sma_long = data['Close'].rolling(window=params['sma_long']).mean()
                volume_sma = data['Volume'].rolling(window=params['sma_short']).mean()

                macd_line = ta.trend.macd(data['Close'], window_slow=params['macd_slow'],
                                          window_fast=params['macd_fast'])
                macd_signal_line = ta.trend.macd_signal(data['Close'], window_slow=params['macd_slow'],
                                                        window_fast=params['macd_fast'],
                                                        window_sign=params['macd_signal'])
                macd_histogram = ta.trend.macd_diff(data['Close'], window_slow=params['macd_slow'],
                                                    window_fast=params['macd_fast'],
                                                    window_sign=params['macd_signal'])

                adx = ta.trend.adx(data['High'], data['Low'], data['Close'],
                                   window=params['adx_period'])

                stoch_k = ta.momentum.stoch(data['High'], data['Low'], data['Close'],
                                            window=params['stoch_window'],
                                            smooth_window=params['stoch_smooth'])
                stoch_d = ta.momentum.stoch_signal(data['High'], data['Low'], data['Close'],
                                                   window=params['stoch_window'],
                                                   smooth_window=params['stoch_smooth'])

                bb_upper = ta.volatility.bollinger_hband(data['Close'], window=params['bb_window'],
                                                         window_dev=params['bb_std'])
                bb_middle = ta.volatility.bollinger_mavg(data['Close'], window=params['bb_window'])
                bb_low = ta.volatility.bollinger_lband(data['Close'], window=params['bb_window'],
                                                       window_dev=params['bb_std'])
                bb_width = (bb_upper - bb_low) / bb_middle

                atr = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'],
                                                       window=params['atr_period'])

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
                    'adx': adx,
                    'stoch_k': stoch_k,
                    'stoch_d': stoch_d,
                    'bb_upper': bb_upper,
                    'bb_middle': bb_middle,
                    'bb_low': bb_low,
                    'bb_width': bb_width,
                    'atr': atr,
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
                last_macd_histogram = macd_histogram.iloc[-1]
                last_adx = adx.iloc[-1]
                last_stoch_k = stoch_k.iloc[-1]
                last_stoch_d = stoch_d.iloc[-1]
                last_bb_upper = bb_upper.iloc[-1]
                last_bb_low = bb_low.iloc[-1]
                last_bb_middle = bb_middle.iloc[-1]
                last_bb_width = bb_width.iloc[-1]
                last_atr = atr.iloc[-1]
                last_obv = obv.iloc[-1]
                last_obv_sma = obv_sma.iloc[-1]

                # Previous values for crossover detection
                prev_close = data['Close'].iloc[-2]
                prev_rsi = rsi.iloc[-2]
                prev_macd = macd_line.iloc[-2]
                prev_macd_signal = macd_signal_line.iloc[-2]
                prev_stoch_k = stoch_k.iloc[-2]
                prev_stoch_d = stoch_d.iloc[-2]
                prev_obv = obv.iloc[-2]
                prev_volume = data['Volume'].iloc[-2]

                obv_trend_ago = obv.iloc[-params['obv_trend_period']]

                signal_date = pd.to_datetime(BACKTEST_END_DATE_STR)

                # Dynamic stops/targets using ATR
                dynamic_stop_loss_buy = last_close - (params['atr_stop_multiple'] * last_atr)
                dynamic_take_profit_buy = last_close + (params['atr_target_multiple'] * last_atr)
                risk_reward_buy = f"1:{params['atr_target_multiple'] / params['atr_stop_multiple']:.1f}"

                # For SELL signals, reverse the logic
                dynamic_stop_loss_sell = last_close + (params['atr_stop_multiple'] * last_atr)
                dynamic_take_profit_sell = last_close - (params['atr_target_multiple'] * last_atr)
                risk_reward_sell = f"1:{params['atr_target_multiple'] / params['atr_stop_multiple']:.1f}"

                # ====================================================
                # BUY SIGNALS
                # ====================================================

                # Strategy 1: Mean Reversion BUY
                if (not pd.isna(last_rsi) and not pd.isna(prev_rsi) and
                        last_rsi < params['rsi_oversold'] and prev_rsi < params['rsi_oversold'] and
                        last_close < last_sma_short and last_volume > last_volume_sma and
                        last_rsi > prev_rsi):
                    buy_signals['Mean Reversion'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_buy, 2),
                        'Stop Loss': round(dynamic_stop_loss_buy, 2),
                        'Risk/Reward': risk_reward_buy,
                        'RSI': round(last_rsi, 2),
                        f'SMA{params["sma_short"]}': round(last_sma_short, 2),
                        'ATR': round(last_atr, 2),
                        'Volume Ratio': round(last_volume / last_volume_sma, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 2: Trend Following BUY
                if (not pd.isna(last_rsi) and not pd.isna(last_adx) and
                        last_rsi > params['rsi_trend'] and last_close > last_sma_short and
                        last_sma_short > last_sma_long and last_volume > last_volume_sma and
                        last_adx > params['adx_threshold']):
                    buy_signals['Trend Following'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_buy, 2),
                        'Stop Loss': round(dynamic_stop_loss_buy, 2),
                        'Risk/Reward': risk_reward_buy,
                        'RSI': round(last_rsi, 2),
                        f'SMA{params["sma_short"]}': round(last_sma_short, 2),
                        f'SMA{params["sma_long"]}': round(last_sma_long, 2),
                        'ADX': round(last_adx, 2),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 3: MACD Crossover BUY
                if (not pd.isna(last_macd) and not pd.isna(prev_macd) and
                        prev_macd <= prev_macd_signal and last_macd > last_macd_signal and
                        last_macd < 0 and last_macd_histogram > 0 and last_close > last_sma_short):
                    buy_signals['MACD Crossover'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_buy, 2),
                        'Stop Loss': round(dynamic_stop_loss_buy, 2),
                        'Risk/Reward': risk_reward_buy,
                        'MACD': round(last_macd, 4),
                        'MACD Signal': round(last_macd_signal, 4),
                        'MACD Hist': round(last_macd_histogram, 4),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 4: Stochastic Oversold BUY
                if (not pd.isna(last_stoch_k) and not pd.isna(prev_stoch_k) and
                        prev_stoch_k <= prev_stoch_d and last_stoch_k > last_stoch_d and
                        prev_stoch_k < params['stoch_oversold'] and last_stoch_k > params['stoch_oversold']):
                    buy_signals['Stochastic Oversold'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_buy, 2),
                        'Stop Loss': round(dynamic_stop_loss_buy, 2),
                        'Risk/Reward': risk_reward_buy,
                        'Stoch %K': round(last_stoch_k, 2),
                        'Stoch %D': round(last_stoch_d, 2),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 5: Bollinger Band Reversion BUY
                if (not pd.isna(last_bb_low) and not pd.isna(last_rsi) and
                        last_close < last_bb_low and last_rsi < params['rsi_oversold'] and
                        last_bb_width > bb_width.iloc[-20:].mean()):
                    buy_signals['Bollinger Band Reversion'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Take Profit': round(last_bb_middle, 2),
                        'Stop Loss': round(last_bb_low * 0.99, 2),
                        'Risk/Reward': 'Dynamic',
                        'RSI': round(last_rsi, 2),
                        'Close': round(last_close, 2),
                        'BB Lower': round(last_bb_low, 2),
                        'BB Middle': round(last_bb_middle, 2),
                        'BB Width': round(last_bb_width, 4),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 6: OBV Accumulation BUY
                if (not pd.isna(last_obv) and not pd.isna(last_obv_sma) and
                        last_obv > last_obv_sma and last_obv > obv_trend_ago and
                        last_close > last_sma_short and last_volume > last_volume_sma and
                        (last_obv > prev_obv or (last_close < prev_close and last_obv > prev_obv))):
                    buy_signals['OBV Accumulation'].append({
                        'Ticker': ticker,
                        'Buy Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_buy, 2),
                        'Stop Loss': round(dynamic_stop_loss_buy, 2),
                        'Risk/Reward': risk_reward_buy,
                        'OBV Trend': 'Rising' if last_obv > obv_trend_ago else 'Flat',
                        'OBV/SMA Ratio': round(last_obv / last_obv_sma, 2),
                        'Volume Ratio': round(last_volume / last_volume_sma, 2),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # ====================================================
                # SELL SIGNALS (Inverse logic)
                # ====================================================

                # Strategy 1: Mean Reversion SELL (Overbought reversal)
                if (not pd.isna(last_rsi) and not pd.isna(prev_rsi) and
                        last_rsi > params['rsi_overbought'] and prev_rsi > params['rsi_overbought'] and
                        last_close > last_sma_short and last_volume > last_volume_sma and
                        last_rsi < prev_rsi):  # RSI turning down
                    sell_signals['Mean Reversion'].append({
                        'Ticker': ticker,
                        'Sell Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_sell, 2),
                        'Stop Loss': round(dynamic_stop_loss_sell, 2),
                        'Risk/Reward': risk_reward_sell,
                        'RSI': round(last_rsi, 2),
                        f'SMA{params["sma_short"]}': round(last_sma_short, 2),
                        'ATR': round(last_atr, 2),
                        'Volume Ratio': round(last_volume / last_volume_sma, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 2: Trend Reversal SELL (Downtrend confirmation)
                if (not pd.isna(last_rsi) and not pd.isna(last_adx) and
                        last_rsi < params['rsi_trend'] and last_close < last_sma_short and
                        last_sma_short < last_sma_long and last_volume > last_volume_sma and
                        last_adx > params['adx_threshold']):
                    sell_signals['Trend Reversal'].append({
                        'Ticker': ticker,
                        'Sell Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_sell, 2),
                        'Stop Loss': round(dynamic_stop_loss_sell, 2),
                        'Risk/Reward': risk_reward_sell,
                        'RSI': round(last_rsi, 2),
                        f'SMA{params["sma_short"]}': round(last_sma_short, 2),
                        f'SMA{params["sma_long"]}': round(last_sma_long, 2),
                        'ADX': round(last_adx, 2),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 3: MACD Bearish Crossover SELL
                if (not pd.isna(last_macd) and not pd.isna(prev_macd) and
                        prev_macd >= prev_macd_signal and last_macd < last_macd_signal and
                        last_macd > 0 and last_macd_histogram < 0 and last_close < last_sma_short):
                    sell_signals['MACD Bearish Crossover'].append({
                        'Ticker': ticker,
                        'Sell Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_sell, 2),
                        'Stop Loss': round(dynamic_stop_loss_sell, 2),
                        'Risk/Reward': risk_reward_sell,
                        'MACD': round(last_macd, 4),
                        'MACD Signal': round(last_macd_signal, 4),
                        'MACD Hist': round(last_macd_histogram, 4),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 4: Stochastic Overbought SELL
                if (not pd.isna(last_stoch_k) and not pd.isna(prev_stoch_k) and
                        prev_stoch_k >= prev_stoch_d and last_stoch_k < last_stoch_d and
                        prev_stoch_k > params['stoch_overbought'] and last_stoch_k < params['stoch_overbought']):
                    sell_signals['Stochastic Overbought'].append({
                        'Ticker': ticker,
                        'Sell Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_sell, 2),
                        'Stop Loss': round(dynamic_stop_loss_sell, 2),
                        'Risk/Reward': risk_reward_sell,
                        'Stoch %K': round(last_stoch_k, 2),
                        'Stoch %D': round(last_stoch_d, 2),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 5: Bollinger Band Overbought SELL
                if (not pd.isna(last_bb_upper) and not pd.isna(last_rsi) and
                        last_close > last_bb_upper and last_rsi > params['rsi_overbought'] and
                        last_bb_width > bb_width.iloc[-20:].mean()):
                    sell_signals['Bollinger Band Overbought'].append({
                        'Ticker': ticker,
                        'Sell Price': round(last_close, 2),
                        'Take Profit': round(last_bb_middle, 2),
                        'Stop Loss': round(last_bb_upper * 1.01, 2),
                        'Risk/Reward': 'Dynamic',
                        'RSI': round(last_rsi, 2),
                        'Close': round(last_close, 2),
                        'BB Upper': round(last_bb_upper, 2),
                        'BB Middle': round(last_bb_middle, 2),
                        'BB Width': round(last_bb_width, 4),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                # Strategy 6: OBV Distribution SELL
                if (not pd.isna(last_obv) and not pd.isna(last_obv_sma) and
                        last_obv < last_obv_sma and last_obv < obv_trend_ago and
                        last_close < last_sma_short and last_volume > last_volume_sma and
                        (last_obv < prev_obv or (last_close > prev_close and last_obv < prev_obv))):
                    sell_signals['OBV Distribution'].append({
                        'Ticker': ticker,
                        'Sell Price': round(last_close, 2),
                        'Take Profit': round(dynamic_take_profit_sell, 2),
                        'Stop Loss': round(dynamic_stop_loss_sell, 2),
                        'Risk/Reward': risk_reward_sell,
                        'OBV Trend': 'Falling' if last_obv < obv_trend_ago else 'Flat',
                        'OBV/SMA Ratio': round(last_obv / last_obv_sma, 2),
                        'Volume Ratio': round(last_volume / last_volume_sma, 2),
                        'ATR': round(last_atr, 2),
                        'Signal Date': signal_date
                    })

                progress_bar.progress((idx + 1) / len(st.session_state.tickers))

            except Exception as e:
                st.error(f"Error processing {ticker}: {str(e)}")

        status_text.text("✅ Enhanced scan complete!")
        progress_bar.empty()

        st.session_state.scan_results = {
            'start_date': BACKTEST_START_DATE_STR,
            'end_date': BACKTEST_END_DATE_STR
        }
        st.session_state.buy_signals = buy_signals
        st.session_state.sell_signals = sell_signals
        st.session_state.backtest_data = backtest_data

# Display results
if st.session_state.buy_signals is not None and st.session_state.sell_signals is not None:
    buy_signals = st.session_state.buy_signals
    sell_signals = st.session_state.sell_signals
    backtest_data = st.session_state.backtest_data
    params = st.session_state.indicator_params

    # Create two columns for BUY and SELL overview
    col_buy, col_sell = st.columns(2)

    total_buy_signals = sum(len(s) for s in buy_signals.values())
    total_sell_signals = sum(len(s) for s in sell_signals.values())

    with col_buy:
        st.metric("🟢 Total BUY Signals", total_buy_signals)
    with col_sell:
        st.metric("🔴 Total SELL Signals", total_sell_signals)

    st.divider()

    # BUY Signals Section
    st.header("🟢 BUY SIGNALS", divider="green")

    buy_tickers = set()
    for signals in buy_signals.values():
        for signal in signals:
            buy_tickers.add(signal['Ticker'])

    if buy_tickers:
        # BUY Summary Matrix
        st.subheader("BUY Signal Summary Matrix")
        buy_summary_data = []
        for ticker in sorted(buy_tickers):
            row = {'Ticker': ticker}
            for strategy in buy_signals.keys():
                row[strategy] = '✅' if any(s['Ticker'] == ticker for s in buy_signals[strategy]) else ''
            row['Total BUY'] = sum(1 for v in list(row.values())[1:] if v == '✅')
            buy_summary_data.append(row)

        df_buy_summary = pd.DataFrame(buy_summary_data)
        df_buy_summary = df_buy_summary.sort_values('Total BUY', ascending=False)
        st.dataframe(df_buy_summary, use_container_width=True, hide_index=True)

        # Detailed BUY strategies
        st.subheader("Detailed BUY Strategy Breakdown")
        buy_tabs = st.tabs(list(buy_signals.keys()))

        for tab, (strategy_name, signals) in zip(buy_tabs, buy_signals.items()):
            with tab:
                if signals:
                    st.metric(f"{strategy_name}", len(signals))
                    df = pd.DataFrame(signals)
                    if 'Signal Date' in df.columns:
                        df['Signal Date'] = df['Signal Date'].dt.strftime('%Y-%m-%d')
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    csv = df.to_csv(index=False)