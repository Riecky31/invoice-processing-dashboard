import pandas as pd
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Invoice


def load_invoices() -> pd.DataFrame:
    """
    Load all invoices from the database into a pandas DataFrame.
    """

    with SessionLocal() as session:
        invoices = session.scalars(
            select(Invoice)
            .order_by(Invoice.invoice_processing_date)
        ).all()

    if not invoices:
        return pd.DataFrame()

    rows = []

    for invoice in invoices:
        rows.append(
            {
                "id": invoice.id,
                "record_id": invoice.record_id,
                "user_id": invoice.user_id,
                "invoice_processing_date": invoice.invoice_processing_date,
                "invoice_date": invoice.invoice_date,
                "invoice_number": invoice.invoice_number,
                "invoice_type": invoice.invoice_type,
                "vendor_name": invoice.vendor_name,
                "vendor_id": invoice.vendor_id,
                "business_unit": invoice.business_unit,
                "invoice_amount": float(invoice.invoice_amount),
                "invoice_tax_amount": float(invoice.invoice_tax_amount),
                "currency": invoice.currency,
                "reporting_month": invoice.reporting_month,
                "reporting_year": invoice.reporting_year,
                "reporting_week": invoice.reporting_week,
                "source_file": invoice.source_file,
                "shared_drive_posted_at": invoice.shared_drive_posted_at,
                "tat_minutes": invoice.tat_minutes,
                "created_at": invoice.created_at,
            }
        )

    df = pd.DataFrame(rows)

    # Ensure date columns are datetime
    date_columns = [
        "invoice_processing_date",
        "invoice_date",
        "shared_drive_posted_at",
        "created_at",
    ]

    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    # TAT in hours for reporting
    if "tat_minutes" in df.columns:
        df["tat_hours"] = df["tat_minutes"] / 60

    return df