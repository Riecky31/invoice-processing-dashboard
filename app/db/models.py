from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    record_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    user_id: Mapped[str] = mapped_column(String(100), nullable=False)

    invoice_processing_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    invoice_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    invoice_number: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    invoice_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    vendor_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    vendor_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    business_unit: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )

    invoice_tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10), nullable=False
    )

    reporting_month: Mapped[str] = mapped_column(
        String(7), nullable=False
    )

    reporting_year: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    reporting_week: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    source_file: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    shared_drive_posted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    tat_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    rows_found: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    rows_inserted: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    duplicates_found: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )