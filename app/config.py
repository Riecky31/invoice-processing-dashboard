import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def _resolve_path(value: str, default: str) -> Path:
    path = Path(value or default)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    outlook_provider: str
    outlook_tenant_id: str | None
    outlook_client_id: str | None
    outlook_client_secret: str | None
    outlook_user_id: str | None
    outlook_win32_folder_path: str | None
    outlook_subject_reference: str
    outlook_mail_folder: str
    outlook_scan_limit: int
    outlook_scan_timezone: str
    outlook_scan_enabled: bool
    outlook_download_dir: Path
    outlook_token_cache_path: Path
    outlook_scopes: list[str]

    @property
    def outlook_authority(self) -> str:
        tenant_id = self.outlook_tenant_id or "common"
        return f"https://login.microsoftonline.com/{tenant_id}"

    @property
    def uses_app_only_outlook_auth(self) -> bool:
        return bool(
            self.outlook_tenant_id
            and self.outlook_client_id
            and self.outlook_client_secret
            and self.outlook_user_id
        )


def get_settings() -> Settings:
    scopes = [
        scope.strip()
        for scope in os.getenv("OUTLOOK_SCOPES", "Mail.Read").split(",")
        if scope.strip()
    ]

    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        outlook_provider=os.getenv("OUTLOOK_PROVIDER", "win32"),
        outlook_tenant_id=os.getenv("OUTLOOK_TENANT_ID"),
        outlook_client_id=os.getenv("OUTLOOK_CLIENT_ID"),
        outlook_client_secret=os.getenv("OUTLOOK_CLIENT_SECRET"),
        outlook_user_id=os.getenv("OUTLOOK_USER_ID"),
        outlook_win32_folder_path=os.getenv("OUTLOOK_WIN32_FOLDER_PATH"),
        outlook_subject_reference=os.getenv(
            "OUTLOOK_SUBJECT_REFERENCE",
            "AP BTS Weekly Report",
        ),
        outlook_mail_folder=os.getenv("OUTLOOK_MAIL_FOLDER", "inbox"),
        outlook_scan_limit=_env_int("OUTLOOK_SCAN_LIMIT", 250),
        outlook_scan_timezone=os.getenv(
            "OUTLOOK_SCAN_TIMEZONE",
            "Africa/Johannesburg",
        ),
        outlook_scan_enabled=_env_bool("OUTLOOK_SCAN_ENABLED", True),
        outlook_download_dir=_resolve_path(
            os.getenv("OUTLOOK_DOWNLOAD_DIR", ""),
            "data/outlook_downloads",
        ),
        outlook_token_cache_path=_resolve_path(
            os.getenv("OUTLOOK_TOKEN_CACHE_PATH", ""),
            "data/outlook/token_cache.bin",
        ),
        outlook_scopes=scopes,
    )
