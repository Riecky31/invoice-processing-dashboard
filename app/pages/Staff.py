import streamlit as st

from app.ui import (
    configure_page,
    sidebar_header,
    format_currency,
)

from app.services.reporting import (
    load_invoices,
    get_staff_summary,
)


configure_page("Staff Performance")

sidebar_header()


# =========================================================
# PAGE HEADER
# =========================================================

st.title("👥 Staff Performance")

st.caption(
    "Invoice processing activity by User ID"
)


# =========================================================
# LOAD DATA
# =========================================================

df = load_invoices()


if df.empty:

    st.warning(
        "No invoice data available."
    )

    st.stop()


# =========================================================
# STAFF SUMMARY
# =========================================================

summary = get_staff_summary(
    df
)


if summary.empty:

    st.info(
        "No staff records are available."
    )

    st.stop()


# =========================================================
# SEARCH
# =========================================================

search = st.text_input(
    "🔎 Search staff",
    placeholder="Type a staff name...",
)


display_summary = summary.copy()


if search:

    display_summary = display_summary[
        display_summary["user_id"]
        .str.contains(
            search,
            case=False,
            na=False,
        )
    ]


# =========================================================
# KPIs
# =========================================================

col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Total Staff",
    f"{summary['user_id'].nunique():,}",
)


col2.metric(
    "Total Invoices",
    f"{summary['invoices'].sum():,}",
)


col3.metric(
    "Total Invoice Value",
    format_currency(
        summary["invoice_value"].sum()
    ),
)


col4.metric(
    "Vendors",
    f"{df['vendor_name'].nunique():,}",
)


st.divider()


# =========================================================
# STAFF COUNT
# =========================================================

st.subheader(
    f"Staff Members ({len(display_summary):,})"
)


if display_summary.empty:

    st.info(
        "No staff match your search."
    )

else:

    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True,
    )


st.divider()


# =========================================================
# INVOICE VOLUME
# =========================================================

st.subheader(
    "📊 Invoices Processed by Staff"
)


if not display_summary.empty:

    volume_chart = (
        display_summary
        .set_index("user_id")
        [["invoices"]]
        .sort_values(
            "invoices",
            ascending=False,
        )
    )

    st.bar_chart(
        volume_chart,
        use_container_width=True,
    )


# =========================================================
# INVOICE VALUE
# =========================================================

st.subheader(
    "💰 Invoice Value by Staff"
)


if not display_summary.empty:

    value_chart = (
        display_summary
        .set_index("user_id")
        [["invoice_value"]]
        .sort_values(
            "invoice_value",
            ascending=False,
        )
    )

    st.bar_chart(
        value_chart,
        use_container_width=True,
    )


# =========================================================
# DETAILED STAFF TABLE
# =========================================================

st.subheader(
    "📋 Detailed Staff Performance"
)


if not display_summary.empty:

    detailed = display_summary.copy()


    total_invoices = summary[
        "invoices"
    ].sum()


    if total_invoices > 0:

        detailed["invoice_share"] = (
            detailed["invoices"]
            / total_invoices
            * 100
        )

    else:

        detailed["invoice_share"] = 0


    detailed["invoice_share"] = (
        detailed["invoice_share"]
        .round(1)
        .astype(str)
        + "%"
    )


    detailed["invoice_value"] = (
        detailed["invoice_value"]
        .map(format_currency)
    )


    detailed = detailed.rename(
        columns={
            "user_id": "Staff",
            "invoices": "Invoices",
            "invoice_value": "Invoice Value",
            "vendors": "Vendors",
            "invoice_share": "% of Invoices",
        }
    )


    st.dataframe(
        detailed[
            [
                "Staff",
                "Invoices",
                "Invoice Value",
                "Vendors",
                "% of Invoices",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )