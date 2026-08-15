from types import SimpleNamespace

from app.services import outlook_watcher


def test_safe_attachment_filename_removes_windows_path_characters():
    filename = outlook_watcher._safe_attachment_filename(
        r"reports\AP BTS: Weekly/Report?.xlsx"
    )

    assert filename == "reports_AP BTS_ Weekly_Report_.xlsx"


def test_ensure_uploads_dir_uses_configured_download_dir(tmp_path, monkeypatch):
    download_dir = tmp_path / "outlook" / "downloads"

    monkeypatch.setattr(
        outlook_watcher,
        "get_settings",
        lambda: SimpleNamespace(outlook_download_dir=download_dir),
    )

    assert outlook_watcher.ensure_uploads_dir() == download_dir.resolve()
    assert download_dir.is_dir()
