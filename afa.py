import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Depreciation Degressive and Linear", layout="wide")

st.title("Depreciation Degressive and Linear")

# ---------------------------------------------------
# Inputs
# ---------------------------------------------------
expense = st.number_input("Asset Cost", min_value=1.0, value=100000.0, step=1000.0)

useful_life = st.number_input(
    "Useful Life (Years)",
    min_value=1,
    value=5,
    step=1
)

deg_percent = st.number_input(
    "Degressive Percent (%)",
    min_value=1.0,
    max_value=100.0,
    value=25.0,
    step=1.0
)

purchase_date = st.date_input(
    "Purchase Date",
    value=date(date.today().year, 4, 1)
)

# ---------------------------------------------------
# Period logic
# ---------------------------------------------------
first_year_months = (
    12 - purchase_date.month + 1
    if purchase_date.day < 16
    else 12 - purchase_date.month
)

last_year_months = 12 - first_year_months

if first_year_months == 12:
    total_rows = useful_life
else:
    total_rows = useful_life + 1

purchase_year = purchase_date.year

# ---------------------------------------------------
# Calculation
# ---------------------------------------------------
rows = []
rest_value = expense
switched = False
switch_year = None

for year in range(1, total_rows + 1):

    calendar_year = purchase_year + year - 1

    # Months in current row
    if first_year_months == 12:
        months = 12
    else:
        if year == 1:
            months = first_year_months
        elif year == total_rows:
            months = last_year_months
        else:
            months = 12

    factor = months / 12

    # Remaining depreciation years
    remaining_years = sum([
        (
            first_year_months if i == 1 and first_year_months != 12
            else last_year_months if i == total_rows and first_year_months != 12
            else 12
        )
        for i in range(year, total_rows + 1)
    ]) / 12

    degressive_full = rest_value * (deg_percent / 100)
    linear_full = rest_value / remaining_years

    if not switched and linear_full > degressive_full:
        switched = True
        switch_year = calendar_year

    if switched:
        depreciation = linear_full * factor
        method = "Linear"
    else:
        depreciation = degressive_full * factor
        method = "Degressive"

    depreciation = min(depreciation, rest_value)
    rest_value -= depreciation

    rows.append({
        "Year": calendar_year,
        "Months": months,
        "Method": method,
        "Depreciation": round(depreciation, 2),
        "Rest Value": round(rest_value, 2)
    })

df = pd.DataFrame(rows)

# ---------------------------------------------------
# Table
# ---------------------------------------------------
st.subheader("Depreciation Schedule")
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# Chart
# ---------------------------------------------------
st.subheader("Remaining Book Value")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Year"], df["Rest Value"], marker="o", linewidth=2)

if switch_year:
    y = df.loc[df["Year"] == switch_year, "Rest Value"].values[0]
    ax.axvline(switch_year, linestyle="--", alpha=0.7, label="Switch Point")
    ax.scatter(switch_year, y, s=120)
    ax.legend()

ax.set_xlabel("Year")
ax.set_ylabel("Rest Value")
ax.grid(True)

st.pyplot(fig)

# ---------------------------------------------------
# Info
# ---------------------------------------------------
st.info(
    f"Purchase Date: {purchase_date.strftime('%d.%m.%Y')} | "
    f"First Period: {first_year_months} months | "
    f"Last Period: {last_year_months} months | "
    f"Total Rows: {total_rows}"
)

if switch_year:
    st.success(f"Switch from degressive to linear occurs in Year {switch_year}.")
else:
    st.info("No switching point occurred.")