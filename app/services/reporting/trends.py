from __future__ import annotations

import pandas as pd


def get_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return invoice count and amount by processing day.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "invoice_count",
                "total_amount",
            ]
        )

    data = df.copy()

    data["date"] = pd.to_datetime(
        data["invoice_processing_date"],
        errors="coerce",
    ).dt.date

    summary = (
        data.dropna(subset=["date"])
        .groupby("date")
        .agg(
            invoice_count=("invoice_number", "count"),
            total_amount=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values("date")
    )

    return summary


def get_weekly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return invoice count and amount by reporting week.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "reporting_year",
                "reporting_week",
                "invoice_count",
                "total_amount",
            ]
        )

    summary = (
        df.groupby(
            [
                "reporting_year",
                "reporting_week",
            ]
        )
        .agg(
            invoice_count=("invoice_number", "count"),
            total_amount=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values(
            [
                "reporting_year",
                "reporting_week",
            ]
        )
    )

    return summary


def get_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return invoice count and amount by reporting month.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "reporting_month",
                "invoice_count",
                "total_amount",
            ]
        )

    summary = (
        df.groupby("reporting_month")
        .agg(
            invoice_count=("invoice_number", "count"),
            total_amount=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values("reporting_month")
    )

    return summary


def get_business_unit_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return invoice volume and amount grouped by business unit.
    """

    if df.empty:
        return pd.DataFrame(
            columns=[
                "business_unit",
                "invoice_count",
                "total_amount",
            ]
        )

    result = (
        df.groupby("business_unit", dropna=False)
        .agg(
            invoice_count=("id", "count"),
            total_amount=("invoice_amount", "sum"),
        )
        .reset_index()
    )

    result["business_unit"] = (
        result["business_unit"]
        .fillna("Unknown")
        .astype(str)
    )

    return result.sort_values(
        "total_amount",
        ascending=False,
    ).reset_index(drop=True)