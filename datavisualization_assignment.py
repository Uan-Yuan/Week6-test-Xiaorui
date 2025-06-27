import streamlit as st
import pandas as pd
import altair as alt
import io # Used for debugging, can be removed later
import datetime # For current year in filtering

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_airbnb_data():
    # IMPORTANT: Adjust this path if your 'new_nashville.csv' is in a different location.
    # For example, if it's in the same directory as this script, use 'new_nashville.csv'
    # If it's in a 'data' folder, use 'data/new_nashville.csv'
    # Adding engine='python' for robustness against potential CSV parsing issues.
    df = pd.read_csv('new_nashville.csv', engine='python')

    # 1. Convert 'host_since' to datetime and extract 'host_start_year'
    # Specify format for reliable parsing, errors='coerce' turns unparseable into NaT
    df['host_since'] = pd.to_datetime(df['host_since'], format='%m/%d/%Y', errors='coerce')
    df['host_start_year'] = df['host_since'].dt.year

    # 2. Ensure numeric columns are correct type and handle NaNs
    # Define essential numeric columns that charts will rely on
    numeric_cols = [
        'price',
        'reviews_per_month',
        'review_scores_rating',
        'calculated_host_listings_count'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where essential columns for visualization or keys are missing
    # Including host_id as it's used for counting hosts
    df.dropna(subset=numeric_cols + ['host_since', 'host_start_year', 'host_id', 'neighbourhood_cleansed', 'host_is_superhost', 'room_type'], inplace=True)

    # 3. Handle infinite values in 'reviews_per_month' if any (e.g., from division by zero)
    df = df[df['reviews_per_month'] != float('inf')]
    df = df[df['reviews_per_month'] >= 0] # Ensure reviews per month is non-negative

    # 4. Filter out unrealistic 'host_start_year' values
    # Airbnb was founded in 2008, so filter out years before that.
    # Also, filter out future years or extremely old/invalid years if present.
    current_year = datetime.datetime.now().year
    df = df[(df['host_start_year'] >= 2008) & (df['host_start_year'] <= current_year)]

    # Convert host_is_superhost to boolean for cleaner use
    df['host_is_superhost'] = df['host_is_superhost'].astype(str).str.lower().map({'t': True, 'f': False, 'true': True, 'false': False})
    df.dropna(subset=['host_is_superhost'], inplace=True) # Drop if still NaN

    # Ensure price is positive
    df = df[df['price'] > 0]

    return df

# Load the data
df = load_airbnb_data()

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Nashville Airbnb Host Evolution")

st.title("Nashville Airbnb Host Evolution & Listing Performance")
st.markdown("---") # Add a separator

# Optional: Display a quick check of the loaded data for debugging
# if st.checkbox("Show Raw Data Info"):
#     st.subheader("Data Info After Preprocessing")
#     buffer = io.StringIO()
#     df.info(buf=buffer)
#     st.code(buffer.getvalue())
#     st.subheader("First 5 Rows After Preprocessing")
#     st.dataframe(df.head())
#     st.subheader("Final DataFrame Shape")
#     st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
#     if df.empty:
#         st.error("The DataFrame is empty after preprocessing. Charts will not display.")

st.markdown("This dashboard explores trends in Airbnb hosts and listings in Nashville over time.")


# --- Sidebar for Main Chart Control ---
st.sidebar.header("Main Chart Controls")

# Define the columns that can be selected for the Y-axis
y_axis_options = {
    "Number of New Hosts": "num_hosts", # Handled by aggregation count(host_id)
    "Average Reviews per Month": "reviews_per_month",
    "Average Listing Price": "price",
    "Average Overall Rating": "review_scores_rating",
    "Average Host Listings Count": "calculated_host_listings_count"
}

selected_y_axis_label = st.sidebar.selectbox(
    "Select Metric for Main Chart Y-Axis:",
    list(y_axis_options.keys()),
    index=0 # Default selection
)
selected_y_axis_column = y_axis_options[selected_y_axis_label]


# --- Main Chart: Host & Market Growth Over Time ---
st.header("1. Host & Market Growth Over Time")
st.write("Select a range of years on the chart below to filter the corresponding charts.")

# Create a selection for the time range (host_start_year)
time_selection = alt.selection_interval(encodings=['x'], empty='all', resolve='global')

# Base chart for aggregation, adding the time_selection param
base_main_chart = alt.Chart(df).properties(
    title=f"{selected_y_axis_label} by Host Start Year"
).add_params(time_selection)

# Conditional aggregation and Y-axis encoding based on user selection
if selected_y_axis_column == "num_hosts":
    main_chart_spec = base_main_chart.mark_line(point=True, color='steelblue').encode(
        x=alt.X('host_start_year:O', title='Host Start Year'), # 'O' for ordinal/discrete
        y=alt.Y('count(host_id):Q', title='Number of New Hosts'), # Count unique hosts per year
        tooltip=['host_start_year', alt.Tooltip('count(host_id)', title='Number of New Hosts')]
    )
else:
    main_chart_spec = base_main_chart.mark_line(point=True, color='steelblue').encode(
        x=alt.X('host_start_year:O', title='Host Start Year'),
        y=alt.Y(f'mean({selected_y_axis_column}):Q', title=selected_y_axis_label),
        tooltip=['host_start_year', alt.Tooltip(f'mean({selected_y_axis_column}):Q', title=selected_y_axis_label, format='.2f')]
    )

# Display the Main Chart in Streamlit
st.altair_chart(main_chart_spec, use_container_width=True)


# --- Corresponding Charts Section ---
st.header("2. Corresponding Insights for Selected Host Cohort")
st.markdown("These charts update based on the year range selected in the chart above.")

# Create columns for corresponding charts
col1, col2 = st.columns(2) # First row of columns

with col1:
    st.subheader("Price Distribution for Selected Cohort")
    # Corresponding Chart 1: Price Distribution
    price_dist_chart = alt.Chart(df).mark_bar().encode(
        alt.X("price:Q", bin=alt.Bin(maxbins=50), title="Price per Night (USD)"), # Adjust maxbins for desired granularity
        alt.Y("count()", title="Number of Listings"),
        tooltip=[alt.Tooltip("price:Q", bin=True, title="Price Range"), "count()"]
    ).transform_filter(
        time_selection # Link to the main chart's time selection
    ).properties(
        height=300
    )
    st.altair_chart(price_dist_chart, use_container_width=True)

with col2:
    st.subheader("Top Neighborhoods for Selected Cohort")
    # Corresponding Chart 2: Top Neighborhoods
    neighborhood_chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("neighbourhood_cleansed:N", sort="-x", title="Neighborhood"), # Sort by count descending
        x=alt.X("count():Q", title="Number of Listings"),
        tooltip=["neighbourhood_cleansed", "count()"]
    ).transform_filter(
        time_selection # Link to the main chart's time selection
    ).properties(
        height=300
    )
    st.altair_chart(neighborhood_chart, use_container_width=True)


# Second row of columns for additional corresponding charts
col3, col4 = st.columns(2)

with col3:
    st.subheader("Superhost Status for Selected Cohort")
    # Corresponding Chart 3: Superhost Status
    superhost_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("count():Q", title="Number of Listings"),
        y=alt.Y("host_is_superhost:N", title="Is Superhost?"),
        color=alt.Color("host_is_superhost:N", legend=None), # Color by Superhost status
        tooltip=["host_is_superhost", "count()"]
    ).transform_filter(
        time_selection # Link to the main chart's time selection
    ).properties(
        height=300
    )
    st.altair_chart(superhost_chart, use_container_width=True)


with col4:
    st.subheader("Room Type Breakdown for Selected Cohort")
    # Corresponding Chart 4: Room Type Breakdown
    room_type_chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("room_type:N", sort="-x", title="Room Type"),
        x=alt.X("count():Q", title="Number of Listings"),
        tooltip=["room_type", "count()"]
    ).transform_filter(
        time_selection # Link to the main chart's time selection
    ).properties(
        height=300
    )
    st.altair_chart(room_type_chart, use_container_width=True)

st.markdown("---")
st.markdown("Explore the data by interacting with the charts!")