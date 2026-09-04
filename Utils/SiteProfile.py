"""Per-source-site knobs for the extraction run.

The pipeline was written against exactly one WordPress -- thetriangle.org -- and
several of its rules are facts about *that* site rather than about WordPress:
which domains are dead, how short a body can be before it is junk, and where the
id space starts. Pointing the pipeline at a second install (therectangle.org,
which is a live sibling publication on the same VM, not a dead predecessor)
means those facts have to become settings.

Every value here defaults to the historical Triangle behaviour, so an unset
environment reproduces the previous run byte for byte. A second site is
configured by exporting the vars below -- see `profiles/` for ready-made sets.
"""
import os


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped or default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(
            f"{name} must be an integer, got {raw!r}"
        ) from None


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be a boolean, got {raw!r}")


# Domains whose `wp-content/uploads/...` references get pulled onto the media
# base. A host belongs here only if its files are actually present in the media
# tree the run is writing towards -- listing a live foreign domain rewrites
# working image URLs into 404s.
DEFAULT_LEGACY_MEDIA_HOSTS = ("thetriangle.org", "therectangle.org")


def legacy_media_hosts() -> tuple[str, ...]:
    raw = os.getenv("LEGACY_MEDIA_HOSTS")
    if raw is None:
        return DEFAULT_LEGACY_MEDIA_HOSTS
    hosts = tuple(h.strip().lower() for h in raw.split(",") if h.strip())
    # An explicit empty list is meaningful: "rewrite nothing by host, only
    # relative paths". It is how a site whose uploads already live at their
    # final URL opts out.
    return hosts


# Bodies shorter than this are treated as extraction noise rather than articles.
DEFAULT_MIN_BODY_LENGTH = 100


def min_body_length() -> int:
    return _env_int("MIN_BODY_LENGTH", DEFAULT_MIN_BODY_LENGTH)


def keep_short_posts_with_image() -> bool:
    """Exempt a too-short post from the length floor when it carries a featured
    image. On a humour site the shortest posts are the image-only visual gags --
    the body is empty because the picture *is* the article.
    """
    return _env_bool("KEEP_SHORT_POSTS_WITH_IMAGE", False)


def id_offset() -> int:
    """Starting point for the generated id sequences (articles, authors, guest
    authors). Ids are a per-run counter, not the WordPress post id, so a second
    site loaded into the same CMS tables would restart at 1 and collide with the
    first. Offset the second run past the first one's high-water mark.
    """
    return _env_int("ID_OFFSET", 0)


def category_term_source() -> str:
    """Which half of a WXR `<category>` term is recorded: its display `text`
    ("Farts & Enter-pain-ment") or its `nicename` slug ("farts-and-
    entertainment").

    Display text is the historical behaviour and matches how the CMS seeds its
    section names. Slugs are the stable half on a site that rewrites its section
    names for a joke every year, where text-matching silently zeroes out after
    each rename.
    """
    value = _env_str("CATEGORY_TERM_SOURCE", "text").lower()
    if value not in ("text", "nicename"):
        raise ValueError(
            f"CATEGORY_TERM_SOURCE must be 'text' or 'nicename', got {value!r}"
        )
    return value


def describe() -> str:
    """One-line summary of the resolved profile, for the run log. Also the
    validation point: every getter runs here, so a typo'd variable fails at
    startup rather than a thousand articles into the sanitizer.
    """
    hosts = ",".join(legacy_media_hosts()) or "(none)"
    return (
        f"site profile: legacy_media_hosts={hosts} "
        f"min_body_length={min_body_length()} "
        f"keep_short_posts_with_image={keep_short_posts_with_image()} "
        f"id_offset={id_offset()} "
        f"category_term_source={category_term_source()}"
    )
