# Constants
from pathlib import Path

DATA_DIR = Path("Data")
ZIP_FILE = DATA_DIR / "wp-export.zip"
EXPORT_DIR = DATA_DIR / "wp-export"
POSTS_FILE = EXPORT_DIR / "wp-posts[09-25-2025].xml"
GUEST_AUTH_FILE = EXPORT_DIR / "wp-guestAuths[09-25-2025].xml"
UNZIPPED_FILES = [POSTS_FILE, GUEST_AUTH_FILE]
