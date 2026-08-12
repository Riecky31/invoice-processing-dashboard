from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.excel_reader import read_weekly_report
from app.db.database import engine
from app.db.models import Invoice, Upload


def generate_record_id(invoice_number: str, vendor_id: str) -> str:
   

    value = f"{invoice_number}|{vendor_id}"

    return str(uuid5(NAMESPACE_URL, value))


def import_weekly_report(file_path: str | Path) -> dict:
   

    file_path = Path(file_path)

   
    df = read_weekly_report(file_path)

    rows_found = len(df)
    rows_inserted = 0
    duplicates_found = 0

    with Session(engine) as session:

        for _, row in df.iterrows():

            record_id = generate_record_id(
                str(row["Invoice Number"]),
                str(row["Vendor ID"]),
            )

            existing_invoice = session.scalar(
                select(Invoice).where(
                    Invoice.record_id == record_id
                )
            )

            if existing_invoice:
                duplicates_found += 1
                continue

            invoice = Invoice(
                record_id=record_id,
                user_id=str(row["User ID"]),
                invoice_processing_date=row[
                    "Invoice Processing Date"
                ].to_pydatetime(),
                invoice_date=row[
                    "Invoice Date"
                ].to_pydatetime(),
                invoice_number=str(
                    row["Invoice Number"]
                ),
                invoice_type=str(
                    row["Invoice Type"]
                ),
                vendor_name=str(
                    row["Vendor Name"]
                ),
                vendor_id=str(
                    row["Vendor ID"]
                ),
                business_unit=str(
                    row["Business Unit"]
                ),
                invoice_amount=row[
                    "Invoice Amount"
                ],
                invoice_tax_amount=row[
                    "Invoice Tax Amount"
                ],
                currency=str(
                    row["Currency"]
                ),
                reporting_month=str(
                    row["Reporting Month"]
                ),
                reporting_year=int(
                    row["Reporting Year"]
                ),
                reporting_week=int(
                    row["Reporting Week"]
                ),
                source_file=file_path.name,
            )

            session.add(invoice)

            rows_inserted += 1

        upload = Upload(
            filename=file_path.name,
            rows_found=rows_found,
            rows_inserted=rows_inserted,
            duplicates_found=duplicates_found,
            status="SUCCESS",
        )

        session.add(upload)

        session.commit()

    return {
        "filename": file_path.name,
        "rows_found": rows_found,
        "rows_inserted": rows_inserted,
        "duplicates_found": duplicates_found,
        "status": "SUCCESS",
    }