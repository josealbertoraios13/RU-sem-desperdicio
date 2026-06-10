import os
import tempfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

# Persistent local storage remains the default for backward compatibility.
UPLOADS_MENU_DIR = Path(
    os.getenv("UPLOADS_MENU_DIR", PROJECT_ROOT / "volumes" / "uploads" / "menu")
)

# Fallback used only when the configured local upload directory is not writable.
WRITABLE_UPLOADS_MENU_DIR = Path(tempfile.gettempdir()) / "smartru" / "uploads" / "menu"

SCHEMA_SQL = PACKAGE_ROOT / "repository" / "schema.sql"
