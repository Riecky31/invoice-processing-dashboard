import streamlit as st
import plotly.express as px

from app.ui import configure_page, sidebar_header, format_currency

from app.services.reporting.reporting import load_invoices
from app.services.reporting.metrics import (
    calculate_kpis,
    calculate_tat_metrics,
)
from app.services.reporting.trends import (
    get_daily_summary,
    get_weekly_summary,
    get_monthly_summary,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

configure_page("Invoice Processing Dashboard")
sidebar_header()


# =========================================================
# HEADER
# =========================================================

st.title("📊 Invoice Processing Dashboard")

st.caption(
    "Weekly invoice reports consolidated into PostgreSQL"
)


# =========================================================
# LOAD DATA
# =========================================================

try:
    df = load_invoices()
except Exception as exc:
    st.error("Unable to load invoice data.")
    st.exception(exc)
    st.stop()


if df.empty:
    st.warning(
        "No invoice data is currently available."
    )
    st.stop()


# =========================================================
# FILTERS
# =========================================================

with st.sidebar:

    st.header("Filters")

    months = sorted(
        df["reporting_month"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_month = st.selectbox(
        "Reporting Month",
        options=["All"] + months,
    )

    staff = sorted(
        df["user_id"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_staff = st.multiselect(
        "Staff",
        options=staff,
    )

    business_units = sorted(
        df["business_unit"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_business_units = st.multiselect(
        "Business Unit",
        options=business_units,
    )

    invoice_types = sorted(
        df["invoice_type"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_invoice_types = st.multiselect(
        "Invoice Type",
        options=invoice_types,
    )

    if st.button("Clear Filters"):

        st.rerun()


# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df.copy()


if selected_month != "All":

    filtered_df = filtered_df[
        filtered_df["reporting_month"]
        == selected_month
    ]


if selected_staff:

    filtered_df = filtered_df[
        filtered_df["user_id"].isin(
            selected_staff
        )
    ]


if selected_business_units:

    filtered_df = filtered_df[
        filtered_df["business_unit"].isin(
            selected_business_units
        )
    ]


if selected_invoice_types:

    filtered_df = filtered_df[
        filtered_df["invoice_type"].isin(
            selected_invoice_types
        )
    ]


# =========================================================
# FILTER SUMMARY
# =========================================================

st.info(
    f"Showing {len(filtered_df):,} invoices "
    f"from {filtered_df['user_id'].nunique():,} staff."
)


# =========================================================
# KPI METRICS
# =========================================================

kpis = calculate_kpis(filtered_df)

tat_metrics = calculate_tat_metrics(filtered_df)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Invoices Processed",
        f"{kpis['invoice_count']:,}",
    )

with col2:
    st.metric(
        "Invoice Value",
        format_currency(
            kpis["invoice_value"]
        ),
    )

with col3:
    st.metric(
        "Average TAT",
        f"{tat_metrics['average_tat_hours']:.1f} hrs",
    )

with col4:
    st.metric(
        "SLA %",
        f"{tat_metrics['sla_percentage']:.1f}%",
    )


st.divider()


# =========================================================
# PROCESSING TREND
# =========================================================

st.subheader("📈 Invoice Processing Trend")

daily = get_daily_summary(
    filtered_df
)

if daily.empty:

    st.info(
        "No daily processing data available."
    )

else:

    fig = px.line(
        daily,
        x="processing_day",
        y="invoices",
        markers=True,
        labels={
            "processing_day": "Date",
            "invoices": "Invoices",
        },
    )

    fig.update_layout(
        height=380,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# TWO COLUMN SECTION
# =========================================================

left, right = st.columns(2)


# =========================================================
# WEEKLY TREND
# =========================================================

with left:

    st.subheader("📅 Weekly Processing")

    weekly = get_weekly_summary(
        filtered_df
    )

    if weekly.empty:

        st.info(
            "No weekly data available."
        )

    else:

        weekly["week"] = (
            weekly["reporting_year"]
            .astype(str)
            + "-W"
            + weekly["reporting_week"]
            .astype(str)
            .str.zfill(2)
        )

        fig = px.bar(
            weekly,
            x="week",
            y="invoices",
            labels={
                "week": "Week",
                "invoices": "Invoices",
            },
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# =========================================================
# MONTHLY TREND
# =========================================================

with right:

    st.subheader("🗓️ Monthly Processing")

    monthly = get_monthly_summary(
        filtered_df
    )

    if monthly.empty:

        st.info(
            "No monthly data available."
        )

    else:

        fig = px.line(
            monthly,
            x="reporting_month",
            y="invoices",
            markers=True,
            labels={
                "reporting_month": "Month",
                "invoices": "Invoices",
            },
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# =========================================================
# TAT SECTION
# =========================================================

st.divider()

st.subheader("⏱️ Turnaround Time")


tat_col1, tat_col2, tat_col3, tat_col4 = st.columns(4)


with tat_col1:

    st.metric(
        "Average TAT",
        f"{tat_metrics['average_tat_hours']:.1f} hrs",
    )


with tat_col2:

    st.metric(
        "Median TAT",
        f"{tat_metrics['median_tat_hours']:.1f} hrs",
    )


with tat_col3:

    st.metric(
        "Fastest",
        f"{tat_metrics['minimum_tat_hours']:.1f} hrs",
    )


with tat_col4:

    st.metric(
        "Slowest",
        f"{tat_metrics['maximum_tat_hours']:.1f} hrs",
    )


# =========================================================
# TAT DISTRIBUTION
# =========================================================

if "tat_minutes" in filtered_df.columns:

    tat_df = filtered_df.dropna(
        subset=["tat_minutes"]
    ).copy()

    if not tat_df.empty:

        tat_df["tat_hours"] = (
            tat_df["tat_minutes"] / 60
        )

        fig = px.histogram(
            tat_df,
            x="tat_hours",
            nbins=20,
            labels={
                "tat_hours": "TAT (Hours)",
                "count": "Invoices",
            },
        )

        fig.update_layout(
            height=350,
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# =========================================================
# STAFF PERFORMANCE
# =========================================================

st.divider()

st.subheader("👥 Staff Performance")


staff_summary = (
    filtered_df
    .groupby("user_id")
    .agg(
        invoices=("invoice_number", "count"),
        invoice_value=("invoice_amount", "sum"),
        average_tat=("tat_minutes", "mean"),
    )
    .reset_index()
)


if not staff_summary.empty:

    staff_summary["average_tat_hours"] = (
        staff_summary["average_tat"] / 60
    )

    staff_summary = staff_summary.sort_values(
        "invoices",
        ascending=False,
    )

    fig = px.bar(
        staff_summary.head(15),
        x="user_id",
        y="invoices",
        labels={
            "user_id": "Staff",
            "invoices": "Invoices",
        },
    )

    fig.update_layout(
        height=400,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        staff_summary[
            [
                "user_id",
                "invoices",
                "invoice_value",
                "average_tat_hours",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# BUSINESS UNIT PERFORMANCE
# =========================================================

st.divider()

st.subheader("🏢 Business Unit Performance")


business_summary = (
    filtered_df
    .groupby("business_unit")
    .agg(
        invoices=("invoice_number", "count"),
        invoice_value=("invoice_amount", "sum"),
        average_tat=("tat_minutes", "mean"),
    )
    .reset_index()
)


if not business_summary.empty:

    business_summary["average_tat_hours"] = (
        business_summary["average_tat"] / 60
    )

    fig = px.bar(
        business_summary,
        x="business_unit",
        y="invoices",
        labels={
            "business_unit": "Business Unit",
            "invoices": "Invoices",
        },
    )

    fig.update_layout(
        height=400,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# =========================================================
# DATA TABLE
# =========================================================

st.divider()

with st.expander("📋 View Invoice Data"):

    display_columns = [
        "user_id",
        "invoice_number",
        "invoice_type",
        "vendor_name",
        "business_unit",
        "invoice_amount",
        "invoice_date",
        "invoice_processing_date",
        "tat_minutes",
        "currency",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in filtered_df.columns
    ]

    st.dataframe(
        filtered_df[available_columns],
        use_container_width=True,
        hide_index=True,
    )