import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from app.services.tat.calculator import calculate_tat_minutes
from sqlalchemy import select

from app.data.excel_reader import read_weekly_report
from app.db.database import SessionLocal
from app.db.models import Invoice, Upload


@dataclass(frozen=True)
class ImportResult:
    upload_id: int
    filename: str
    rows_found: int
    rows_inserted: int
    duplicates_found: int
    status: str

    def to_dict(self) -> dict[str, int | str]:
        return {
            "upload_id": self.upload_id,
            "filename": self.filename,
            "rows_found": self.rows_found,
            "rows_inserted": self.rows_inserted,
            "duplicates_found": self.duplicates_found,
            "status": self.status,
        }


def _as_datetime(value: Any) -> datetime:
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()

    return value


def _as_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _as_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text in {"<NA>", "nan", "NaT"}:
        return ""

    return text


def _build_record_id(row: Any) -> str:
    parts = [
        _as_text(row["Invoice Number"]),
        _as_text(row["Vendor ID"]),
        _as_text(row["Business Unit"]),
        _as_datetime(row["Invoice Processing Date"]).isoformat(),
        _as_datetime(row["Invoice Date"]).isoformat(),
        str(_as_decimal(row["Invoice Amount"])),
        str(_as_decimal(row["Invoice Tax Amount"])),
        _as_text(row["Currency"]),
    ]

    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def process_weekly_report(file_path: str | Path) -> ImportResult:
    file_path = Path(file_path)

    with SessionLocal() as session:
        upload = Upload(
            filename=file_path.name,
            status="processing",
        )

        session.add(upload)
        session.commit()
        session.refresh(upload)

        upload_id = upload.id

        try:
            df = read_weekly_report(file_path)

            rows_inserted = 0
            duplicates_found = 0

            for _, row in df.iterrows():

                record_id = _build_record_id(row)

                existing_id = session.scalar(
                    select(Invoice.id).where(
                        Invoice.record_id == record_id
                    )
                )

                if existing_id:
                    duplicates_found += 1
                    continue

                invoice_processing_date = _as_datetime(
                    row["Invoice Processing Date"]
                )

                invoice_date = _as_datetime(
                    row["Invoice Date"]
                )

                tat_minutes = calculate_tat_minutes(
                    invoice_date,
                    invoice_processing_date,
                )

      
                invoice = Invoice(
                    record_id=record_id,

                    user_id=_as_text(
                        row["User ID"]
                    ),

                    invoice_processing_date=invoice_processing_date,

                    invoice_date=invoice_date,

                    invoice_number=_as_text(
                        row["Invoice Number"]
                    ),

                    invoice_type=_as_text(
                        row["Invoice Type"]
                    ),

                    vendor_name=_as_text(
                        row["Vendor Name"]
                    ),

                    vendor_id=_as_text(
                        row["Vendor ID"]
                    ),

                    business_unit=_as_text(
                        row["Business Unit"]
                    ),

                    invoice_amount=_as_decimal(
                        row["Invoice Amount"]
                    ),

                    invoice_tax_amount=_as_decimal(
                        row["Invoice Tax Amount"]
                    ),

                    currency=_as_text(
                        row["Currency"]
                    ),

                    reporting_month=_as_text(
                        row["Reporting Month"]
                    ),

                    reporting_year=int(
                        row["Reporting Year"]
                    ),

                    reporting_week=int(
                        row["Reporting Week"]
                    ),

                    source_file=file_path.name,

                    tat_minutes=tat_minutes,
                )

                session.add(invoice)

                rows_inserted += 1

     
            upload.rows_found = len(df)

            upload.rows_inserted = rows_inserted

            upload.duplicates_found = duplicates_found

            upload.status = "completed"

            session.commit()

            return ImportResult(
                upload_id=upload_id,
                filename=file_path.name,
                rows_found=len(df),
                rows_inserted=rows_inserted,
                duplicates_found=duplicates_found,
                status="completed",
            )

        except Exception:

            session.rollback()

            failed_upload = session.get(
                Upload,
                upload_id,
            )

            if failed_upload:
                failed_upload.status = "failed"
                session.commit()

            raise