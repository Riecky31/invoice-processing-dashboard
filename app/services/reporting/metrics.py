import pandas as pd


def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate the main dashboard KPIs.
    """

    if df.empty:
        return {
            "invoice_count": 0,
            "invoice_value": 0.0,
            "staff_count": 0,
            "vendor_count": 0,
            "business_unit_count": 0,
            "invoice_type_count": 0,
        }

    return {
        "invoice_count": len(df),

        "invoice_value": float(
            pd.to_numeric(
                df["invoice_amount"],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        ),

        "staff_count": int(
            df["user_id"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        ),

        "vendor_count": int(
            df["vendor_name"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        ),

        "business_unit_count": int(
            df["business_unit"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        ),

        "invoice_type_count": int(
            df["invoice_type"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        ),
    }


def calculate_tat_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate TAT statistics from tat_minutes.

    TAT calculation itself belongs to:
        app.services.tat.calculator

    This function only calculates reporting statistics.
    """

    empty_result = {
        "tat_count": 0,
        "average_tat_minutes": None,
        "average_tat_hours": None,
        "median_tat_minutes": None,
        "median_tat_hours": None,
        "minimum_tat_minutes": None,
        "maximum_tat_minutes": None,
    }

    if df.empty:
        return empty_result

    if "tat_minutes" not in df.columns:
        return empty_result

    tat = pd.to_numeric(
        df["tat_minutes"],
        errors="coerce",
    ).dropna()

    # Only valid TAT values
    tat = tat[tat >= 0]

    if tat.empty:
        return empty_result

    average_minutes = float(tat.mean())
    median_minutes = float(tat.median())
    minimum_minutes = float(tat.min())
    maximum_minutes = float(tat.max())

    return {
        "tat_count": int(len(tat)),

        "average_tat_minutes": round(
            average_minutes,
            2,
        ),

        "average_tat_hours": round(
            average_minutes / 60,
            2,
        ),

        "median_tat_minutes": round(
            median_minutes,
            2,
        ),

        "median_tat_hours": round(
            median_minutes / 60,
            2,
        ),

        "minimum_tat_minutes": round(
            minimum_minutes,
            2,
        ),

        "maximum_tat_minutes": round(
            maximum_minutes,
            2,
        ),
    }