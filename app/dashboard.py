import streamlit as st

from app.ui import (
    configure_page,
    sidebar_header,
    format_currency,
)

from app.services.reporting import (
    load_invoices,
    get_daily_summary,
    get_weekly_summary,
    get_monthly_summary,
)
from app.services.outlook_watcher import process_existing_emails


configure_page("Invoice Processing Dashboard")

sidebar_header()


# =========================================================
# PAGE HEADER
# =========================================================

st.title("📊 Invoice Processing Dashboard")

st.caption(
    "Weekly invoice reports consolidated into PostgreSQL"
)

# ---------------------------------------------------------
# Manual Outlook import
# ---------------------------------------------------------
with st.expander("📥 Import from Outlook", expanded=False):
    subject_input = st.text_input(
        "Match subject contains (case-insensitive)",
        value="FW: AP BTS Weekly Report",
        help="Search inbox for emails whose subject contains this text",
    )

    if st.button("Check Inbox & Import", key="import_from_outlook"):
        with st.spinner("Checking Outlook inbox and importing attachments..."):
            try:
                results = process_existing_emails(subject_input)
            except Exception as exc:
                st.exception(exc)
                results = []

        if results:
            st.success("Import completed")
            st.write(results)
            # reload data after import
            df = load_invoices()
            if df.empty:
                st.warning("No invoice data is currently available after import.")
                st.stop()
        else:
            st.info("No matching messages or attachments were processed.")


# =========================================================
# LOAD DATA
# =========================================================

df = load_invoices()

if df.empty:
    st.warning(
        "No invoice data is currently available."
    )
    st.stop()


# =========================================================
# FILTERS
# =========================================================

with st.expander(
    "🔎 Filters",
    expanded=False,
):

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:

        months = sorted(
            df["reporting_month"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_month = st.selectbox(
            "Reporting Month",
            options=["All"] + months,
            key="filter_month",
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
            key="filter_staff",
        )


    with filter_col2:

        business_units = sorted(
            df["business_unit"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_business_units = st.multiselect(
            "Business Unit",
            options=business_units,
            key="filter_business_unit",
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
            key="filter_invoice_type",
        )


    if st.button(
        "🧹 Clear Filters",
        key="clear_filters",
    ):

        st.session_state["filter_month"] = "All"
        st.session_state["filter_staff"] = []
        st.session_state["filter_business_unit"] = []
        st.session_state["filter_invoice_type"] = []

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
# FILTER STATUS
# =========================================================

filter_count = (
    (selected_month != "All")
    + bool(selected_staff)
    + bool(selected_business_units)
    + bool(selected_invoice_types)
)

if filter_count:

    st.info(
        f"🔎 {len(filtered_df):,} invoices "
        f"match the selected filters."
    )


# =========================================================
# KPI CALCULATIONS
# =========================================================

invoice_count = len(filtered_df)

invoice_value = filtered_df[
    "invoice_amount"
].sum()

staff_count = filtered_df[
    "user_id"
].nunique()

vendor_count = filtered_df[
    "vendor_name"
].nunique()


# =========================================================
# KPI CARDS
# =========================================================

col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Invoices Processed",
    f"{invoice_count:,}",
)


col2.metric(
    "Invoice Value",
    format_currency(invoice_value),
)


col3.metric(
    "Staff",
    f"{staff_count:,}",
)


col4.metric(
    "Vendors",
    f"{vendor_count:,}",
)


st.divider()


# =========================================================
# TAT
# =========================================================

st.subheader("⏱️ Turnaround Time")

st.info(
    "TAT is currently pending confirmation of the "
    "Shared Drive posting timestamp."
)


st.divider()


# =========================================================
# DAILY TREND
# =========================================================

st.subheader("📈 Daily Processing Trend")

daily = get_daily_summary(
    filtered_df
)


if daily.empty:

    st.info(
        "No daily data available for the "
        "selected filters."
    )

else:

    daily_chart = daily.set_index(
        "processing_day"
    )[["invoices"]]

    st.line_chart(
        daily_chart,
        use_container_width=True,
    )


# =========================================================
# WEEKLY TREND
# =========================================================

st.subheader("📅 Weekly Processing Trend")

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

    weekly_chart = weekly.set_index(
        "week"
    )[["invoices"]]

    st.bar_chart(
        weekly_chart,
        use_container_width=True,
    )


# =========================================================
# MONTHLY TREND
# =========================================================

st.subheader("🗓️ Monthly Processing Trend")

monthly = get_monthly_summary(
    filtered_df
)


if monthly.empty:

    st.info(
        "No monthly data available."
    )

else:

    monthly_chart = monthly.set_index(
        "reporting_month"
    )[["invoices"]]

    st.line_chart(
        monthly_chart,
        use_container_width=True,
    )


# =========================================================
# MONTHLY VALUE
# =========================================================

st.subheader("💰 Monthly Invoice Value")


if monthly.empty:

    st.info(
        "No invoice value data available."
    )

else:

    monthly_value_chart = monthly.set_index(
        "reporting_month"
    )[["invoice_value"]]

    st.bar_chart(
        monthly_value_chart,
        use_container_width=True,
    )


# =========================================================
# CURRENT DATA SUMMARY
# =========================================================

st.divider()

st.subheader("📋 Current Selection")

summary_col1, summary_col2 = st.columns(2)


with summary_col1:

    st.write(
        f"**Invoices:** {len(filtered_df):,}"
    )

    st.write(
        f"**Staff:** "
        f"{filtered_df['user_id'].nunique():,}"
    )

    st.write(
        f"**Vendors:** "
        f"{filtered_df['vendor_name'].nunique():,}"
    )


with summary_col2:

    st.write(
        f"**Invoice Value:** "
        f"{format_currency(invoice_value)}"
    )

    st.write(
        f"**Business Units:** "
        f"{filtered_df['business_unit'].nunique():,}"
    )

    st.write(
        f"**Invoice Types:** "
        f"{filtered_df['invoice_type'].nunique():,}"
    )