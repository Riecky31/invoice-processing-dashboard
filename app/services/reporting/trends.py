import pandas as pd


def get_daily_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(
            columns=[
                "processing_day",
                "invoices",
                "invoice_value",
            ]
        )

    data = df.copy()

    data["processing_day"] = (
        pd.to_datetime(
            data["invoice_processing_date"],
            errors="coerce",
        )
        .dt.date
    )

    data = data.dropna(
        subset=["processing_day"]
    )

    if data.empty:
        return pd.DataFrame(
            columns=[
                "processing_day",
                "invoices",
                "invoice_value",
            ]
        )

    summary = (
        data.groupby("processing_day")
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values("processing_day")
    )

    return summary


def get_weekly_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(
            columns=[
                "reporting_year",
                "reporting_week",
                "invoices",
                "invoice_value",
            ]
        )

    data = df.copy()

    summary = (
        data.groupby(
            [
                "reporting_year",
                "reporting_week",
            ]
        )
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
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


def get_monthly_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(
            columns=[
                "reporting_month",
                "invoices",
                "invoice_value",
            ]
        )

    data = df.copy()

    summary = (
        data.groupby("reporting_month")
        .agg(
            invoices=("invoice_number", "count"),
            invoice_value=("invoice_amount", "sum"),
        )
        .reset_index()
        .sort_values("reporting_month")
    )

    return summary


def get_daily_tat_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty or "tat_minutes" not in df.columns:
        return pd.DataFrame(
            columns=[
                "processing_day",
                "average_tat_hours",
                "median_tat_hours",
            ]
        )

    data = df.copy()

    data["processing_day"] = (
        pd.to_datetime(
            data["invoice_processing_date"],
            errors="coerce",
        )
        .dt.date
    )

    data["tat_minutes"] = pd.to_numeric(
        data["tat_minutes"],
        errors="coerce",
    )

    data = data[
        data["tat_minutes"].notna()
        & (data["tat_minutes"] >= 0)
    ]

    if data.empty:
        return pd.DataFrame(
            columns=[
                "processing_day",
                "average_tat_hours",
                "median_tat_hours",
            ]
        )

    summary = (
        data.groupby("processing_day")
        .agg(
            average_tat_minutes=(
                "tat_minutes",
                "mean",
            ),
            median_tat_minutes=(
                "tat_minutes",
                "median",
            ),
        )
        .reset_index()
    )

    summary["average_tat_hours"] = (
        summary["average_tat_minutes"] / 60
    )

    summary["median_tat_hours"] = (
        summary["median_tat_minutes"] / 60
    )

    return summary[
        [
            "processing_day",
            "average_tat_hours",
            "median_tat_hours",
        ]
    ]


def get_monthly_tat_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty or "tat_minutes" not in df.columns:
        return pd.DataFrame(
            columns=[
                "reporting_month",
                "average_tat_hours",
                "median_tat_hours",
            ]
        )

    data = df.copy()

    data["tat_minutes"] = pd.to_numeric(
        data["tat_minutes"],
        errors="coerce",
    )

    data = data[
        data["tat_minutes"].notna()
        & (data["tat_minutes"] >= 0)
    ]

    if data.empty:
        return pd.DataFrame(
            columns=[
                "reporting_month",
                "average_tat_hours",
                "median_tat_hours",
            ]
        )

    summary = (
        data.groupby("reporting_month")
        .agg(
            average_tat_minutes=(
                "tat_minutes",
                "mean",
            ),
            median_tat_minutes=(
                "tat_minutes",
                "median",
            ),
        )
        .reset_index()
        .sort_values("reporting_month")
    )

    summary["average_tat_hours"] = (
        summary["average_tat_minutes"] / 60
    )

    summary["median_tat_hours"] = (
        summary["median_tat_minutes"] / 60
    )

    return summary[
        [
            "reporting_month",
            "average_tat_hours",
            "median_tat_hours",
        ]
    ]