from pathlib import Path
import datetime
import logging
import os

try:
    import pythoncom
    import win32com.client
except Exception:  # pragma: no cover - import may not be present in CI
    pythoncom = None
    win32com = None

from app.services.invoice_importer import import_weekly_report


LOG = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
UPLOADS_DIR = BASE_DIR / "uploads"


def ensure_uploads_dir() -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def find_and_download_reports(
    subject_keyword: str = "ap bts weekly report",
) -> list[str]:

    if win32com is None or pythoncom is None:
        raise ImportError(
            "pywin32 is required for Outlook automation. "
            "Install with: pip install pywin32"
        )

    ensure_uploads_dir()

    pythoncom.CoInitialize()

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")

        inbox = ns.GetDefaultFolder(6)  # 6 == olFolderInbox

        items = inbox.Items

        # Sort by ReceivedTime descending
        try:
            items.Sort("[ReceivedTime]", True)
        except Exception:
            pass

        saved_files: list[str] = []

        for item in list(items):
            try:
                subject = str(getattr(item, "Subject", "") or "")
            except Exception:
                continue

            if subject_keyword.lower() not in subject.lower():
                continue

            attachments = getattr(item, "Attachments", None)

            if not attachments:
                continue

            for i in range(1, attachments.Count + 1):

                try:
                    attachment = attachments.Item(i)

                    filename = str(
                        getattr(attachment, "FileName", "") or ""
                    )

                    if not filename:
                        continue

                    # Only download Excel files
                    if not filename.lower().endswith(
                        (".xlsx", ".xls")
                    ):
                        continue

                    timestamp = datetime.datetime.now().strftime(
                        "%Y%m%d%H%M%S"
                    )

                    save_name = f"{timestamp}_{filename}"
                    save_path = UPLOADS_DIR / save_name
                    save_path = save_path.resolve()

                    attachment.SaveAsFile(str(save_path))

                    saved_files.append(str(save_path))

                    LOG.info(
                        "Saved attachment %s to %s",
                        filename,
                        save_path,
                    )

                except Exception:
                    LOG.exception(
                        "Failed to process attachment in email: %s",
                        subject,
                    )

        return saved_files

    finally:
        # Release COM for this thread
        pythoncom.CoUninitialize()


def process_existing_emails(
    subject_keyword: str = "ap bts weekly report",
) -> list[dict]:


    results: list[dict] = []

    try:
        files = find_and_download_reports(
            subject_keyword=subject_keyword
        )

    except Exception as exc:
        LOG.exception(
            "Error while accessing Outlook: %s",
            exc,
        )
        raise

    for f in files:

        try:
            res = import_weekly_report(f)
            results.append(res)

        except Exception:
            LOG.exception(
                "Failed to import report %s",
                f,
            )

            results.append(
                {
                    "filename": os.path.basename(f),
                    "status": "FAILED",
                }
            )

    return results