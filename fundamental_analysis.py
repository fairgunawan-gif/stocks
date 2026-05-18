# customized fundamental analysis
import pandas as pd
from git.refs import head
from streamlit import columns

df = pd.read_csv("fundamental_analysis_20260507_092326.csv")
# print(df.head())
print(df.columns)