import sys
from pathlib import Path

# Make project root importable when running:
# streamlit run app/dashboard.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.ui import configure_page, sidebar_header, format_currency
from app.services.reporting import (
    load_invoices,
    calculate_kpis,
    calculate_tat_metrics,
    get_daily_summary,
    get_weekly_summary,
    get_monthly_summary,
    get_business_unit_summary,
)


# ============================================================
# PAGE CONFIG
# ============================================================

configure_page("Invoice Processing Dashboard")
sidebar_header()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=60)
def load_dashboard_data():
    df = load_invoices()

    if df is None:
        return pd.DataFrame()

    return df


df = load_dashboard_data()


# ============================================================
# EMPTY STATE
# ============================================================

if df.empty:
    st.title("📊 Invoice Processing Dashboard")

    st.warning(
        "No invoice data is currently available."
    )

    st.info(
        "Import a weekly invoice report first, then refresh the dashboard."
    )

    st.stop()


# ============================================================
# TITLE
# ============================================================

st.title("📊 Invoice Processing Dashboard")

st.caption(
    "Invoice Processing Reporting System"
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.divider()

st.sidebar.subheader("Filters")


# ------------------------------------------------------------
# Reporting Year
# ------------------------------------------------------------

years = sorted(
    df["reporting_year"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

selected_year = st.sidebar.selectbox(
    "Reporting Year",
    options=years,
    index=len(years) - 1,
)


# ------------------------------------------------------------
# Reporting Month
# ------------------------------------------------------------

year_df = df[
    df["reporting_year"].astype(int) == selected_year
].copy()

months = sorted(
    year_df["reporting_month"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_month = st.sidebar.selectbox(
    "Reporting Month",
    options=["All"] + months,
)


# ------------------------------------------------------------
# Business Unit
# ------------------------------------------------------------

business_units = sorted(
    df["business_unit"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_business_unit = st.sidebar.selectbox(
    "Business Unit",
    options=["All"] + business_units,
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    df["reporting_year"].astype(int) == selected_year
].copy()


if selected_month != "All":
    filtered_df = filtered_df[
        filtered_df["reporting_month"].astype(str)
        == selected_month
    ]


if selected_business_unit != "All":
    filtered_df = filtered_df[
        filtered_df["business_unit"].astype(str)
        == selected_business_unit
    ]


# ============================================================
# FILTER SUMMARY
# ============================================================

st.markdown(
    f"""
**Showing:** {len(filtered_df):,} invoices  
**Year:** {selected_year}  
**Month:** {selected_month}  
**Business Unit:** {selected_business_unit}
"""
)


# ============================================================
# KPI CALCULATIONS
# ============================================================

kpis = calculate_kpis(filtered_df)
tat_metrics = calculate_tat_metrics(filtered_df)


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Invoices",
        f"{kpis.get('total_invoices', 0):,}",
    )

with col2:
    st.metric(
        "Invoice Value",
        format_currency(
            kpis.get("total_amount", 0)
        ),
    )

with col3:
    st.metric(
        "VAT",
        format_currency(
            kpis.get("total_tax", 0)
        ),
    )

with col4:
    st.metric(
        "Average Invoice",
        format_currency(
            kpis.get("average_invoice_amount", 0)
        ),
    )


col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        "Vendors",
        f"{kpis.get('unique_vendors', 0):,}",
    )

with col6:
    st.metric(
        "Business Units",
        f"{kpis.get('unique_business_units', 0):,}",
    )

with col7:
    st.metric(
        "Average TAT",
        f"{tat_metrics.get('average_tat_hours', 0):.1f} hrs",
    )

with col8:
    st.metric(
        "Median TAT",
        f"{tat_metrics.get('median_tat_hours', 0):.1f} hrs",
    )


# ============================================================
# TAT INFORMATION
# ============================================================

st.divider()

st.subheader("⏱️ Turnaround Time")

tat1, tat2, tat3, tat4 = st.columns(4)

with tat1:
    st.metric(
        "Invoices with TAT",
        f"{tat_metrics.get('tat_count', 0):,}",
    )

with tat2:
    st.metric(
        "Minimum TAT",
        f"{tat_metrics.get('minimum_tat_minutes', 0) / 60:.1f} hrs",
    )

with tat3:
    st.metric(
        "Median TAT",
        f"{tat_metrics.get('median_tat_hours', 0):.1f} hrs",
    )

with tat4:
    st.metric(
        "Maximum TAT",
        f"{tat_metrics.get('maximum_tat_minutes', 0) / 60:.1f} hrs",
    )


# ============================================================
# MONTHLY TREND
# ============================================================

st.divider()

st.subheader("📈 Monthly Invoice Trend")

monthly = get_monthly_summary(filtered_df)


if not monthly.empty:

    fig_monthly = px.bar(
        monthly,
        x="reporting_month",
        y="invoice_count",
        text="invoice_count",
        labels={
            "reporting_month": "Month",
            "invoice_count": "Invoices",
        },
        title="Invoices Processed by Month",
    )

    fig_monthly.update_traces(
        textposition="outside"
    )

    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Invoices",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_monthly,
        use_container_width=True,
    )

else:
    st.info("No monthly data available.")


# ============================================================
# MONTHLY VALUE TREND
# ============================================================

if not monthly.empty:

    fig_value = px.line(
        monthly,
        x="reporting_month",
        y="total_amount",
        markers=True,
        labels={
            "reporting_month": "Month",
            "total_amount": "Invoice Value",
        },
        title="Invoice Value by Month",
    )

    fig_value.update_layout(
        xaxis_title="Month",
        yaxis_title="Invoice Value",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_value,
        use_container_width=True,
    )


# ============================================================
# DAILY PROCESSING TREND
# ============================================================

st.divider()

st.subheader("📅 Daily Processing Trend")

daily = get_daily_summary(filtered_df)


if not daily.empty:

    # The reporting layer currently returns `date`,
    # so we use that column directly.
    daily = daily.copy()

    daily["date"] = pd.to_datetime(
        daily["date"]
    )

    fig_daily = px.line(
        daily,
        x="date",
        y="invoice_count",
        markers=True,
        labels={
            "date": "Processing Date",
            "invoice_count": "Invoices",
        },
        title="Invoices Processed Per Day",
    )

    fig_daily.update_layout(
        xaxis_title="Processing Date",
        yaxis_title="Invoices",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_daily,
        use_container_width=True,
    )

else:
    st.info("No daily data available.")


# ============================================================
# BUSINESS UNIT
# ============================================================

st.divider()

st.subheader("🏢 Business Unit Performance")

business_summary = get_business_unit_summary(
    filtered_df
)


if not business_summary.empty:

    st.dataframe(
        business_summary,
        use_container_width=True,
        hide_index=True,
    )

    # Detect the appropriate invoice-count column
    count_column = None

    for column in [
        "invoice_count",
        "count",
        "total_invoices",
    ]:
        if column in business_summary.columns:
            count_column = column
            break

    if count_column:

        fig_business = px.bar(
            business_summary,
            x="business_unit",
            y=count_column,
            text=count_column,
            labels={
                "business_unit": "Business Unit",
                count_column: "Invoices",
            },
            title="Invoices by Business Unit",
        )

        fig_business.update_traces(
            textposition="outside"
        )

        st.plotly_chart(
            fig_business,
            use_container_width=True,
        )

else:
    st.info("No business-unit data available.")


# ============================================================
# WEEKLY PERFORMANCE
# ============================================================

st.divider()

st.subheader("📊 Weekly Processing")

weekly = get_weekly_summary(filtered_df)


if not weekly.empty:

    st.dataframe(
        weekly,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("No weekly data available.")


# ============================================================
# INVOICE DATA
# ============================================================

st.divider()

st.subheader("🧾 Invoice Records")

display_columns = [
    "invoice_processing_date",
    "invoice_date",
    "invoice_number",
    "invoice_type",
    "vendor_name",
    "vendor_id",
    "business_unit",
    "invoice_amount",
    "invoice_tax_amount",
    "currency",
    "reporting_month",
    "reporting_week",
    "tat_hours",
]


available_columns = [
    column
    for column in display_columns
    if column in filtered_df.columns
]


display_df = filtered_df[
    available_columns
].copy()


# Format dates

for column in [
    "invoice_processing_date",
    "invoice_date",
]:

    if column in display_df.columns:

        display_df[column] = pd.to_datetime(
            display_df[column],
            errors="coerce",
        ).dt.strftime(
            "%Y-%m-%d %H:%M"
        )


# Format monetary values

for column in [
    "invoice_amount",
    "invoice_tax_amount",
]:

    if column in display_df.columns:

        display_df[column] = display_df[
            column
        ].apply(
            lambda x: f"R{float(x):,.2f}"
            if pd.notna(x)
            else "R0.00"
        )


if "tat_hours" in display_df.columns:

    display_df["tat_hours"] = display_df[
        "tat_hours"
    ].apply(
        lambda x: round(float(x), 1)
        if pd.notna(x)
        else None
    )


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Invoice Processing Dashboard • "
    f"{len(filtered_df):,} records displayed"
)