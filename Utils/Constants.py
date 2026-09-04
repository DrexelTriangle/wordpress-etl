# Constants
from pathlib import Path

DATA_DIR = Path("Data")
ZIP_FILE = DATA_DIR / "wp-export.zip"
EXPORT_DIR = DATA_DIR / "wp-export"
POSTS_FILE = EXPORT_DIR / "wp-posts.xml"
GUEST_AUTH_FILE = EXPORT_DIR / "wp-guestAuths.xml"
UNZIPPED_FILES = [POSTS_FILE, GUEST_AUTH_FILE]

# wp-polls stores its data in its own tables, which the WordPress exporter does
# not touch, so the poll stage reads these dumps instead of the export. They are
# optional: scripts/dump_wp_polls.sh writes them, and without them the run just
# skips polls. See Utils/WPPolls.py.
POLLS_QUESTIONS_FILE = DATA_DIR / "wp-pollsq.tsv"
POLLS_ANSWERS_FILE = DATA_DIR / "wp-pollsa.tsv"

# WordPress stores a post's featured image as this postmeta key, whose value is
# the post id of the attachment <item> holding the actual file URL.
THUMBNAIL_META_KEY = "_thumbnail_id"

# The "field absent" placeholder the translators compare against. It is the
# string "None", not the None object: it originates in the export's own text
# and predates this constant, which is why the comparisons are `== DEFAULT_VALUE`
# rather than `is None`.
DEFAULT_VALUE = "None"
