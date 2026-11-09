
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Smart Supply Chain Control Tower",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Smart Supply Chain Control Tower")
st.caption("Real-Time Shipment Visibility & Inventory Risk Monitoring")

API_BASE_URL = "http://127.0.0.1:8000"

# --------------------------------------------------
# API DATA LOADING
# --------------------------------------------------

@st.cache_data(ttl=5)
def load_data():
    response = requests.get(
        f"{API_BASE_URL}/api/shipments",
        params={"limit": 1000},
        timeout=10
    )
    response.raise_for_status()
    return pd.DataFrame(response.json()["shipments"])


@st.cache_data(ttl=5)
def load_kpis():
    response = requests.get(
        f"{API_BASE_URL}/api/shipments/kpis",
        timeout=10
    )
    response.raise_for_status()
    return response.json()


try:
    df = load_data()
    kpis = load_kpis()

except requests.RequestException as error:
    st.error(f"Unable to connect to Module 2 API: {error}")
    st.info("Make sure FastAPI is running on port 8000.")
    st.stop()


if df.empty:
    st.warning("No shipment events available.")
    st.stop()

# --------------------------------------------------
# LATEST STATUS PER SHIPMENT
# --------------------------------------------------

# Exclude legacy duplicate candidates from analytics.
analytics_df = df[
    df["duplicate_of_id"].isna()
].copy()

# Latest event based on event timestamp.
latest_df = (
    analytics_df
    .sort_values(
        ["event_timestamp", "id"],
        ascending=[False, False]
    )
    .drop_duplicates(
        subset="shipment_id",
        keep="first"
    )
)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

shipment_filter = st.sidebar.multiselect(
    "Shipment ID",
    sorted(df["shipment_id"].dropna().unique())
)

delay_filter = st.sidebar.multiselect(
    "Delay Status",
    sorted(df["delay_status"].dropna().unique())
)

risk_filter = st.sidebar.multiselect(
    "Stockout Risk",
    sorted(df["stockout_risk"].dropna().unique())
)

filtered_df = analytics_df.copy()

if shipment_filter:
    filtered_df = filtered_df[
        filtered_df["shipment_id"].isin(shipment_filter)
    ]

if delay_filter:
    filtered_df = filtered_df[
        filtered_df["delay_status"].isin(delay_filter)
    ]

if risk_filter:
    filtered_df = filtered_df[
        filtered_df["stockout_risk"].isin(risk_filter)
    ]
filtered_latest = (
    filtered_df
    .sort_values(
        ["event_timestamp", "id"],
        ascending=[False, False]
    )
    .drop_duplicates(
        subset="shipment_id",
        keep="first"
    )
)

# --------------------------------------------------
# SUPPLY CHAIN OVERVIEW
# --------------------------------------------------

st.subheader("Supply Chain Overview")

total_events = len(filtered_df)
total_shipments = filtered_latest["shipment_id"].nunique()

delayed_events = (
    filtered_df["delay_status"] != "ON_TIME"
).sum()

delayed_shipments = (
    filtered_latest["delay_status"] != "ON_TIME"
).sum()

high_risk_shipments = (
    filtered_latest["stockout_risk"] == "HIGH"
).sum()

average_eta = filtered_latest["eta_variance_hours"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Unique Shipments", int(total_shipments))
col2.metric("Delayed Shipments", int(delayed_shipments))
col3.metric("High-Risk Shipments", int(high_risk_shipments))

col4.metric(
    "Average Latest ETA Variance",
    f"{average_eta:.2f} hrs"
    if pd.notna(average_eta)
    else "N/A"
)

st.caption(
    f"Analytical events: {total_events} | "
    f"Delayed events: {int(delayed_events)} | "
    f"Retained legacy duplicate records: "
    f"{int(df['duplicate_of_id'].notna().sum())}"
)

st.divider()

# --------------------------------------------------
# EVENT AND SHIPMENT SUMMARY
# --------------------------------------------------

st.subheader("Shipment Status Summary")

summary_df = filtered_latest[
    [
        "shipment_id",
        "order_id",
        "sku",
        "warehouse_id",
        "event_type",
        "eta_variance_hours",
        "delay_status",
        "days_of_supply",
        "stockout_risk"
    ]
]

st.dataframe(summary_df, width="stretch", hide_index=True)

st.divider()

# --------------------------------------------------
# DELAY ANALYSIS
# --------------------------------------------------

st.subheader("Shipment Delay Analysis")

col1, col2 = st.columns(2)

with col1:
    delay_counts = (
        filtered_df["delay_status"]
        .fillna("UNKNOWN")
        .value_counts()
        .rename_axis("Delay Status")
        .reset_index(name="Count")
    )

    fig_delay = px.pie(
        delay_counts,
        names="Delay Status",
        values="Count",
        title="Event-Level Delay Distribution",
        hole=0.45
    )

    st.plotly_chart(fig_delay, width="stretch")

with col2:
    risk_counts = (
        filtered_latest["stockout_risk"]
        .fillna("UNKNOWN")
        .value_counts()
        .rename_axis("Stockout Risk")
        .reset_index(name="Count")
    )

    fig_risk = px.bar(
        risk_counts,
        x="Stockout Risk",
        y="Count",
        title="Latest Stockout Risk by Shipment",
        text="Count"
    )

    st.plotly_chart(fig_risk, width="stretch")

st.divider()

# --------------------------------------------------
# INVENTORY MONITORING
# --------------------------------------------------

st.subheader("Inventory Monitoring")

inventory_df = filtered_latest[
    [
        "sku",
        "warehouse_id",
        "available_inventory",
        "average_daily_demand",
        "days_of_supply",
        "stockout_risk"
    ]
]

st.dataframe(
    inventory_df,
    width="stretch",
    hide_index=True
)

st.caption(
    "Inventory and demand values currently use demonstration inputs."
)

st.divider()

# --------------------------------------------------
# SHIPMENT EVENT HISTORY
# --------------------------------------------------

st.subheader("Shipment Event History (Including Legacy Records)")

display_columns = [
    "id",
    "event_id",
    "duplicate_of_id",
    "shipment_id",
    "order_id",
    "sku",
    "warehouse_id",
    "event_type",
    "event_timestamp",
    "eta_variance_hours",
    "delay_status",
    "days_of_supply",
    "stockout_risk"
]

st.dataframe(
    filtered_df[display_columns],
    width="stretch",
    hide_index=True
)

st.caption("Data source: Module 2 FastAPI → SQLite")
st.caption("Refresh interval: 5 seconds")
