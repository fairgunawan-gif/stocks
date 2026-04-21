import streamlit as st
import pandas as pd
import numpy as np

# Try to import centralized formatter. Fallback to local converter if unavailable.
try:
    from number_format import format_number
except Exception:
    def format_number(value, decimals: int = 2) -> str:
        if value is None:
            return ""
        try:
            s = f"{float(value):,.{decimals}f}"
        except Exception:
            try:
                s = f"{value:,.{decimals}f}"
            except Exception:
                return str(value)
        # swap: US uses ',' thousands and '.' decimal -> want '.' thousands and ',' decimal
        s = s.replace(',', '␟').replace('.', ',').replace('␟', '.')
        return s

st.set_page_config(page_title="Wealth Growth Simulator", layout="wide")

st.title("Wealth Growth Simulator (Money Market + Stocks)")

# --- Inputs ---
st.sidebar.header("Parameters")
initial_capital = st.sidebar.number_input("Initial capital (C)", min_value=0.0, value=100000.0, step=1000.0)
mm_rate = (st.sidebar.number_input("Money Market annual return (%)", value=6.0, step=0.1) / 100.0) / 12
stock_rate = (st.sidebar.number_input("Stocks annual return (%)", value=12.0, step=0.1) / 100.0) / 12
withdrawal_pct = st.sidebar.number_input("Monthly withdrawal (% of C)", value=3.0, step=0.5) / 100.0
months = st.sidebar.number_input("Number of months", min_value=1, max_value=360, value=120, step=12)

st.sidebar.markdown("---")
st.sidebar.write("Logic:")
st.sidebar.write("- Withdrawal = min(3% of C, MM_Start + MM_Interest)")
st.sidebar.write("- Stock purchase = Withdrawal")
st.sidebar.write("- Withdrawals stop when MM reaches zero")

# --- Calculation ---
data = {
    "Month": np.arange(1, months + 1),
    "MM_Start": np.zeros(months),
    "MM_Interest": np.zeros(months),
    "Withdrawal": np.zeros(months),
    "MM_End": np.zeros(months),
    "Stocks_Start": np.zeros(months),
    "Stock_Purchase": np.zeros(months),
    "Stocks_Interest": np.zeros(months),
    "Stocks_End": np.zeros(months),
    "Total": np.zeros(months),
}

df = pd.DataFrame(data)

for i in range(months):
    if i == 0:
        mm_start = initial_capital
        stocks_start = 0.0
    else:
        mm_start = df.loc[i - 1, "MM_End"]
        stocks_start = df.loc[i - 1, "Stocks_End"]

    mm_interest = mm_start * mm_rate
    desired_withdrawal = initial_capital * withdrawal_pct
    withdrawal = 0 if i == 0 else min(desired_withdrawal, mm_start + mm_interest)

    mm_end = mm_start + mm_interest - withdrawal

    stock_purchase = 0 if i == 0 else withdrawal
    stocks_interest = (stocks_start + stock_purchase) * stock_rate
    stocks_end = stocks_start + stock_purchase + stocks_interest

    total = mm_end + stocks_end

    df.loc[i, "MM_Start"] = mm_start
    df.loc[i, "MM_Interest"] = mm_interest
    df.loc[i, "Withdrawal"] = withdrawal
    df.loc[i, "MM_End"] = mm_end
    df.loc[i, "Stocks_Start"] = stocks_start
    df.loc[i, "Stock_Purchase"] = stock_purchase
    df.loc[i, "Stocks_Interest"] = stocks_interest
    df.loc[i, "Stocks_End"] = stocks_end
    df.loc[i, "Total"] = total

# --- Display ---

# Select first 5 and last 5 rows
st.subheader("Wealth Growth Table (First 5 and Last 5 Rows)")

# Ensure Month column is integer before preview
df["Month"] = df["Month"].astype("Int64")

# Create two blank rows with NaN
blank_rows = pd.DataFrame([[np.nan] * len(df.columns)] * 2, columns=df.columns)

# Build preview table
df_preview = pd.concat([
    df.head(5),
    blank_rows,
    df.tail(5)
], ignore_index=True)

# Convert Month back to nullable integer (keeps NaN allowed)
df_preview["Month"] = df_preview["Month"].astype("Int64")

# Display without index
# Format numeric columns with custom separators ('.' thousands, ',' decimal)
num_cols = [
    "MM_Start",
    "MM_Interest",
    "Withdrawal",
    "MM_End",
    "Stocks_Start",
    "Stock_Purchase",
    "Stocks_Interest",
    "Stocks_End",
    "Total",
]
for col in num_cols:
    df_preview[col] = df_preview[col].apply(lambda x: format_number(x, decimals=2) if pd.notna(x) else "")

st.dataframe(df_preview, hide_index=True)

st.subheader("Total Wealth Over Time")
st.line_chart(df.set_index("Month")[["Total", "MM_End", "Stocks_End"]])

st.subheader("Final Values")
col1, col2, col3 = st.columns(3)
col1.metric("Final Total Wealth", format_number(df['Total'].iloc[-1], decimals=2))
col2.metric("Final MM Balance", format_number(df['MM_End'].iloc[-1], decimals=2))
col3.metric("Final Stocks Value", format_number(df['Stocks_End'].iloc[-1], decimals=2))