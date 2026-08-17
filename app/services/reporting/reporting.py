from __future__ import annotations

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
            select(Invoice).order_by(Invoice.invoice_processing_date)
        ).all()

    if not invoices:
        return pd.DataFrame(
            columns=[
                "id",
                "record_id",
                "user_id",
                "invoice_processing_date",
                "invoice_date",
                "invoice_number",
                "invoice_type",
                "vendor_name",
                "vendor_id",
                "business_unit",
                "invoice_amount",
                "invoice_tax_amount",
                "currency",
                "reporting_month",
                "reporting_year",
                "reporting_week",
                "source_file",
                "shared_drive_posted_at",
                "tat_minutes",
                "created_at",
            ]
        )

    records = []

    for invoice in invoices:
        records.append(
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
                "invoice_amount": float(invoice.invoice_amount or 0),
                "invoice_tax_amount": float(invoice.invoice_tax_amount or 0),
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

    df = pd.DataFrame(records)

    if not df.empty:
        df["invoice_processing_date"] = pd.to_datetime(
            df["invoice_processing_date"],
            errors="coerce",
        )

        df["invoice_date"] = pd.to_datetime(
            df["invoice_date"],
            errors="coerce",
        )

        df["shared_drive_posted_at"] = pd.to_datetime(
            df["shared_drive_posted_at"],
            errors="coerce",
        )

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce",
        )

        df["tat_hours"] = df["tat_minutes"] / 60

    return df