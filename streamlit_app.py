import streamlit as st
import pandas as pd
import altair as alt
df = pd.read_csv("new_nashville.csv")

#app title
st.title("Xiaorui's Week6 Assignment on Nashville's Airbnb Data Visualization")
st.markdown("### Nashville Airbnb Host Evolution & Listing Performance")

#data preprocessing
df['host_since'] = pd.to_datetime(df['host_since'], format='%m/%d/%Y', errors='coerce')
df['host_start_year'] = df['host_since'].dt.year

numeric_cols = ['price', 'reviews_per_month', 'review_scores_rating', 'calculated_host_listings_count']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df.dropna(subset=numeric_cols + ['host_since', 'host_start_year'], inplace=True)

df = df[df['reviews_per_month'] != float('inf')] # Remove inf values if any

# Filter out unrealistic years (e.g., if host_start_year is too old/future)
# Adjust min/max year based on your dataset's actual range if needed
min_year = df['host_start_year'].min()
max_year = df['host_start_year'].max()
# A reasonable range for Airbnb might be from 2008 (founding) to current year
current_year = pd.Timestamp.now().year
df = df[(df['host_start_year'] >= 2008) & (df['host_start_year'] <= current_year)]
return df
df = nash_airbnb()
