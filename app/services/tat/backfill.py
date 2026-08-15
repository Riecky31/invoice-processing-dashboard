from app.db.database import SessionLocal
from app.db.models import Invoice
from app.services.tat.calculator import calculate_tat_minutes


def backfill_tat() -> int:
    updated = 0

    with SessionLocal() as session:
        invoices = session.query(Invoice).all()

        for invoice in invoices:

            if (
                invoice.invoice_date is None
                or invoice.invoice_processing_date is None
            ):
                continue

            invoice.tat_minutes = calculate_tat_minutes(
                invoice.invoice_date,
                invoice.invoice_processing_date,
            )

            updated += 1

        session.commit()

    return updated


if __name__ == "__main__":
    count = backfill_tat()
    print(f"Updated TAT for {count} invoices.")