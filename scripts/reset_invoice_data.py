from app.db.database import SessionLocal
from app.db.models import Invoice, Upload, EmailAttachmentImport


def reset_invoice_data():
    with SessionLocal() as session:

        invoice_count = session.query(Invoice).count()
        upload_count = session.query(Upload).count()
        email_import_count = session.query(
            EmailAttachmentImport
        ).count()

        session.query(Invoice).delete()
        session.query(EmailAttachmentImport).delete()
        session.query(Upload).delete()

        session.commit()

    print("Database reset completed.")
    print(f"Invoices deleted: {invoice_count}")
    print(f"Uploads deleted: {upload_count}")
    print(f"Email imports deleted: {email_import_count}")


if __name__ == "__main__":
    reset_invoice_data()