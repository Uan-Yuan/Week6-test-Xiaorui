import streamlit as st
import pandas as pd
import altair as alt
import datetime

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_and_clean_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure it's in the correct directory.")
        return pd.DataFrame(), {}
        
    df.columns = df.columns.str.strip()

    # --- Data Cleaning and Type Conversion ---
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')
    
    if 'host_since' in df.columns:
        df['host_since'] = pd.to_datetime(df['host_since'], errors='coerce')
        df['host_start_year'] = df['host_since'].dt.year
        df['host_start_month'] = df['host_since'].dt.month
    
    # --- Filtering and Dropping Missing Data ---
    ideal_cols_pre_filter = [
        'price', 'host_since', 'host_id', 'property_type'
    ]
    cols_to_check_pre = [col for col in ideal_cols_pre_filter if col in df.columns]
    df.dropna(subset=cols_to_check_pre, inplace=True)

    # Filter by host start year
    if 'host_start_year' in df.columns:
        current_year = datetime.datetime.now().year
        df = df[(df['host_start_year'] >= 2008) & (df['host_start_year'] <= current_year)]
        df['host_start_year'] = df['host_start_year'].astype(int)
    
    price_ranges = {}
    
    # Filter out extreme prices based on 5th and 95th percentiles
    if 'price' in df.columns and len(df['price']) > 0:
        low_quantile = df['price'].quantile(0.05)
        high_quantile = df['price'].quantile(0.95)
        df = df[df['price'].between(low_quantile, high_quantile)]
        
        # Create price tiers based on the filtered (more realistic) data
        if not df.empty:
            min_price = df['price'].min()
            low_bound = df['price'].quantile(0.33)
            high_bound = df['price'].quantile(0.66)
            max_price = df['price'].max()
            
            price_ranges = {
                'Budget': f"${min_price:,.0f} - ${low_bound:,.0f}",
                'Mid-Range': f"${low_bound:,.0f} - ${high_bound:,.0f}",
                'Premium': f"${high_bound:,.0f} - ${max_price:,.0f}"
            }

            def assign_tier(price):
                if price <= low_bound:
                    return 'Budget'
                elif price <= high_bound:
                    return 'Mid-Range'
                else:
                    return 'Premium'
            
            df['price_tier'] = df['price'].apply(assign_tier)
            df.dropna(subset=['price_tier'], inplace=True)
    
    return df, price_ranges

# --- Main App Layout ---
st.set_page_config(layout="wide", page_title="Nashville Airbnb Analysis")
st.title("Xiaorui's Assignment - Nashville Airbnb Analysis")

# --- Load Data ---
df, price_ranges = load_and_clean_data('new_nashville.csv')

if df.empty:
    st.error("The dataframe is empty after cleaning. This could be due to the source file or filtering criteria.")
    st.stop()


# --- Visualization 1: Host Cohort and Price Analysis ---
st.markdown("---")
st.header("Host Growth and Price Trends by Cohort")
st.markdown("Select a range of years on the top chart to see the price distribution for that group of hosts below.")

brush_selection = alt.selection_interval(encodings=['x'], empty='all')

host_year_chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('host_start_year:O', title="Host Start Year"),
    y=alt.Y('count()', title="Number of New Hosts"),
    color=alt.condition(brush_selection, alt.value('steelblue'), alt.value('lightgray')),
    tooltip=['host_start_year:O', alt.Tooltip('count()', title='New Hosts')]
).add_params(
    brush_selection
).properties(
    title="Number of New Hosts by Start Year"
)

price_dist_chart = alt.Chart(df).mark_bar(color='seagreen').encode(
    x=alt.X('price:Q', bin=alt.Bin(maxbins=40), title="Price per Night (USD)"),
    y=alt.Y('count()', title="Number of Listings"),
    tooltip=[alt.Tooltip('price:Q', bin=True), alt.Tooltip('count()', title='Number of Listings')]
).transform_filter(
    brush_selection
).properties(
    title="Price Distribution for Selected Host Cohort"
)

st.altair_chart(host_year_chart & price_dist_chart, use_container_width=True)


# --- Visualization 2: Seasonal Onboarding Trends ---
st.markdown("---")
st.header("Seasonal Trend of New Hosts by Price Tier")
st.markdown("Use the filter to see if seasonal joining trends differ for listings in various price tiers.")

col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("#### Filter by Price Tier")
    if 'price_tier' in df.columns:
        price_tier_options = ['All'] + sorted(df['price_tier'].unique().tolist())
        selected_price_tier = st.selectbox("Select a Price Tier", options=price_tier_options, key='seasonal_filter', label_visibility="collapsed")
        
        if price_ranges:
            st.markdown("---")
            st.markdown("##### Price Tier Ranges")
            st.markdown(f"**Budget:** {price_ranges.get('Budget', 'N/A')}")
            st.markdown(f"**Mid-Range:** {price_ranges.get('Mid-Range', 'N/A')}")
            st.markdown(f"**Premium:** {price_ranges.get('Premium', 'N/A')}")

    else:
        selected_price_tier = 'All'
        st.warning("Price Tier column could not be created.")

if selected_price_tier == 'All' or 'price_tier' not in df.columns:
    seasonal_df = df
else:
    seasonal_df = df[df['price_tier'] == selected_price_tier]

with col2:
    if not seasonal_df.empty:
        seasonal_chart = alt.Chart(seasonal_df).mark_bar().encode(
            x=alt.X('count()', title="Total Number of New Hosts"),
            y=alt.Y('host_start_month:O', title="Month", axis=alt.Axis(
                labelExpr="['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][datum.value - 1]"
            )),
            tooltip=[
                alt.Tooltip('host_start_month:O', title='Month'), 
                alt.Tooltip('count()', title='Total New Hosts')
            ]
        ).properties(
            title=f"Total New Hosts by Start Month for '{selected_price_tier}' Listings"
        )
        st.altair_chart(seasonal_chart, use_container_width=True)

