#Sajal Gangrade
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Set page config for wide layout
st.set_page_config(page_title="SuperStore KPI Dashboard", layout="wide")

# ---- Load Data ----
@st.cache_data
def load_data():
    df = pd.read_excel("Sample - Superstore.xlsx", engine="openpyxl")
    if not pd.api.types.is_datetime64_any_dtype(df["Order Date"]):
        df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df

df_original = load_data()

# ---- Sidebar Filters ----
st.sidebar.title("Filters")

# Region Filter
all_regions = sorted(df_original["Region"].dropna().unique())
selected_region = st.sidebar.selectbox("Select Region", options=["All"] + all_regions)

# Filter data by Region
if selected_region != "All":
    df_filtered_region = df_original[df_original["Region"] == selected_region]
else:
    df_filtered_region = df_original

# State Filter
all_states = sorted(df_filtered_region["State"].dropna().unique())
selected_state = st.sidebar.selectbox("Select State", options=["All"] + all_states)

if selected_state != "All":
    df_filtered_state = df_filtered_region[df_filtered_region["State"] == selected_state]
else:
    df_filtered_state = df_filtered_region

# Category Filter
all_categories = sorted(df_filtered_state["Category"].dropna().unique())
selected_category = st.sidebar.selectbox("Select Category", options=["All"] + all_categories)

if selected_category != "All":
    df_filtered_category = df_filtered_state[df_filtered_state["Category"] == selected_category]
else:
    df_filtered_category = df_filtered_state

# Sub-Category Filter
all_subcats = sorted(df_filtered_category["Sub-Category"].dropna().unique())
selected_subcat = st.sidebar.selectbox("Select Sub-Category", options=["All"] + all_subcats)

df = df_filtered_category.copy()
if selected_subcat != "All":
    df = df[df["Sub-Category"] == selected_subcat]

# ---- Sidebar Date Range ----
if df.empty:
    min_date = df_original["Order Date"].min()
    max_date = df_original["Order Date"].max()
else:
    min_date = df["Order Date"].min()
    max_date = df["Order Date"].max()

from_date = st.sidebar.date_input("From Date", value=min_date, min_value=min_date, max_value=max_date)
to_date = st.sidebar.date_input("To Date", value=max_date, min_value=min_date, max_value=max_date)

if from_date > to_date:
    st.sidebar.error("From Date must be earlier than To Date.")

df = df[(df["Order Date"] >= pd.to_datetime(from_date)) & (df["Order Date"] <= pd.to_datetime(to_date))]

# ---- Sidebar Summary Insights ----
st.sidebar.markdown("### Key Insights")

if df.empty:
    st.sidebar.info("No data available.")
else:
    top_state = df.groupby("State")["Profit"].sum().idxmax()
    top_category = df.groupby("Category")["Profit"].sum().idxmax()
    avg_discount = df["Discount"].mean()

    st.sidebar.write(f"**Top Profitable State:** {top_state}")
    st.sidebar.write(f"**Top Profitable Category:** {top_category}")
    st.sidebar.write(f"**Average Discount:** {avg_discount:.2%}")

# ---- Page Title ----
st.title("SuperStore KPI Dashboard")

# ---- Custom CSS for KPI Tiles ----
st.markdown("""
    <style>
    .kpi-box {
        background-color: #FFFFFF;
        border: 2px solid #EAEAEA;
        border-radius: 8px;
        padding: 16px;
        margin: 8px;
        text-align: center;
    }
    .kpi-title {
        font-weight: 600;
        color: #333333;
        font-size: 16px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-weight: 700;
        font-size: 24px;
        color: #1E90FF;
    }
    </style>
""", unsafe_allow_html=True)

# ---- KPI Calculation ----
if df.empty:
    total_sales = 0
    total_quantity = 0
    total_profit = 0
    margin_rate = 0
else:
    total_sales = df["Sales"].sum()
    total_quantity = df["Quantity"].sum()
    total_profit = df["Profit"].sum()
    margin_rate = (total_profit / total_sales) if total_sales != 0 else 0

# ---- KPI Display ----
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Sales</div>
            <div class='kpi-value'>${total_sales:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi_col2:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Quantity Sold</div>
            <div class='kpi-value'>{total_quantity:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi_col3:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Profit</div>
            <div class='kpi-value'>${total_profit:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi_col4:
    st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Margin Rate</div>
            <div class='kpi-value'>{(margin_rate * 100):,.2f}%</div>
        </div>
    """, unsafe_allow_html=True)

# ---- Time Granularity ----
granularity = st.radio("Select Time Granularity:", ["Daily", "Monthly", "Yearly"], horizontal=True)

if granularity == "Monthly":
    df["YearMonth"] = df["Order Date"].dt.to_period('M').astype(str)
    grouped_time = df.groupby("YearMonth").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index().rename(columns={"YearMonth": "Order Date"})
elif granularity == "Yearly":
    df["Year"] = df["Order Date"].dt.year
    grouped_time = df.groupby("Year").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index().rename(columns={"Year": "Order Date"})
else:
    grouped_time = df.groupby("Order Date").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index()

# Calculate Margin Rate
grouped_time["Margin Rate"] = grouped_time["Profit"] / grouped_time["Sales"].replace(0, 1)

# ---- KPI Selection ----
st.subheader("Visualize KPI Across Time & Top Products")

if df.empty:
    st.warning("No data available for the selected filters and date range.")
else:
    kpi_options = ["Sales", "Quantity", "Profit", "Margin Rate"]
    selected_kpi = st.radio("Select KPI to display:", options=kpi_options, horizontal=True)

    # Product grouping for top 10 chart
    product_grouped = df.groupby("Product Name").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index()
    product_grouped["Margin Rate"] = product_grouped["Profit"] / product_grouped["Sales"].replace(0, 1)

    product_grouped.sort_values(by=selected_kpi, ascending=False, inplace=True)
    top_10 = product_grouped.head(10)

    # ---- Side-by-Side Charts ----
    col_left, col_right = st.columns(2)

    with col_left:
        fig_line = px.line(
            grouped_time,
            x="Order Date",
            y=selected_kpi,
            title=f"{selected_kpi} Over Time ({granularity})",
            labels={"Order Date": "Date", selected_kpi: selected_kpi},
            template="plotly_white",
        )
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        fig_bar = px.bar(
            top_10,
            x=selected_kpi,
            y="Product Name",
            orientation="h",
            title=f"Top 10 Products by {selected_kpi}",
            labels={selected_kpi: selected_kpi, "Product Name": "Product"},
            color=top_10["Profit"].apply(lambda x: 'Loss' if x < 0 else 'Profit'),
            color_discrete_map={'Profit': 'blue', 'Loss': 'red'},
            template="plotly_white",
        )
        fig_bar.update_layout(
            height=400,
            yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ---- Download Filtered Data ----
st.subheader("Download Filtered Data")
if df.empty:
    st.info("No data to download.")
else:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='Filtered_Superstore_Data.csv',
        mime='text/csv',
    )
