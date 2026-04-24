import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Depreciation Comparison", layout="wide")

st.title("Linear vs Degressive Depreciation")

st.write("""
This app compares:

- **Linear depreciation** (recalculated each year from remaining value / remaining years)
- **Degressive depreciation** (remaining value × percent)

Each year:

1. Calculate both methods from the **same remaining value**
2. If **linear reduction > degressive reduction**
3. Then switch permanently from degressive to linear
""")

# -----------------------------
# Inputs
# -----------------------------
expense = st.number_input("Expense", min_value=1.0, value=10000.0, step=100.0)
years = st.number_input("Years of Depreciation", min_value=1, value=10, step=1)
deg_percent = st.number_input(
    "Degressive Percent (%)",
    min_value=1.0,
    max_value=100.0,
    value=25.0,
    step=1.0
)

# -----------------------------
# Iteration
# -----------------------------
rest_value = expense
linear_rest = expense

linear_line = []
switch_line = []

rows = []

switched = False
switch_year = None

for year in range(1, years + 1):

    remaining_years = years - year + 1

    # Standard linear line (original straight-line method)
    linear_standard = expense / years
    linear_rest = max(0, linear_rest - linear_standard)

    # Recalculated methods from same rest value
    linear_dynamic = rest_value / remaining_years
    degressive = rest_value * (deg_percent / 100)

    # Switch logic
    if not switched and linear_dynamic > degressive:
        switched = True
        switch_year = year

    # Use selected method
    if switched:
        depreciation = linear_dynamic
        used_method = "Linear after switch"
    else:
        depreciation = degressive
        used_method = "Degressive"

    rest_value = max(0, rest_value - depreciation)

    rows.append({
        "Year": year,
        "Remaining Years": remaining_years,
        "Linear Dynamic": round(linear_dynamic, 2),
        "Degressive": round(degressive, 2),
        "Used Method": used_method,
        "Rest Value": round(rest_value, 2)
    })

    linear_line.append(linear_rest)
    switch_line.append(rest_value)

# -----------------------------
# DataFrame
# -----------------------------
df = pd.DataFrame(rows)

st.subheader("Calculation Table")
st.dataframe(df, use_container_width=True)

# -----------------------------
# Chart
# -----------------------------
st.subheader("Rest Value Comparison")

fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(df["Year"], linear_line, marker="o", linewidth=2, label="Linear Standard")
ax.plot(df["Year"], switch_line, marker="o", linewidth=2, label="Degressive → Linear")

if switch_year:
    y = df.loc[df["Year"] == switch_year, "Rest Value"].values[0]
    ax.axvline(switch_year, linestyle="--", alpha=0.7, label="Switch Point")
    ax.scatter(switch_year, y, s=120)

ax.set_xlabel("Year")
ax.set_ylabel("Remaining Value")
ax.grid(True)
ax.legend()

st.pyplot(fig)

# -----------------------------
# Result
# -----------------------------
if switch_year:
    st.success(
        f"Switch occurs in Year {switch_year}. "
        f"At that point linear reduction becomes greater than degressive reduction."
    )
else:
    st.info("No switching point occurred.")

# -----------------------------
# Example explanation
# -----------------------------
if deg_percent == 25:
    st.info(
        "With 25% degressive rate, switch usually begins when remaining years = 4, "
        "because 1 / 4 = 25%. After that, linear becomes larger."
    )