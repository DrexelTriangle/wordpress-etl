# Constants
from pathlib import Path

DATA_DIR = Path("Data")
ZIP_FILE = DATA_DIR / "wp-export.zip"
EXPORT_DIR = DATA_DIR / "wp-export"
POSTS_FILE = EXPORT_DIR / "wp-posts.xml"
GUEST_AUTH_FILE = EXPORT_DIR / "wp-guestAuths.xml"
UNZIPPED_FILES = [POSTS_FILE, GUEST_AUTH_FILE]

# WordPress stores a post's featured image as this postmeta key, whose value is
# the post id of the attachment <item> holding the actual file URL.
THUMBNAIL_META_KEY = "_thumbnail_id"
