import pandas as pd


def get_staff_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

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

    summary.loc[
        summary["user_id"] == "",
        "user_id",
    ] = "Unknown"

    return (
        summary.sort_values(
            "invoices",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def get_business_unit_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(
            columns=[
                "business_unit",
                "invoices",
                "invoice_value",
                "vendors",
            ]
        )

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
        .reset_index(drop=True)
    )
