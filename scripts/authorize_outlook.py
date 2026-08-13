from app.config import get_settings
from app.email.outlook import authorize_outlook_device_flow


if __name__ == "__main__":
    settings = get_settings()

    if settings.outlook_provider.lower() == "win32":
        print(
            "OUTLOOK_PROVIDER=win32 uses your signed-in Outlook desktop app. "
            "No Microsoft Graph authorization is required. Run "
            "`python scripts/scan_outlook.py` or use the dashboard button."
        )
    else:
        print(authorize_outlook_device_flow())
