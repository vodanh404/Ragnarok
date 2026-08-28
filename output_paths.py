"""Centralized output folders for Ragnarok Control Center."""
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = APP_ROOT / "output"

CATEGORIES = {
    "camera": "camera",
    "qr": "qr",
    "barcode": "barcode",
    "screenshots": "screenshots",
    "audio": "audio",
    "audiobook": "audiobook",
    "recordings": "recordings",
    "downloads": "downloads",
    "pdf": "pdf",
}


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in CATEGORIES.values():
        (OUTPUT_DIR / name).mkdir(parents=True, exist_ok=True)


def output_dir(category: str) -> Path:
    ensure_output_dirs()
    folder = CATEGORIES.get(category, category)
    path = OUTPUT_DIR / folder
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_path(category: str, filename: str, default_name: str = "output") -> Path:
    """Return a path strictly inside output/<category>.

    User-supplied absolute paths and ../ traversal are intentionally discarded;
    only the filename portion is accepted so every generated artifact stays in output/.
    """
    name = str(filename or default_name).strip().replace("\x00", "")
    # Normalize both separators so path traversal is blocked consistently on
    # Windows and POSIX, even when a Windows-style path is supplied on POSIX.
    name = name.replace("\\", "/")
    name = Path(name).name
    if not name or name in {".", ".."}:
        name = default_name
    return output_dir(category) / name
