from pathlib import Path

from app.services.invoice.importer import (
    ImportResult,
    process_weekly_report,
)


def import_weekly_report(file_path: str | Path) -> dict[str, int | str]:
    result = process_weekly_report(file_path)
    return result.to_dict()


__all__ = [
    "ImportResult",
    "import_weekly_report",
    "process_weekly_report",
]
