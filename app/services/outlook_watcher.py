from pathlib import Path
import datetime
import logging
import os

try:
    import win32com.client
except Exception:  # pragma: no cover - import may not be present in CI
    win32com = None

from app.services.invoice_importer import import_weekly_report

LOG = logging.getLogger(__name__)

UPLOADS_DIR = Path("uploads")


def ensure_uploads_dir() -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def find_and_download_reports(subject_keyword: str = "ap bts weekly report") -> list[str]:
    """Search the Outlook Inbox for emails whose subject contains
    `subject_keyword` (case-insensitive), download any Excel
    attachments to the project's `uploads/` folder and return saved paths.

    Requires `pywin32` (win32com.client) and Windows Outlook.
    """

    if win32com is None:
        raise ImportError(
            "pywin32 is required for Outlook automation. Install with: pip install pywin32"
        )

    ensure_uploads_dir()

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)  # 6 == olFolderInbox

    items = inbox.Items
    # sort by ReceivedTime descending
    try:
        items.Sort("[ReceivedTime]", True)
    except Exception:
        # Sorting can fail on some Outlook versions; ignore
        pass

    saved_files: list[str] = []

    for item in list(items):
        try:
            subject = str(getattr(item, "Subject", "") or "")
        except Exception:
            continue

        if subject_keyword.lower() in subject.lower():
            attachments = getattr(item, "Attachments", None)
            if not attachments:
                continue

            for i in range(1, attachments.Count + 1):
                attachment = attachments.Item(i)
                filename = str(getattr(attachment, "FileName", ""))
                if not filename:
                    continue

                if not filename.lower().endswith((".xlsx", ".xls")):
                    continue

                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                save_name = f"{timestamp}_{filename}"
                save_path = UPLOADS_DIR / save_name

                try:
                    attachment.SaveAsFile(str(save_path))
                    saved_files.append(str(save_path))
                    LOG.info("Saved attachment %s to %s", filename, save_path)
                except Exception:
                    LOG.exception("Failed to save attachment %s", filename)

    return saved_files


def process_existing_emails(subject_keyword: str = "ap bts weekly report") -> list[dict]:
    """Find matching emails, download Excel attachments and import them
    using the existing importer. Returns a list of import results.
    """

    results: list[dict] = []

    try:
        files = find_and_download_reports(subject_keyword=subject_keyword)
    except Exception as exc:
        LOG.exception("Error while accessing Outlook: %s", exc)
        raise

    for f in files:
        try:
            res = import_weekly_report(f)
            results.append(res)
        except Exception:
            LOG.exception("Failed to import report %s", f)
            results.append({"filename": os.path.basename(f), "status": "FAILED"})

    return results
