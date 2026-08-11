from app.data.excel_reader import read_weekly_report


FILE_PATH = (
    "data/sample/"
    "AP BTS Weekly Report 3rd Aug to 9th Aug, 2026.xlsx"
)


if __name__ == "__main__":
    df = read_weekly_report(FILE_PATH)

    print("Excel file loaded and transformed successfully!")
    print(f"Rows found: {len(df)}")

    print("\nData types:")
    print(df.dtypes)

    print("\nReporting periods:")
    print(
        df[
            [
                "Invoice Processing Date",
                "Reporting Month",
                "Reporting Year",
                "Reporting Week",
            ]
        ].to_string(index=False)
    )

    print("\nAmount summary:")
    print(df[["Invoice Amount", "Invoice Tax Amount"]].describe())