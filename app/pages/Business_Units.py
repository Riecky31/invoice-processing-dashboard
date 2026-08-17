import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import plotly.express as px

from app.ui import configure_page, sidebar_header, format_currency
from app.services.reporting import (
    load_invoices,
    get_business_unit_summary,
)


# ============================================================
# PAGE CONFIG
# ============================================================

configure_page("Business Units")
sidebar_header()

st.title("🏢 Business Unit Performance")

st.caption(
    "Invoice processing performance by business unit"
)


# ============================================================
# LOAD DATA
# ============================================================

df = load_invoices()

if df is None or df.empty:
    st.warning("No invoice data is available.")
    st.stop()


# ============================================================
# FILTERS
# ============================================================

st.sidebar.divider()
st.sidebar.subheader("Filters")


# Year

years = sorted(
    df["reporting_year"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

selected_year = st.sidebar.selectbox(
    "Reporting Year",
    years,
    index=len(years) - 1,
)


filtered_df = df[
    df["reporting_year"].astype(int) == selected_year
].copy()


# Month

months = sorted(
    filtered_df["reporting_month"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_month = st.sidebar.selectbox(
    "Reporting Month",
    ["All"] + months,
)


if selected_month != "All":

    filtered_df = filtered_df[
        filtered_df["reporting_month"].astype(str)
        == selected_month
    ]


# ============================================================
# BUSINESS UNIT SUMMARY
# ============================================================

summary = get_business_unit_summary(
    filtered_df
)


if summary is None or summary.empty:

    st.info(
        "No business-unit data is available for the selected filters."
    )

    st.stop()


# ============================================================
# NORMALISE COLUMN NAMES
# ============================================================

# We expect the reporting layer to return:
#
# business_unit
# invoice_count
# total_amount
#
# This keeps the page independent from alternative
# column names such as "invoices".

if "invoice_count" not in summary.columns:

    possible_columns = [
        "invoices",
        "count",
        "total_invoices",
    ]

    for column in possible_columns:

        if column in summary.columns:

            summary = summary.rename(
                columns={
                    column: "invoice_count"
                }
            )

            break


if "total_amount" not in summary.columns:

    possible_columns = [
        "amount",
        "invoice_value",
        "value",
    ]

    for column in possible_columns:

        if column in summary.columns:

            summary = summary.rename(
                columns={
                    column: "total_amount"
                }
            )

            break


# ============================================================
# VALIDATION
# ============================================================

required_columns = [
    "business_unit",
    "invoice_count",
    "total_amount",
]

missing_columns = [
    column
    for column in required_columns
    if column not in summary.columns
]


if missing_columns:

    st.error(
        "Business-unit reporting returned unexpected columns."
    )

    st.write(
        "Available columns:",
        summary.columns.tolist(),
    )

    st.write(
        "Missing columns:",
        missing_columns,
    )

    st.stop()


# ============================================================
# KPI CARDS
# ============================================================

total_invoices = summary["invoice_count"].sum()

total_value = summary["total_amount"].sum()

business_unit_count = len(summary)

average_value = (
    total_value / total_invoices
    if total_invoices
    else 0
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Business Units",
        f"{business_unit_count:,}",
    )


with col2:

    st.metric(
        "Invoices",
        f"{total_invoices:,}",
    )


with col3:

    st.metric(
        "Invoice Value",
        format_currency(total_value),
    )


with col4:

    st.metric(
        "Average Invoice",
        format_currency(average_value),
    )


# ============================================================
# SUMMARY TABLE
# ============================================================

st.divider()

st.subheader("Business Unit Summary")


display_summary = summary.copy()

display_summary["total_amount"] = (
    display_summary["total_amount"]
    .apply(
        lambda value: format_currency(value)
    )
)


st.dataframe(
    display_summary,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# INVOICE COUNT CHART
# ============================================================

st.divider()

st.subheader("📊 Invoice Volume by Business Unit")


fig_invoices = px.bar(
    summary,
    x="business_unit",
    y="invoice_count",
    text="invoice_count",
    labels={
        "business_unit": "Business Unit",
        "invoice_count": "Invoices",
    },
)


fig_invoices.update_traces(
    textposition="outside"
)


fig_invoices.update_layout(
    xaxis_title="Business Unit",
    yaxis_title="Invoices",
)


st.plotly_chart(
    fig_invoices,
    use_container_width=True,
)


# ============================================================
# INVOICE VALUE CHART
# ============================================================

st.subheader("💰 Invoice Value by Business Unit")


fig_value = px.bar(
    summary,
    x="business_unit",
    y="total_amount",
    text="total_amount",
    labels={
        "business_unit": "Business Unit",
        "total_amount": "Invoice Value",
    },
)


fig_value.update_traces(
    texttemplate="R%{y:,.0f}",
    textposition="outside",
)


fig_value.update_layout(
    xaxis_title="Business Unit",
    yaxis_title="Invoice Value",
)


st.plotly_chart(
    fig_value,
    use_container_width=True,
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Showing {total_invoices:,} invoices "
    f"across {business_unit_count:,} business units."
)