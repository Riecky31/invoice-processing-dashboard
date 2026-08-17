from app.services.reporting.metrics import (
    calculate_kpis,
    calculate_tat_metrics,
)
import pandas as pd

from app.db.database import SessionLocal
from app.db.models import InvoiceReportRow

from app.services.reporting.reporting import (
    load_invoices,
)

from app.services.reporting.trends import (
    get_daily_summary,
    get_weekly_summary,
    get_monthly_summary,
    get_business_unit_summary,
)


__all__ = [
    "load_invoices",
    "calculate_kpis",
    "calculate_tat_metrics",
    "get_daily_summary",
    "get_weekly_summary",
    "get_monthly_summary",
    "get_business_unit_summary",
]
def get_staff_summary() -> pd.DataFrame:
    with SessionLocal() as session:
        rows = session.query(InvoiceReportRow).all()

        data = [
            {
                "user_id": row.user_id,
                "invoice_count": 1,
                "invoice_amount": float(row.invoice_amount or 0),
                "invoice_tax_amount": float(
                    row.invoice_tax_amount or 0
                ),
            }
            for row in rows
        ]

    if not data:
        return pd.DataFrame(
            columns=[
                "user_id",
                "invoice_count",
                "invoice_amount",
                "invoice_tax_amount",
            ]
        )

    df = pd.DataFrame(data)

    summary = (
        df.groupby("user_id", dropna=False)
        .agg(
            invoice_count=("invoice_count", "sum"),
            invoice_amount=("invoice_amount", "sum"),
            invoice_tax_amount=("invoice_tax_amount", "sum"),
        )
        .reset_index()
        .sort_values("invoice_count", ascending=False)
    )

    return summary