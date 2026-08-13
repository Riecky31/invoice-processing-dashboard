from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select

from app.config import get_settings
from app.db.database import SessionLocal, create_tables
from app.db.models import EmailAttachmentImport, Upload
from app.email.outlook import (
    OutlookConfigurationError,
    OutlookGraphError,
    scan_outlook_inbox,
)
from app.services.scheduler import scheduler_status, start_scheduler, stop_scheduler


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Invoice Processing Dashboard",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Invoice Processing Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --border: #d8dde6;
      --text: #17202a;
      --muted: #5f6b7a;
      --accent: #1f6feb;
      --accent-hover: #1a5dc5;
      --danger: #b42318;
      --ok: #067647;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 22px;
    }

    h1 {
      margin: 0;
      font-size: clamp(24px, 3vw, 34px);
      font-weight: 700;
      letter-spacing: 0;
    }

    .toolbar {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    button {
      min-height: 40px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      padding: 0 14px;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
      white-space: nowrap;
    }

    button:hover {
      background: var(--accent-hover);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.72;
    }

    .status-line {
      min-height: 24px;
      color: var(--muted);
      font-size: 14px;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 22px;
    }

    .metric,
    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
    }

    .metric {
      min-height: 86px;
      padding: 14px;
    }

    .metric-label {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }

    .metric-value {
      font-size: 26px;
      font-weight: 750;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }

    .panel {
      overflow: hidden;
    }

    .panel h2 {
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 16px;
      letter-spacing: 0;
    }

    .table-wrap {
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
      table-layout: fixed;
    }

    th,
    td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
      font-size: 14px;
      overflow-wrap: anywhere;
    }

    th {
      color: var(--muted);
      font-weight: 650;
      background: #fbfcfe;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 0 9px;
      font-size: 12px;
      font-weight: 700;
      background: #edf2ff;
      color: #1d4ed8;
    }

    .pill.completed {
      background: #ecfdf3;
      color: var(--ok);
    }

    .pill.failed {
      background: #fef3f2;
      color: var(--danger);
    }

    .pill.processing {
      background: #fffaeb;
      color: #b54708;
    }

    @media (max-width: 760px) {
      main {
        width: min(100vw - 24px, 1180px);
        padding-top: 18px;
      }

      header {
        align-items: flex-start;
        flex-direction: column;
      }

      .toolbar {
        width: 100%;
      }

      button {
        width: 100%;
      }

      .metrics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Invoice Processing Dashboard</h1>
        <div class="status-line" id="schedulerStatus"></div>
      </div>
      <div class="toolbar">
        <button id="scanButton" type="button">Create Email Search</button>
      </div>
    </header>

    <section class="metrics" aria-label="Import metrics">
      <div class="metric">
        <div class="metric-label">Uploads</div>
        <div class="metric-value" id="uploadsCount">0</div>
      </div>
      <div class="metric">
        <div class="metric-label">Email imports</div>
        <div class="metric-value" id="emailImportsCount">0</div>
      </div>
      <div class="metric">
        <div class="metric-label">Rows inserted</div>
        <div class="metric-value" id="rowsInserted">0</div>
      </div>
      <div class="metric">
        <div class="metric-label">Duplicates</div>
        <div class="metric-value" id="duplicatesFound">0</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Recent Email Imports</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Attachment</th>
                <th>Status</th>
                <th>Sender</th>
                <th>Received</th>
                <th>Upload</th>
              </tr>
            </thead>
            <tbody id="emailImportsBody"></tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <h2>Recent Uploads</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Status</th>
                <th>Rows</th>
                <th>Inserted</th>
                <th>Duplicates</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody id="uploadsBody"></tbody>
          </table>
        </div>
      </div>
    </section>
  </main>

  <script>
    const scanButton = document.getElementById("scanButton");
    const schedulerStatus = document.getElementById("schedulerStatus");
    const uploadsBody = document.getElementById("uploadsBody");
    const emailImportsBody = document.getElementById("emailImportsBody");

    function formatDate(value) {
      if (!value) return "";
      return new Date(value).toLocaleString();
    }

    function statusPill(status) {
      const safeStatus = status || "unknown";
      return `<span class="pill ${safeStatus}">${safeStatus}</span>`;
    }

    function emptyRow(columns) {
      return `<tr><td colspan="${columns}">No records yet.</td></tr>`;
    }

    async function loadDashboard() {
      const response = await fetch("/api/dashboard");
      const data = await response.json();

      document.getElementById("uploadsCount").textContent = data.uploads.length;
      document.getElementById("emailImportsCount").textContent = data.email_imports.length;
      document.getElementById("rowsInserted").textContent = data.metrics.rows_inserted;
      document.getElementById("duplicatesFound").textContent = data.metrics.duplicates_found;

      const nextRun = data.scheduler.next_run_time
        ? formatDate(data.scheduler.next_run_time)
        : "not scheduled";
      schedulerStatus.textContent = `Wednesday 10:00 scan: ${nextRun}`;

      uploadsBody.innerHTML = data.uploads.length
        ? data.uploads.map((upload) => `
          <tr>
            <td>${upload.filename}</td>
            <td>${statusPill(upload.status)}</td>
            <td>${upload.rows_found}</td>
            <td>${upload.rows_inserted}</td>
            <td>${upload.duplicates_found}</td>
            <td>${formatDate(upload.uploaded_at)}</td>
          </tr>
        `).join("")
        : emptyRow(6);

      emailImportsBody.innerHTML = data.email_imports.length
        ? data.email_imports.map((emailImport) => `
          <tr>
            <td>${emailImport.attachment_name}</td>
            <td>${statusPill(emailImport.status)}</td>
            <td>${emailImport.sender || ""}</td>
            <td>${formatDate(emailImport.received_at)}</td>
            <td>${emailImport.upload_id || ""}</td>
          </tr>
        `).join("")
        : emptyRow(5);
    }

    scanButton.addEventListener("click", async () => {
      scanButton.disabled = true;
      scanButton.textContent = "Searching...";

      try {
        const response = await fetch("/api/outlook/scan", { method: "POST" });
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Outlook search failed.");
        }

        schedulerStatus.textContent =
          `Found ${data.attachments_matched}, processed ${data.attachments_processed}, skipped ${data.attachments_skipped}.`;
        await loadDashboard();
      } catch (error) {
        schedulerStatus.textContent = error.message;
      } finally {
        scanButton.disabled = false;
        scanButton.textContent = "Create Email Search";
      }
    });

    loadDashboard();
  </script>
</body>
</html>
"""


@app.get("/api/dashboard")
def dashboard_data() -> dict[str, Any]:
    with SessionLocal() as session:
        uploads = session.scalars(
            select(Upload)
            .order_by(desc(Upload.uploaded_at))
            .limit(20)
        ).all()
        email_imports = session.scalars(
            select(EmailAttachmentImport)
            .order_by(desc(EmailAttachmentImport.created_at))
            .limit(20)
        ).all()

    return {
        "scheduler": scheduler_status(),
        "metrics": {
            "rows_inserted": sum(upload.rows_inserted for upload in uploads),
            "duplicates_found": sum(upload.duplicates_found for upload in uploads),
        },
        "uploads": [
            {
                "id": upload.id,
                "filename": upload.filename,
                "uploaded_at": _iso(upload.uploaded_at),
                "rows_found": upload.rows_found,
                "rows_inserted": upload.rows_inserted,
                "duplicates_found": upload.duplicates_found,
                "status": upload.status,
            }
            for upload in uploads
        ],
        "email_imports": [
            {
                "id": email_import.id,
                "attachment_name": email_import.attachment_name,
                "subject": email_import.subject,
                "sender": email_import.sender,
                "received_at": _iso(email_import.received_at),
                "downloaded_path": email_import.downloaded_path,
                "upload_id": email_import.upload_id,
                "status": email_import.status,
                "error_message": email_import.error_message,
            }
            for email_import in email_imports
        ],
        "settings": {
            "subject_reference": get_settings().outlook_subject_reference,
            "scan_limit": get_settings().outlook_scan_limit,
            "scan_timezone": get_settings().outlook_scan_timezone,
        },
    }


@app.post("/api/outlook/scan")
def trigger_outlook_scan() -> dict[str, Any]:
    try:
        return scan_outlook_inbox().to_dict()
    except OutlookConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OutlookGraphError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
