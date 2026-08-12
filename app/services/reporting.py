import pandas as pd
from sqlalchemy import text

from app.db.database import engine


def load_invoices() -> pd.DataFrame:
    query = text("""
        SELECT
            id,
            user_id,
            invoice_processing_date,
            invoice_date,
            invoice_number,
            invoice_type,
            vendor_name,
            vendor_id,
            business_unit,
            invoice_amount,
            invoice_tax_amount,
            currency,
            reporting_month,
            reporting_year,
            reporting_week,
            source_file,
            shared_drive_posted_at,
            tat_minutes
        FROM invoices
        ORDER BY invoice_processing_date
    """)

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    if not df.empty:
        df["invoice_processing_date"] = pd.to_datetime(
            df["invoice_processing_date"]
        )

        df["invoice_date"] = pd.to_datetime(
            df["invoice_date"]
        )

    return df


def load_upload_history() -> pd.DataFrame:
    query = text("""
        SELECT
            id,
            filename,
            rows_found,
            rows_inserted,
            duplicates_found,
            status,
            uploaded_at
        FROM uploads
        ORDER BY uploaded_at DESC
    """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def get_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("reporting_month")
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values("reporting_month")
    )


def get_weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby(
            ["reporting_year", "reporting_week"]
        )
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values(
            ["reporting_year", "reporting_week"]
        )
    )


def get_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    daily = (
        df.assign(
            processing_day=df[
                "invoice_processing_date"
            ].dt.date
        )
        .groupby("processing_day")
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
        )
        .reset_index()
    )

    return daily.sort_values("processing_day")


def get_staff_summary(df):

    if df.empty:
        return pd.DataFrame(
            columns=[
                "user_id",
                "invoices",
                "invoice_value",
                "vendors",
            ]
        )


    summary = (
        df.groupby("user_id", dropna=False)
        .agg(
            invoices=(
                "invoice_number",
                "count",
            ),
            invoice_value=(
                "invoice_amount",
                "sum",
            ),
            vendors=(
                "vendor_name",
                "nunique",
            ),
        )
        .reset_index()
    )


    summary["user_id"] = (
        summary["user_id"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )


    return (
        summary
        .sort_values(
            "invoices",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def get_business_unit_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("business_unit")
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
            vendors=("vendor_name", "nunique"),
        )
        .reset_index()
        .sort_values(
            "invoices",
            ascending=False,
        )
    )