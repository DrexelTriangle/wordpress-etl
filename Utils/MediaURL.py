"""Canonicalization of WordPress image URLs to the configured media base.

This is the single source of truth for how `wp-content/uploads/...` references —
both an article's featured `photo_url` and inline `<img>`/`srcset` URLs in the
body — are rewritten during ETL. The CMS deliberately stores and serves whatever
the ETL emits verbatim (no read-time rewriting), so the final, working URL must
be produced here.

Set the ``MEDIA_BASE_URL`` env var to the host that actually serves the uploads
(the Ceph-backed Nginx/CDN once the images are rsynced over). It defaults to the
legacy WordPress image proxy so freshly generated data keeps working before the
Ceph cutover.
"""
import os
import re

# Legacy default: bare /wp-content/ paths 404 on the origin, so uploads are
# served through the site's /proxy/ handler. Overridden by MEDIA_BASE_URL.
_DEFAULT_MEDIA_BASE_URL = "https://www.thetriangle.org/proxy"


def media_base_url() -> str:
    value = os.getenv("MEDIA_BASE_URL", "").strip().rstrip("/")
    return value or _DEFAULT_MEDIA_BASE_URL


# Legacy Triangle-owned domains whose uploads were migrated into the same media
# tree. therectangle.org is a defunct predecessor of thetriangle.org: 2011-era
# articles still link to new.therectangle.org, the domain no longer resolves, and
# the files live under the same wp-content/uploads/ paths as everything else. Any
# host added here must have its files present in the media tree.
_LEGACY_MEDIA_HOSTS = ("thetriangle.org", "therectangle.org")

# Any Triangle-hosted (scheme-full, protocol-relative, or scheme-less) wp-content
# upload URL, with or without the /proxy/ segment. group(1) is the canonical
# "wp-content/uploads/..." suffix. Stops at whitespace or HTML attribute/URL
# delimiters so it is safe to run over raw body HTML.
_LEGACY_HOST_ALTERNATION = r'|'.join(
    host.replace('.', r'\.') for host in _LEGACY_MEDIA_HOSTS
)
_TRIANGLE_UPLOAD_IN_HTML = re.compile(
    r'(?i)(?:(?:https?:)?//(?:[a-z0-9-]+\.)*(?:' + _LEGACY_HOST_ALTERNATION + r')/'
    r'|(?:[a-z0-9-]+\.)*(?:' + _LEGACY_HOST_ALTERNATION + r')/)'
    r'(?:proxy/)?'
    r'(wp-content/uploads/[^\s"\'<>)]+)'
)

# Relative wp-content upload references in body HTML. The prefix capture keeps us
# from rewriting external absolute URLs such as https://cdn.example/wp-content/...
_RELATIVE_UPLOAD_IN_HTML = re.compile(
    r'(?i)(^|[\s"\'(=])/?(wp-content/uploads/[^\s"\'<>)]+)'
)


def canonicalize_media_url(value, base: str | None = None):
    """Rewrite a single Triangle-hosted or relative wp-content URL onto the media
    base. Non-string values, empty strings, non-wp-content URLs, and absolute
    URLs on some other host (e.g. an already-migrated CDN) pass through
    unchanged.
    """
    if not isinstance(value, str):
        return value
    trimmed = value.strip()
    if not trimmed:
        return value

    lowered = trimmed.lower()
    is_absolute = (
        lowered.startswith(("http://", "https://"))
        or trimmed.startswith("//")
        or any(f"{host}/" in lowered.split("/")[0] + "/" for host in _LEGACY_MEDIA_HOSTS)
    )
    # Absolute URL pointing at a different host — leave it alone. Third-party
    # sites also serve /wp-content/uploads/ paths (they run WordPress too), so
    # matching on the path alone would corrupt genuine external links.
    if is_absolute and not any(host in lowered for host in _LEGACY_MEDIA_HOSTS):
        return trimmed

    idx = lowered.find("wp-content/uploads/")
    if idx < 0:
        return trimmed

    if base is None:
        base = media_base_url()
    return f"{base}/{trimmed[idx:]}"


def rewrite_media_urls_in_html(html: str, base: str | None = None) -> str:
    """Rewrite every Triangle-hosted wp-content upload URL embedded in body HTML
    (img src, srcset, anchor hrefs, etc.) onto the media base. A cheap substring
    guard skips the regex for the overwhelming majority of articles with no such
    images.
    """
    if not html or "wp-content/uploads/" not in html.lower():
        return html
    if base is None:
        base = media_base_url()
    rewritten = _TRIANGLE_UPLOAD_IN_HTML.sub(lambda m: f"{base}/{m.group(1)}", html)
    return _RELATIVE_UPLOAD_IN_HTML.sub(lambda m: f"{m.group(1)}{base}/{m.group(2)}", rewritten)
