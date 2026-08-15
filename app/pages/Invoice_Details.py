import streamlit as st

from app.ui import (
    configure_page,
    sidebar_header,
)

from app.services.reporting import load_invoices


configure_page("Invoice Details")

sidebar_header()

st.title("📑 Invoice Details")

df = load_invoices()

if df.empty:
    st.warning("No invoice data available.")
    st.stop()

col1, col2 = st.columns(2)

with col1:

    search = st.text_input(
        "Search invoice / vendor",
        placeholder=(
            "Enter invoice number or vendor"
        ),
    )


with col2:

    currency = st.multiselect(
        "Currency",
        sorted(
            df["currency"]
            .dropna()
            .unique()
        ),
    )


filtered = df.copy()


if search:

    search_lower = search.lower()

    filtered = filtered[
        filtered["invoice_number"]
        .str.lower()
        .str.contains(
            search_lower,
            na=False,
        )
        |
        filtered["vendor_name"]
        .str.lower()
        .str.contains(
            search_lower,
            na=False,
        )
    ]


if currency:

    filtered = filtered[
        filtered["currency"]
        .isin(currency)
    ]



display_columns = [
    "user_id",
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
]


st.write(
    f"Showing **{len(filtered):,}** invoices"
)


st.dataframe(
    filtered[display_columns],
    width="stretch",
    hide_index=True,
)