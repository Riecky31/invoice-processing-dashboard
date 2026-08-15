import base64
import hashlib
import platform
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sqlalchemy import select

from app.config import Settings, get_settings
from app.db.database import SessionLocal
from app.db.models import EmailAttachmentImport
from app.services.invoice.importer import ImportResult, process_weekly_report


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
FORWARD_PREFIX_RE = re.compile(r"^\s*((fw|fwd|re)\s*:\s*)+", re.IGNORECASE)
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")
EXCEL_EXTENSIONS = {".xls", ".xlsx", ".xlsm"}


class OutlookConfigurationError(RuntimeError):
    pass


class OutlookGraphError(RuntimeError):
    pass


@dataclass(frozen=True)
class AttachmentScanResult:
    message_id: str
    attachment_id: str
    attachment_name: str
    status: str
    downloaded_path: str | None = None
    upload: ImportResult | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "attachment_id": self.attachment_id,
            "attachment_name": self.attachment_name,
            "status": self.status,
            "downloaded_path": self.downloaded_path,
            "upload": self.upload.to_dict() if self.upload else None,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class OutlookScanResult:
    messages_scanned: int = 0
    attachments_matched: int = 0
    attachments_downloaded: int = 0
    attachments_processed: int = 0
    attachments_skipped: int = 0
    attachments_failed: int = 0
    attachment_results: list[AttachmentScanResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages_scanned": self.messages_scanned,
            "attachments_matched": self.attachments_matched,
            "attachments_downloaded": self.attachments_downloaded,
            "attachments_processed": self.attachments_processed,
            "attachments_skipped": self.attachments_skipped,
            "attachments_failed": self.attachments_failed,
            "attachment_results": [
                attachment_result.to_dict()
                for attachment_result in self.attachment_results
            ],
        }


def _normalise_subject(subject: str | None) -> str:
    return FORWARD_PREFIX_RE.sub("", subject or "").strip().lower()


def _contains_reference(value: str | None, reference: str) -> bool:
    return reference.lower() in (value or "").lower()


def _is_excel_attachment(attachment_name: str | None) -> bool:
    return Path(attachment_name or "").suffix.lower() in EXCEL_EXTENSIONS


def _parse_graph_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError:
        return None


def _parse_message_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)

    if hasattr(value, "replace") and hasattr(value, "year"):
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
        )

    return _parse_graph_datetime(str(value))


def _safe_filename(filename: str) -> str:
    safe_name = SAFE_FILENAME_RE.sub("_", filename).strip(" .")
    return safe_name or "attachment.xlsx"


def _sender_email(message: dict[str, Any]) -> str | None:
    if message.get("sender"):
        return message["sender"]

    email_address = (
        message.get("from", {})
        .get("emailAddress", {})
        .get("address")
    )
    return email_address


def _stable_id(value: Any) -> str:
    text = str(value or "")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Win32OutlookClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _namespace(self) -> Any:
        if platform.system() != "Windows":
            raise OutlookConfigurationError(
                "OUTLOOK_PROVIDER=win32 requires Windows with the Outlook "
                "desktop app installed and signed in."
            )

        try:
            import win32com.client
        except ImportError as exc:
            raise OutlookConfigurationError(
                "pywin32 is required for OUTLOOK_PROVIDER=win32. Install it "
                "with `pip install pywin32` inside your Windows environment."
            ) from exc

        outlook = win32com.client.Dispatch("Outlook.Application")
        return outlook.GetNamespace("MAPI")

    def _folder_from_path(self, namespace: Any, folder_path: str) -> Any:
        cleaned_path = folder_path.replace("\\", "/").strip("/")

        if not cleaned_path:
            return namespace.GetDefaultFolder(6)

        parts = [part for part in cleaned_path.split("/") if part]
        folder = namespace.Folders.Item(parts[0])

        for part in parts[1:]:
            folder = folder.Folders.Item(part)

        return folder

    def inbox_folder(self) -> Any:
        namespace = self._namespace()

        if self.settings.outlook_win32_folder_path:
            return self._folder_from_path(
                namespace,
                self.settings.outlook_win32_folder_path,
            )

        return namespace.GetDefaultFolder(6)

    def list_recent_messages(self) -> list[dict[str, Any]]:
        folder = self.inbox_folder()
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        messages: list[dict[str, Any]] = []
        limit = max(self.settings.outlook_scan_limit, 1)
        index = 1

        while index <= items.Count and len(messages) < limit:
            item = items.Item(index)
            index += 1

            if getattr(item, "Class", None) != 43:
                continue

            if getattr(item, "Attachments", None).Count < 1:
                continue

            entry_id = getattr(item, "EntryID", "") or f"{index}-{item.Subject}"
            received_time = getattr(item, "ReceivedTime", None)

            messages.append(
                {
                    "id": _stable_id(entry_id),
                    "subject": getattr(item, "Subject", "") or "",
                    "receivedDateTime": _parse_message_datetime(received_time),
                    "sender": self._sender_email(item),
                    "_item": item,
                }
            )

        return messages

    def _sender_email(self, item: Any) -> str | None:
        sender_email = getattr(item, "SenderEmailAddress", None)

        if sender_email and not str(sender_email).startswith("/O="):
            return sender_email

        try:
            sender = item.Sender

            if sender:
                exchange_user = sender.GetExchangeUser()

                if exchange_user:
                    return exchange_user.PrimarySmtpAddress
        except Exception:
            pass

        return sender_email

    def list_attachments(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        item = message["_item"]
        attachments: list[dict[str, Any]] = []

        for index in range(1, item.Attachments.Count + 1):
            attachment = item.Attachments.Item(index)
            filename = (
                getattr(attachment, "FileName", None)
                or getattr(attachment, "DisplayName", None)
                or f"attachment-{index}.xlsx"
            )

            attachments.append(
                {
                    "id": str(index),
                    "name": filename,
                    "isInline": False,
                    "_attachment": attachment,
                }
            )

        return attachments

    def save_attachment(
        self,
        message: dict[str, Any],
        attachment: dict[str, Any],
    ) -> Path:
        received_value = message.get("receivedDateTime")
        received_date = (
            received_value.strftime("%Y-%m-%d")
            if isinstance(received_value, datetime)
            else "unknown"
        )
        fingerprint = f"{message['id'][:10]}{attachment['id']}"
        filename = _safe_filename(attachment.get("name") or "attachment.xlsx")
        download_dir = self.settings.outlook_download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
        output_path = download_dir / f"{received_date}_{fingerprint}_{filename}"
        attachment["_attachment"].SaveAsFile(str(output_path))
        return output_path


class OutlookGraphClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_access_token(self, interactive: bool = False) -> str:
        if not self.settings.outlook_client_id:
            raise OutlookConfigurationError(
                "OUTLOOK_CLIENT_ID is required before Outlook scans can run."
            )

        if self.settings.uses_app_only_outlook_auth:
            return self._get_app_only_access_token()

        return self._get_delegated_access_token(interactive=interactive)

    def _get_app_only_access_token(self) -> str:
        try:
            import msal
        except ImportError as exc:
            raise OutlookConfigurationError(
                "msal is required for OUTLOOK_PROVIDER=graph."
            ) from exc

        app = msal.ConfidentialClientApplication(
            self.settings.outlook_client_id,
            authority=self.settings.outlook_authority,
            client_credential=self.settings.outlook_client_secret,
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" not in result:
            raise OutlookConfigurationError(
                result.get("error_description")
                or "Microsoft Graph app-only authentication failed."
            )

        return result["access_token"]

    def _get_delegated_access_token(self, interactive: bool = False) -> str:
        try:
            import msal
        except ImportError as exc:
            raise OutlookConfigurationError(
                "msal is required for OUTLOOK_PROVIDER=graph."
            ) from exc

        cache = msal.SerializableTokenCache()
        cache_path = self.settings.outlook_token_cache_path

        if cache_path.exists():
            cache.deserialize(cache_path.read_text())

        app = msal.PublicClientApplication(
            self.settings.outlook_client_id,
            authority=self.settings.outlook_authority,
            token_cache=cache,
        )
        accounts = app.get_accounts()
        account = accounts[0] if accounts else None
        result = app.acquire_token_silent(
            self.settings.outlook_scopes,
            account=account,
        )

        if not result and interactive:
            flow = app.initiate_device_flow(
                scopes=self.settings.outlook_scopes
            )

            if "user_code" not in flow:
                raise OutlookConfigurationError(
                    "Microsoft device-code sign-in could not be started."
                )

            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow)

        if cache.has_state_changed:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(cache.serialize())

        if not result or "access_token" not in result:
            raise OutlookConfigurationError(
                "Outlook is not authorized yet. Run "
                "`python3 scripts/authorize_outlook.py` once, or configure "
                "OUTLOOK_CLIENT_SECRET and OUTLOOK_USER_ID for app-only auth."
            )

        return result["access_token"]

    def mailbox_root(self) -> str:
        if self.settings.uses_app_only_outlook_auth:
            user_id = quote(self.settings.outlook_user_id or "", safe="")
            return f"{GRAPH_BASE_URL}/users/{user_id}"

        return f"{GRAPH_BASE_URL}/me"

    def request(
        self,
        method: str,
        url: str,
        token: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise OutlookConfigurationError(
                "requests is required for OUTLOOK_PROVIDER=graph."
            ) from exc

        response = requests.request(
            method,
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=60,
            **kwargs,
        )

        if response.status_code >= 400:
            raise OutlookGraphError(
                f"Microsoft Graph returned {response.status_code}: "
                f"{response.text}"
            )

        return response.json()

    def list_recent_messages(self, token: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        remaining = max(self.settings.outlook_scan_limit, 1)
        folder = quote(self.settings.outlook_mail_folder, safe="")
        url = f"{self.mailbox_root()}/mailFolders/{folder}/messages"
        params: dict[str, str] | None = {
            "$select": "id,subject,hasAttachments,receivedDateTime,from",
            "$filter": "hasAttachments eq true",
            "$orderby": "receivedDateTime desc",
            "$top": str(min(50, remaining)),
        }

        while url and remaining > 0:
            data = self.request("GET", url, token, params=params)
            page_messages = data.get("value", [])
            messages.extend(page_messages[:remaining])
            remaining -= len(page_messages)
            url = data.get("@odata.nextLink")
            params = None

        return messages

    def list_attachments(
        self,
        message_id: str,
        token: str,
    ) -> list[dict[str, Any]]:
        encoded_message_id = quote(message_id, safe="")
        url = f"{self.mailbox_root()}/messages/{encoded_message_id}/attachments"
        data = self.request("GET", url, token)
        return data.get("value", [])

    def save_attachment(
        self,
        message: dict[str, Any],
        attachment: dict[str, Any],
        token: str,
    ) -> Path:
        attachment_data = attachment

        if "contentBytes" not in attachment_data:
            encoded_message_id = quote(message["id"], safe="")
            encoded_attachment_id = quote(attachment["id"], safe="")
            url = (
                f"{self.mailbox_root()}/messages/{encoded_message_id}"
                f"/attachments/{encoded_attachment_id}"
            )
            attachment_data = self.request("GET", url, token)

        content_bytes = attachment_data.get("contentBytes")

        if not content_bytes:
            raise OutlookGraphError(
                f"Attachment {attachment.get('name')} did not include file bytes."
            )

        received_date = (message.get("receivedDateTime") or "unknown")[:10]
        fingerprint = re.sub(r"[^A-Za-z0-9]+", "", attachment["id"])[:12]
        filename = _safe_filename(attachment.get("name") or "attachment.xlsx")
        download_dir = self.settings.outlook_download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
        output_path = download_dir / f"{received_date}_{fingerprint}_{filename}"
        output_path.write_bytes(base64.b64decode(content_bytes))
        return output_path


def authorize_outlook_device_flow() -> str:
    settings = get_settings()

    if settings.outlook_provider.lower() == "win32":
        return (
            "OUTLOOK_PROVIDER=win32 uses your signed-in Outlook desktop app; "
            "no separate authorization step is required."
        )

    client = OutlookGraphClient()
    client.get_access_token(interactive=True)
    return "Outlook authorization saved."


def _upsert_email_import(
    message: dict[str, Any],
    attachment: dict[str, Any],
) -> tuple[EmailAttachmentImport, bool]:
    with SessionLocal() as session:
        existing = session.scalar(
            select(EmailAttachmentImport).where(
                EmailAttachmentImport.message_id == message["id"],
                EmailAttachmentImport.attachment_id == attachment["id"],
            )
        )

        if existing:
            if existing.status == "completed":
                return existing, False

            existing.status = "processing"
            existing.error_message = None
            session.commit()
            session.refresh(existing)
            return existing, True

        email_import = EmailAttachmentImport(
            message_id=message["id"],
            attachment_id=attachment["id"],
            attachment_name=attachment.get("name") or "attachment.xlsx",
            subject=message.get("subject"),
            sender=_sender_email(message),
            received_at=_parse_message_datetime(message.get("receivedDateTime")),
            status="processing",
        )
        session.add(email_import)
        session.commit()
        session.refresh(email_import)
        return email_import, True


def _update_email_import(
    email_import_id: int,
    *,
    status: str,
    downloaded_path: Path | None = None,
    upload: ImportResult | None = None,
    error_message: str | None = None,
) -> None:
    with SessionLocal() as session:
        email_import = session.get(EmailAttachmentImport, email_import_id)

        if not email_import:
            return

        email_import.status = status
        email_import.downloaded_path = (
            str(downloaded_path) if downloaded_path else email_import.downloaded_path
        )
        email_import.upload_id = upload.upload_id if upload else email_import.upload_id
        email_import.error_message = error_message
        session.commit()


def scan_outlook_inbox() -> OutlookScanResult:
    settings = get_settings()
    provider = settings.outlook_provider.lower()

    if provider == "win32":
        client = Win32OutlookClient(settings)
        messages = client.list_recent_messages()
    elif provider == "graph":
        graph_client = OutlookGraphClient(settings)
        token = graph_client.get_access_token(interactive=False)
        messages = graph_client.list_recent_messages(token)
        client = graph_client
    else:
        raise OutlookConfigurationError(
            "OUTLOOK_PROVIDER must be either `win32` or `graph`."
        )

    reference = client.settings.outlook_subject_reference
    attachment_results: list[AttachmentScanResult] = []
    matched = 0
    downloaded = 0
    processed = 0
    skipped = 0
    failed = 0

    for message in messages:
        subject = message.get("subject")
        subject_matches = _contains_reference(
            _normalise_subject(subject),
            reference,
        )

        if provider == "graph":
            attachments = client.list_attachments(message["id"], token)
        else:
            attachments = client.list_attachments(message)

        for attachment in attachments:
            attachment_name = attachment.get("name") or ""

            if attachment.get("isInline"):
                continue

            if not _is_excel_attachment(attachment_name):
                continue

            if not subject_matches and not _contains_reference(
                attachment_name,
                reference,
            ):
                continue

            matched += 1
            email_import, should_process = _upsert_email_import(message, attachment)

            if not should_process:
                skipped += 1
                attachment_results.append(
                    AttachmentScanResult(
                        message_id=message["id"],
                        attachment_id=attachment["id"],
                        attachment_name=attachment_name,
                        status="skipped",
                        downloaded_path=email_import.downloaded_path,
                    )
                )
                continue

            try:
                if provider == "graph":
                    downloaded_path = client.save_attachment(
                        message,
                        attachment,
                        token,
                    )
                else:
                    downloaded_path = client.save_attachment(
                        message,
                        attachment,
                    )
                downloaded += 1
                import_result = process_weekly_report(downloaded_path)
                processed += 1
                _update_email_import(
                    email_import.id,
                    status="completed",
                    downloaded_path=downloaded_path,
                    upload=import_result,
                )
                attachment_results.append(
                    AttachmentScanResult(
                        message_id=message["id"],
                        attachment_id=attachment["id"],
                        attachment_name=attachment_name,
                        status="completed",
                        downloaded_path=str(downloaded_path),
                        upload=import_result,
                    )
                )

            except Exception as exc:
                failed += 1
                _update_email_import(
                    email_import.id,
                    status="failed",
                    error_message=str(exc),
                )
                attachment_results.append(
                    AttachmentScanResult(
                        message_id=message["id"],
                        attachment_id=attachment["id"],
                        attachment_name=attachment_name,
                        status="failed",
                        error_message=str(exc),
                    )
                )

    return OutlookScanResult(
        messages_scanned=len(messages),
        attachments_matched=matched,
        attachments_downloaded=downloaded,
        attachments_processed=processed,
        attachments_skipped=skipped,
        attachments_failed=failed,
        attachment_results=attachment_results,
    )
