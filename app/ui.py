import streamlit as st


def configure_page(title: str):
    st.set_page_config(
        page_title=title,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def sidebar_header():
    st.sidebar.title("📊 Invoice Dashboard")

    st.sidebar.caption(
        "Invoice Processing Reporting System"
    )


def format_currency(value) -> str:
    if value is None:
        return "R0.00"

    return f"R{float(value):,.2f}"