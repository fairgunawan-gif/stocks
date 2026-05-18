import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Fundamental Analysis Scanner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Fundamental Analysis Scanner")
st.markdown("Analyze stocks based on key fundamental ratios")

# Initialize session state for tickers
if 'fundamental_tickers' not in st.session_state:
    st.session_state.fundamental_tickers = [
        'AALI.JK', 'ARTO.JK', 'ASGR.JK', 'ASII.JK', 'AUTO.JK',
        'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BBTN.JK', 'BDMN.JK',
        'BJBR.JK', 'BJTM.JK', 'BMRI.JK', 'BNGA.JK', 'BNLI.JK',
        'BRIS.JK', 'BTPS.JK', 'BTPN.JK', 'HEAL.JK', 'ICBP.JK',
        'INDF.JK', 'KLBF.JK', 'MARK.JK', 'MIKA.JK', 'NISP.JK',
        'OMED.JK', 'PNBN.JK', 'POWR.JK', 'SIDO.JK', 'SMSM.JK',
        'TLKM.JK', 'TSPC.JK', 'UNTR.JK', 'MLBI.JK', 'DLTA.JK',
    ]
    st.session_state.fundamental_tickers.sort()

# Initialize session state for ratio thresholds
if 'ratio_thresholds' not in st.session_state:
    st.session_state.ratio_thresholds = {
        'per_max': 15.0,
        'pbv_max': 3.0,
        'quick_ratio_min': 1.0,
        'debt_ratio_max': 0.5,
        'roa_min': 5.0,
        'roe_min': 15.0,
        'gpm_min': 20.0,
        'opm_min': 10.0,
        'npm_min': 5.0
    }

# Initialize session state for analysis results
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None


# Function to get financial data
@st.cache_data(ttl=3600)
def get_financial_data(ticker):
    try:
        stock = yf.Ticker(ticker)

        # Get financial statements
        info = stock.info

        # Get balance sheet
        balance_sheet = stock.balance_sheet
        if balance_sheet.empty:
            balance_sheet = stock.quarterly_balance_sheet

        # Get income statement
        income_stmt = stock.financials
        if income_stmt.empty:
            income_stmt = stock.quarterly_financials

        # Get cash flow
        cash_flow = stock.cashflow
        if cash_flow.empty:
            cash_flow = stock.quarterly_cashflow

        return {
            'info': info,
            'balance_sheet': balance_sheet,
            'income_stmt': income_stmt,
            'cash_flow': cash_flow
        }
    except Exception as e:
        return None


# Function to calculate financial ratios
def calculate_ratios(data):
    if data is None:
        return None

    try:
        info = data['info']
        balance_sheet = data['balance_sheet']
        income_stmt = data['income_stmt']
        cash_flow = data['cash_flow']

        ratios = {}

        # Market Data
        ratios['Current Price'] = info.get('currentPrice', info.get('regularMarketPrice', None))
        ratios['Market Cap'] = info.get('marketCap', None)

        # PER (Price to Earnings Ratio)
        ratios['PER'] = info.get('trailingPE', info.get('forwardPE', None))

        # PBV (Price to Book Value)
        ratios['PBV'] = info.get('priceToBook', None)

        # Quick Ratio
        if not balance_sheet.empty:
            current_assets = balance_sheet.loc['Current Assets'].iloc[
                0] if 'Current Assets' in balance_sheet.index else None
            inventory = balance_sheet.loc['Inventory'].iloc[0] if 'Inventory' in balance_sheet.index else 0
            current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[
                0] if 'Current Liabilities' in balance_sheet.index else None

            if current_assets and current_liabilities:
                ratios['Quick Ratio'] = round((current_assets - inventory) / current_liabilities, 2)
            else:
                ratios['Quick Ratio'] = info.get('quickRatio', None)
        else:
            ratios['Quick Ratio'] = info.get('quickRatio', None)

        # Debt Ratio
        if not balance_sheet.empty:
            total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else None
            total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else None

            if total_assets and total_debt:
                ratios['Debt Ratio'] = round(total_debt / total_assets, 4)
            else:
                ratios['Debt Ratio'] = info.get('debtToEquity', None)
                if ratios['Debt Ratio']:
                    ratios['Debt Ratio'] = round(ratios['Debt Ratio'] / (1 + ratios['Debt Ratio']), 4)
        else:
            debt_to_equity = info.get('debtToEquity', None)
            if debt_to_equity:
                ratios['Debt Ratio'] = round(debt_to_equity / (1 + debt_to_equity), 4)
            else:
                ratios['Debt Ratio'] = None

        # ROA (Return on Assets)
        ratios['ROA'] = info.get('returnOnAssets', None)
        if ratios['ROA']:
            ratios['ROA'] = round(ratios['ROA'] * 100, 2)

        # ROE (Return on Equity)
        ratios['ROE'] = info.get('returnOnEquity', None)
        if ratios['ROE']:
            ratios['ROE'] = round(ratios['ROE'] * 100, 2)

        # Profitability Ratios from Income Statement
        if not income_stmt.empty:
            total_revenue = income_stmt.loc['Total Revenue'].iloc[0] if 'Total Revenue' in income_stmt.index else None
            gross_profit = income_stmt.loc['Gross Profit'].iloc[0] if 'Gross Profit' in income_stmt.index else None
            operating_income = income_stmt.loc['Operating Income'].iloc[
                0] if 'Operating Income' in income_stmt.index else None
            net_income = income_stmt.loc['Net Income'].iloc[0] if 'Net Income' in income_stmt.index else None

            # GPM (Gross Profit Margin)
            if total_revenue and gross_profit:
                ratios['GPM'] = round((gross_profit / total_revenue) * 100, 2)
            else:
                ratios['GPM'] = info.get('grossMargins', None)
                if ratios['GPM']:
                    ratios['GPM'] = round(ratios['GPM'] * 100, 2)

            # OPM (Operating Profit Margin)
            if total_revenue and operating_income:
                ratios['OPM'] = round((operating_income / total_revenue) * 100, 2)
            else:
                ratios['OPM'] = info.get('operatingMargins', None)
                if ratios['OPM']:
                    ratios['OPM'] = round(ratios['OPM'] * 100, 2)

            # NPM (Net Profit Margin)
            if total_revenue and net_income:
                ratios['NPM'] = round((net_income / total_revenue) * 100, 2)
            else:
                ratios['NPM'] = info.get('profitMargins', None)
                if ratios['NPM']:
                    ratios['NPM'] = round(ratios['NPM'] * 100, 2)

        # Additional useful ratios
        ratios['Dividend Yield'] = info.get('dividendYield', None)
        if ratios['Dividend Yield']:
            ratios['Dividend Yield'] = round(ratios['Dividend Yield'] * 100, 2)

        ratios['EPS'] = info.get('trailingEps', None)
        ratios['Beta'] = info.get('beta', None)

        # Company info
        ratios['Sector'] = info.get('sector', 'N/A')
        ratios['Industry'] = info.get('industry', 'N/A')

        return ratios

    except Exception as e:
        return None


# Function to create radar chart for a ticker
def create_radar_chart(ticker_data):
    categories = ['Valuation', 'Liquidity', 'Solvency', 'ROA', 'ROE', 'GPM', 'OPM', 'NPM']

    # Normalize values for radar chart (0-100 scale)
    values = []

    # Valuation Score (inverse - lower is better)
    per_val = ticker_data['PER'] if pd.notna(ticker_data['PER']) else None
    pbv_val = ticker_data['PBV'] if pd.notna(ticker_data['PBV']) else None
    if per_val and pbv_val:
        val_score = max(0, 100 - (per_val / 30 * 50 + pbv_val / 5 * 50))
    else:
        val_score = 50
    values.append(round(val_score, 1))

    # Liquidity Score
    qr_val = ticker_data['Quick Ratio'] if pd.notna(ticker_data['Quick Ratio']) else None
    if qr_val:
        liq_score = min(100, qr_val * 50)
    else:
        liq_score = 50
    values.append(round(liq_score, 1))

    # Solvency Score (inverse - lower debt is better)
    dr_val = ticker_data['Debt Ratio'] if pd.notna(ticker_data['Debt Ratio']) else None
    if dr_val:
        solv_score = max(0, 100 - dr_val * 200)
    else:
        solv_score = 50
    values.append(round(solv_score, 1))

    # ROA Score
    roa_val = ticker_data['ROA (%)'] if pd.notna(ticker_data['ROA (%)']) else None
    if roa_val:
        roa_score = min(100, roa_val * 5)
    else:
        roa_score = 50
    values.append(round(roa_score, 1))

    # ROE Score
    roe_val = ticker_data['ROE (%)'] if pd.notna(ticker_data['ROE (%)']) else None
    if roe_val:
        roe_score = min(100, roe_val * 3)
    else:
        roe_score = 50
    values.append(round(roe_score, 1))

    # GPM Score
    gpm_val = ticker_data['GPM (%)'] if pd.notna(ticker_data['GPM (%)']) else None
    if gpm_val:
        gpm_score = min(100, gpm_val * 2)
    else:
        gpm_score = 50
    values.append(round(gpm_score, 1))

    # OPM Score
    opm_val = ticker_data['OPM (%)'] if pd.notna(ticker_data['OPM (%)']) else None
    if opm_val:
        opm_score = min(100, opm_val * 3)
    else:
        opm_score = 50
    values.append(round(opm_score, 1))

    # NPM Score
    npm_val = ticker_data['NPM (%)'] if pd.notna(ticker_data['NPM (%)']) else None
    if npm_val:
        npm_score = min(100, npm_val * 5)
    else:
        npm_score = 50
    values.append(round(npm_score, 1))

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=ticker_data['Ticker'],
        line=dict(color='blue')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=400,
        margin=dict(l=80, r=80, t=20, b=20)
    )

    return fig


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
            if new_ticker and new_ticker.upper() not in st.session_state.fundamental_tickers:
                st.session_state.fundamental_tickers.append(new_ticker.upper())
                st.session_state.fundamental_tickers.sort()
                st.rerun()
            elif new_ticker:
                st.warning("Ticker already exists!")

    # Edit ticker
    ticker_to_edit = st.selectbox("Select ticker to edit", st.session_state.fundamental_tickers, key="edit_select")
    edited_ticker = st.text_input("Edit ticker", value=ticker_to_edit if ticker_to_edit else "", key="edit_ticker")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update", use_container_width=True):
            if edited_ticker and edited_ticker != ticker_to_edit:
                idx = st.session_state.fundamental_tickers.index(ticker_to_edit)
                st.session_state.fundamental_tickers[idx] = edited_ticker.upper()
                st.session_state.fundamental_tickers.sort()
                st.rerun()
    with col2:
        if st.button("Delete", use_container_width=True):
            if ticker_to_edit in st.session_state.fundamental_tickers:
                st.session_state.fundamental_tickers.remove(ticker_to_edit)
                st.rerun()

    st.divider()

    # Screening Criteria
    st.subheader("📊 Screening Criteria")
    st.caption("Set thresholds for filtering stocks")

    # Valuation Ratios
    with st.expander("Valuation Ratios", expanded=False):
        st.session_state.ratio_thresholds['per_max'] = st.number_input(
            "Max PER", min_value=0.0, max_value=100.0, step=0.5,
            value=st.session_state.ratio_thresholds['per_max'],
            help="Price to Earnings Ratio - lower is generally better"
        )
        st.session_state.ratio_thresholds['pbv_max'] = st.number_input(
            "Max PBV", min_value=0.0, max_value=10.0, step=0.1,
            value=st.session_state.ratio_thresholds['pbv_max'],
            help="Price to Book Value - lower is generally better"
        )

    # Liquidity & Solvency
    with st.expander("Liquidity & Solvency", expanded=False):
        st.session_state.ratio_thresholds['quick_ratio_min'] = st.number_input(
            "Min Quick Ratio", min_value=0.0, max_value=5.0, step=0.1,
            value=st.session_state.ratio_thresholds['quick_ratio_min'],
            help="Quick Ratio - higher is better (>1 is healthy)"
        )
        st.session_state.ratio_thresholds['debt_ratio_max'] = st.number_input(
            "Max Debt Ratio", min_value=0.0, max_value=1.0, step=0.05,
            value=st.session_state.ratio_thresholds['debt_ratio_max'],
            help="Debt to Assets Ratio - lower is better"
        )

    # Profitability
    with st.expander("Profitability Ratios", expanded=False):
        st.session_state.ratio_thresholds['roa_min'] = st.number_input(
            "Min ROA (%)", min_value=0.0, max_value=50.0, step=0.5,
            value=st.session_state.ratio_thresholds['roa_min'],
            help="Return on Assets - higher is better"
        )
        st.session_state.ratio_thresholds['roe_min'] = st.number_input(
            "Min ROE (%)", min_value=0.0, max_value=100.0, step=0.5,
            value=st.session_state.ratio_thresholds['roe_min'],
            help="Return on Equity - higher is better"
        )

    # Margins
    with st.expander("Profit Margins", expanded=False):
        st.session_state.ratio_thresholds['gpm_min'] = st.number_input(
            "Min GPM (%)", min_value=0.0, max_value=100.0, step=0.5,
            value=st.session_state.ratio_thresholds['gpm_min'],
            help="Gross Profit Margin"
        )
        st.session_state.ratio_thresholds['opm_min'] = st.number_input(
            "Min OPM (%)", min_value=0.0, max_value=100.0, step=0.5,
            value=st.session_state.ratio_thresholds['opm_min'],
            help="Operating Profit Margin"
        )
        st.session_state.ratio_thresholds['npm_min'] = st.number_input(
            "Min NPM (%)", min_value=0.0, max_value=100.0, step=0.5,
            value=st.session_state.ratio_thresholds['npm_min'],
            help="Net Profit Margin"
        )

    # Scan button
    st.divider()
    scan_button = st.button("🔍 Run Fundamental Analysis", type="primary", use_container_width=True)

    # Quick presets
    st.subheader("💡 Quick Presets")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Value Stocks", use_container_width=True):
            st.session_state.ratio_thresholds.update({
                'per_max': 15.0, 'pbv_max': 1.5, 'quick_ratio_min': 1.0,
                'debt_ratio_max': 0.5, 'roa_min': 5.0, 'roe_min': 15.0,
                'gpm_min': 20.0, 'opm_min': 10.0, 'npm_min': 5.0
            })
            st.rerun()
    with col2:
        if st.button("Growth Stocks", use_container_width=True):
            st.session_state.ratio_thresholds.update({
                'per_max': 30.0, 'pbv_max': 5.0, 'quick_ratio_min': 1.0,
                'debt_ratio_max': 0.4, 'roa_min': 10.0, 'roe_min': 20.0,
                'gpm_min': 30.0, 'opm_min': 15.0, 'npm_min': 10.0
            })
            st.rerun()

# Main content area
if scan_button:
    with st.spinner("Analyzing fundamental data..."):
        thresholds = st.session_state.ratio_thresholds

        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []

        for idx, ticker in enumerate(st.session_state.fundamental_tickers):
            status_text.text(f"Analyzing {ticker}... ({idx + 1}/{len(st.session_state.fundamental_tickers)})")

            # Fetch and analyze data
            data = get_financial_data(ticker)
            ratios = calculate_ratios(data)

            if ratios:
                # Apply screening criteria
                passed = True
                fail_reasons = []

                # Check PER
                if ratios.get('PER'):
                    if ratios['PER'] > thresholds['per_max']:
                        fail_reasons.append(f"PER too high ({ratios['PER']:.2f})")

                # Check PBV
                if ratios.get('PBV'):
                    if ratios['PBV'] > thresholds['pbv_max']:
                        fail_reasons.append(f"PBV too high ({ratios['PBV']:.2f})")

                # Check Quick Ratio
                if ratios.get('Quick Ratio'):
                    if ratios['Quick Ratio'] < thresholds['quick_ratio_min']:
                        fail_reasons.append(f"Quick Ratio too low ({ratios['Quick Ratio']:.2f})")

                # Check Debt Ratio
                if ratios.get('Debt Ratio'):
                    if ratios['Debt Ratio'] > thresholds['debt_ratio_max']:
                        fail_reasons.append(f"Debt Ratio too high ({ratios['Debt Ratio']:.2f})")

                # Check ROA
                if ratios.get('ROA'):
                    if ratios['ROA'] < thresholds['roa_min']:
                        fail_reasons.append(f"ROA too low ({ratios['ROA']:.2f}%)")

                # Check ROE
                if ratios.get('ROE'):
                    if ratios['ROE'] < thresholds['roe_min']:
                        fail_reasons.append(f"ROE too low ({ratios['ROE']:.2f}%)")

                # Check GPM
                if ratios.get('GPM'):
                    if ratios['GPM'] < thresholds['gpm_min']:
                        fail_reasons.append(f"GPM too low ({ratios['GPM']:.2f}%)")

                # Check OPM
                if ratios.get('OPM'):
                    if ratios['OPM'] < thresholds['opm_min']:
                        fail_reasons.append(f"OPM too low ({ratios['OPM']:.2f}%)")

                # Check NPM
                if ratios.get('NPM'):
                    if ratios['NPM'] < thresholds['npm_min']:
                        fail_reasons.append(f"NPM too low ({ratios['NPM']:.2f}%)")

                # Add to results
                result_entry = {
                    'Ticker': ticker,
                    'Company': data['info'].get('longName', ticker),
                    'Sector': ratios.get('Sector', 'N/A'),
                    'Current Price': ratios.get('Current Price'),
                    'Market Cap': ratios.get('Market Cap'),
                    'PER': ratios.get('PER'),
                    'PBV': ratios.get('PBV'),
                    'Quick Ratio': ratios.get('Quick Ratio'),
                    'Debt Ratio': ratios.get('Debt Ratio'),
                    'ROA (%)': ratios.get('ROA'),
                    'ROE (%)': ratios.get('ROE'),
                    'GPM (%)': ratios.get('GPM'),
                    'OPM (%)': ratios.get('OPM'),
                    'NPM (%)': ratios.get('NPM'),
                    'Dividend Yield (%)': ratios.get('Dividend Yield'),
                    'EPS': ratios.get('EPS'),
                    'Beta': ratios.get('Beta'),
                    'Pass': '✅' if len(fail_reasons) == 0 else '❌',
                    'Failed Criteria': ', '.join(fail_reasons) if fail_reasons else 'All Passed',
                    'Score': max(0, 9 - len(fail_reasons))
                }

                results.append(result_entry)

            progress_bar.progress((idx + 1) / len(st.session_state.fundamental_tickers))

        status_text.text("Analysis complete!")
        progress_bar.empty()

        # Store results in session state
        st.session_state.analysis_results = results

# Display results if available
if st.session_state.analysis_results is not None:
    results = st.session_state.analysis_results

    if results:
        df_results = pd.DataFrame(results)

        # Sort by score (descending)
        df_results = df_results.sort_values('Score', ascending=False)

        # Display Results
        st.header("📊 Fundamental Analysis Results")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Analyzed", len(df_results))
        with col2:
            passed_count = len(df_results[df_results['Pass'] == '✅'])
            st.metric("Passed Screening", passed_count)
        with col3:
            pass_rate = (passed_count / len(df_results)) * 100 if len(df_results) > 0 else 0
            st.metric("Pass Rate", f"{pass_rate:.1f}%")
        with col4:
            avg_score = df_results['Score'].mean() if len(df_results) > 0 else 0
            st.metric("Avg Score", f"{avg_score:.1f}/9")

        # Screening Passed Table
        st.subheader("✅ Screening Passed")
        df_passed = df_results[df_results['Pass'] == '✅']

        if not df_passed.empty:
            # Format columns for display
            display_columns = [
                'Ticker', 'Company', 'Sector', 'Current Price', 'PER', 'PBV',
                'Quick Ratio', 'Debt Ratio', 'ROA (%)', 'ROE (%)',
                'GPM (%)', 'OPM (%)', 'NPM (%)', 'Score'
            ]

            # Format the dataframe
            df_display = df_passed[display_columns].copy()

            # Format numbers
            for col in ['Current Price', 'PER', 'PBV', 'Quick Ratio', 'Debt Ratio',
                        'ROA (%)', 'ROE (%)', 'GPM (%)', 'OPM (%)', 'NPM (%)']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(
                        lambda x: f'{x:.2f}' if pd.notna(x) and isinstance(x, (int, float)) else 'N/A'
                    )

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Color-coded visualization
            st.subheader("📈 Ratio Visualization (Passed Stocks)")

            # Get list of passed tickers
            passed_tickers = df_passed['Ticker'].tolist()

            # Create a key for the selectbox to maintain state
            if 'selected_ticker' not in st.session_state:
                st.session_state.selected_ticker = passed_tickers[0] if passed_tickers else None


            # Use a callback function to update the chart
            def on_ticker_change():
                st.session_state.selected_ticker = st.session_state.ticker_selectbox


            # Select ticker for detailed view with callback
            selected_ticker = st.selectbox(
                "Select ticker for detailed analysis",
                passed_tickers,
                key="ticker_selectbox",
                on_change=on_ticker_change,
                index=passed_tickers.index(
                    st.session_state.selected_ticker) if st.session_state.selected_ticker in passed_tickers else 0
            )

            # Update selected ticker
            if selected_ticker and selected_ticker != st.session_state.selected_ticker:
                st.session_state.selected_ticker = selected_ticker

            # Display chart for selected ticker
            if st.session_state.selected_ticker and st.session_state.selected_ticker in df_passed['Ticker'].values:
                ticker_data = df_passed[df_passed['Ticker'] == st.session_state.selected_ticker].iloc[0]

                # Display company info
                st.write(f"**{ticker_data['Company']}** ({ticker_data['Ticker']})")
                st.write(f"Sector: {ticker_data['Sector']} | Score: {ticker_data['Score']}/9")

                # Create and display radar chart
                fig = create_radar_chart(ticker_data)
                st.plotly_chart(fig, use_container_width=True, key=f"radar_{st.session_state.selected_ticker}")

                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("PER", f"{ticker_data['PER']:.2f}" if pd.notna(ticker_data['PER']) else "N/A")
                with col2:
                    st.metric("PBV", f"{ticker_data['PBV']:.2f}" if pd.notna(ticker_data['PBV']) else "N/A")
                with col3:
                    st.metric("ROE", f"{ticker_data['ROE (%)']:.2f}%" if pd.notna(ticker_data['ROE (%)']) else "N/A")
                with col4:
                    st.metric("NPM", f"{ticker_data['NPM (%)']:.2f}%" if pd.notna(ticker_data['NPM (%)']) else "N/A")

            # Download button
            csv_passed = df_passed.to_csv(index=False)
            st.download_button(
                label="📥 Download Passed Results as CSV",
                data=csv_passed,
                file_name=f"fundamental_analysis_passed.csv",
                mime="text/csv"
            )
        else:
            st.info("No stocks passed the screening criteria. Try adjusting the thresholds.")

        # All Results Table
        st.subheader("📋 All Results")

        # Display all results with failed criteria
        all_display_columns = [
            'Ticker', 'Company', 'Sector', 'Current Price', 'Pass', 'Score',
            'PER', 'PBV', 'Quick Ratio', 'Debt Ratio', 'ROA (%)', 'ROE (%)',
            'GPM (%)', 'OPM (%)', 'NPM (%)', 'Failed Criteria'
        ]

        df_all_display = df_results[all_display_columns].copy()

        # Format numbers
        for col in ['Current Price', 'PER', 'PBV', 'Quick Ratio', 'Debt Ratio',
                    'ROA (%)', 'ROE (%)', 'GPM (%)', 'OPM (%)', 'NPM (%)']:
            if col in df_all_display.columns:
                df_all_display[col] = df_all_display[col].apply(
                    lambda x: float(f'{x:.2f}') if pd.notna(x) and isinstance(x, (int, float)) else 'N/A'
                )

        st.dataframe(df_all_display, use_container_width=True, hide_index=True)

        # Download all results
        csv_all = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download All Results as CSV",
            data=csv_all,
            file_name=f"fundamental_analysis_all.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data could be retrieved for the selected tickers.")

else:
    # Show instructions when no scan has been run
    st.info("👈 Configure your settings in the sidebar and click 'Run Fundamental Analysis' to start scanning.")

    # Display current configuration
    st.subheader("Current Screening Criteria")

    thresholds = st.session_state.ratio_thresholds

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Valuation:**")
        st.write(f"- PER < {thresholds['per_max']}x")
        st.write(f"- PBV < {thresholds['pbv_max']}x")
        st.write("**Liquidity & Solvency:**")
        st.write(f"- Quick Ratio > {thresholds['quick_ratio_min']}x")
        st.write(f"- Debt Ratio < {thresholds['debt_ratio_max'] * 100:.1f}%")

    with col2:
        st.write("**Profitability:**")
        st.write(f"- ROA > {thresholds['roa_min']}%")
        st.write(f"- ROE > {thresholds['roe_min']}%")
        st.write("**Margins:**")
        st.write(f"- GPM > {thresholds['gpm_min']}%")

    with col3:
        st.write("&nbsp;")
        st.write(f"- OPM > {thresholds['opm_min']}%")
        st.write(f"- NPM > {thresholds['npm_min']}%")

    # Feature overview
    st.subheader("📊 Features Overview")

    features = {
        "PER (Price to Earnings)": "Measures valuation - how much investors pay for each dollar of earnings",
        "PBV (Price to Book Value)": "Compares market value to book value - useful for financial and asset-heavy companies",
        "Quick Ratio": "Measures short-term liquidity - ability to pay current liabilities without selling inventory",
        "Debt Ratio": "Shows financial leverage - what portion of assets is financed by debt",
        "ROA (Return on Assets)": "Measures how efficiently a company uses its assets to generate profit",
        "ROE (Return on Equity)": "Shows how well management uses shareholder equity to generate returns",
        "GPM (Gross Profit Margin)": "Indicates pricing power and production efficiency",
        "OPM (Operating Profit Margin)": "Shows operational efficiency before interest and taxes",
        "NPM (Net Profit Margin)": "Measures overall profitability after all expenses"
    }

    for ratio, description in features.items():
        st.write(f"**{ratio}:** {description}")