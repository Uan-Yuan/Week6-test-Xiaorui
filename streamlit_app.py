import streamlit as st
import pandas as pd
import altair as alt


st.title("Xiaorui's Week6 Assignment on Nashville's Airbnb Data Visualization")
st.markdown("### Nashville Airbnb Host Evolution & Listing Performance")


@st.cache_data
def nash_airbnb():
    df = pd.read_csv('25Summer_Data_Visualization_Data/nashville.csv')
    return df

df = nash_airbnb()

#data preprocessing
# 1. 转换日期列
df['host_since'] = pd.to_datetime(df['host_since'], errors='coerce')
df['host_start_year'] = df['host_since'].dt.year
numeric_cols = ['price', 'reviews_per_month', 'review_scores_rating', 'calculated_host_listings_count']
for col in numeric_cols:
  df[col] = pd.to_numeric(df[col], errors='coerce') 
# 2. 确保数值列是正确的类型并处理缺失值
numeric_cols = ['price', 'reviews_per_month', 'review_scores_rating', 'calculated_host_listings_count']
for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 移除关键列中包含NaN的行
df.dropna(subset=numeric_cols + ['host_since', 'host_start_year'], inplace=True) # Added host_since to subset

# 3. 处理 reviews_per_month 潜在的无穷大值
df = df[df['reviews_per_month'] != float('inf')]

st.subheader("Data Info After Preprocessing")
# Capture info output and display it
import io
buffer = io.StringIO()
df.info(buf=buffer)
s = buffer.getvalue()
st.code(s) # Displays the info as a code block in Streamlit

# Alternatively, just print to console for debugging:
# print(df.info())

st.subheader("First 5 Rows After Preprocessing")
st.dataframe(df.head()) # Displays a DataFrame in Streamlit