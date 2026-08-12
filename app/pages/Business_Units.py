import streamlit as st

from app.ui import (
    configure_page,
    sidebar_header,
    format_currency,
)

from app.services.reporting import (
    load_invoices,
    get_business_unit_summary,
)


configure_page("Business Units")

sidebar_header()

st.title("🏢 Business Unit Analysis")

df = load_invoices()

if df.empty:
    st.warning("No invoice data available.")
    st.stop()


summary = get_business_unit_summary(df)


col1, col2, col3 = st.columns(3)

col1.metric(
    "Business Units",
    summary["business_unit"].nunique(),
)

col2.metric(
    "Invoices",
    f"{summary['invoices'].sum():,}",
)

col3.metric(
    "Invoice Value",
    format_currency(
        summary["invoice_value"].sum()
    ),
)


st.divider()


st.subheader("Invoices by Business Unit")

st.bar_chart(
    summary.set_index("business_unit")[
        ["invoices"]
    ]
)


st.subheader("Invoice Value by Business Unit")

st.bar_chart(
    summary.set_index("business_unit")[
        ["invoice_value"]
    ]
)


st.subheader("Business Unit Summary")

display = summary.copy()

display["invoice_value"] = display[
    "invoice_value"
].map(
    lambda x: f"R{x:,.2f}"
)

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
)