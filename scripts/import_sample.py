from app.services.invoice_importer import import_weekly_report


FILE_PATH = (
    "data/sample/"
    "AP BTS Weekly Report 3rd Aug to 9th Aug, 2026.xlsx"
)


if __name__ == "__main__":
    result = import_weekly_report(FILE_PATH)

    print("\nUpload complete!")
    print("------------------------------")
    print(f"File:       {result['filename']}")
    print(f"Rows found: {result['rows_found']}")
    print(f"Inserted:   {result['rows_inserted']}")
    print(f"Duplicates: {result['duplicates_found']}")
    print(f"Status:     {result['status']}")