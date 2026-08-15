from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "User ID",
    "Invoice Processing Date",
    "Invoice Date",
    "Invoice Number",
    "Invoice Type",
    "Vendor Name",
    "Vendor ID",
    "Business Unit",
    "Invoice Amount",
    "Invoice Tax Amount",
    "Currency",
]


def parse_excel_datetime(series: pd.Series) -> pd.Series:
  
    return pd.to_datetime(
        series,
        format="mixed",
        dayfirst=True,
        errors="coerce",
    )


def read_weekly_report(file_path: str | Path) -> pd.DataFrame:
   

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_path.suffix.lower() not in [".xlsx", ".xls"]:
        raise ValueError(
            "The uploaded file must be an Excel workbook."
        )

    # Read Excel
    df = pd.read_excel(file_path)

    # Remove completely empty rows
    df = df.dropna(how="all").copy()

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The following required columns are missing: "
            + ", ".join(missing_columns)
        )

    df["Invoice Processing Date"] = parse_excel_datetime(
        df["Invoice Processing Date"]
    )

    df["Invoice Date"] = parse_excel_datetime(
        df["Invoice Date"]
    )

    # Validate dates
    date_columns = [
        "Invoice Processing Date",
        "Invoice Date",
    ]

    for column in date_columns:
        invalid_count = df[column].isna().sum()

        if invalid_count > 0:
            raise ValueError(
                f"{column} contains "
                f"{invalid_count} invalid date value(s)."
            )

    

    df["Invoice Amount"] = pd.to_numeric(
        df["Invoice Amount"],
        errors="coerce",
    )

    df["Invoice Tax Amount"] = pd.to_numeric(
        df["Invoice Tax Amount"],
        errors="coerce",
    )

    # Validate numeric fields
    numeric_columns = [
        "Invoice Amount",
        "Invoice Tax Amount",
    ]

    for column in numeric_columns:
        invalid_count = df[column].isna().sum()

        if invalid_count > 0:
            raise ValueError(
                f"{column} contains "
                f"{invalid_count} invalid numeric value(s)."
            )

  

    text_columns = [
        "User ID",
        "Invoice Number",
        "Invoice Type",
        "Vendor Name",
        "Vendor ID",
        "Business Unit",
        "Currency",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    required_value_columns = [
        "User ID",
        "Invoice Number",
        "Vendor Name",
        "Vendor ID",
        "Business Unit",
        "Currency",
    ]

    for column in required_value_columns:
        missing_count = df[column].isna().sum()

        if missing_count > 0:
            raise ValueError(
                f"{column} contains "
                f"{missing_count} missing value(s)."
            )


    df["Reporting Month"] = (
        df["Invoice Processing Date"]
        .dt.to_period("M")
        .astype(str)
    )

    df["Reporting Year"] = (
        df["Invoice Processing Date"]
        .dt.year
    )

    df["Reporting Week"] = (
        df["Invoice Processing Date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    return df