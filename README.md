# Invoice Processing Dashboard

Run the dashboard:

```bash
pip install -r requirements.txt
docker compose up -d
python3 scripts/init_database.py
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Outlook setup

The default Outlook mode is `OUTLOOK_PROVIDER=win32`. It uses the Outlook desktop app on Windows through `pywin32`, so Outlook must be installed, signed in, and able to open your inbox on that machine.

You do not need to run `scripts/authorize_outlook.py` for Win32 Outlook. That script is only useful if you later switch to Microsoft Graph.

If the target inbox is not your default inbox, set `OUTLOOK_WIN32_FOLDER_PATH` in `.env`, for example `Mailbox - Finance Team/Inbox`.

The scheduled scan runs every Wednesday at 10:00 in `OUTLOOK_SCAN_TIMEZONE` and searches recent inbox messages with Excel attachments matching `AP BTS Weekly Report` in the subject or attachment filename.

The `Create Email Search` button runs the same scan immediately against existing inbox messages.
