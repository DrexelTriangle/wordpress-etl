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
from functools import lru_cache

from Utils.SiteProfile import legacy_media_hosts

# Legacy default: bare /wp-content/ paths 404 on the origin, so uploads are
# served through the site's /proxy/ handler. Overridden by MEDIA_BASE_URL.
_DEFAULT_MEDIA_BASE_URL = "https://www.thetriangle.org/proxy"


def media_base_url() -> str:
    value = os.getenv("MEDIA_BASE_URL", "").strip().rstrip("/")
    return value or _DEFAULT_MEDIA_BASE_URL


# Which domains count as "ours" is a per-run setting -- see Utils.SiteProfile.
# A host is only listed there if its uploads are actually present in the media
# tree this run writes towards.
#
# NOTE: therectangle.org is in the default list because 2011-era Triangle
# articles link to new.therectangle.org and those files were folded into the
# Triangle media tree. That is a statement about old Triangle content, NOT about
# the live Rectangle site, which serves its own uploads from its own VM. A run
# extracting the Rectangle itself must drop that host from LEGACY_MEDIA_HOSTS,
# or its working image URLs get rewritten onto a base that has never held them.


def _host_upload_pattern(hosts: tuple[str, ...]):
    """Any of `hosts` (scheme-full, protocol-relative, or scheme-less) serving a
    wp-content upload, with or without the /proxy/ segment. group(1) is the
    canonical "wp-content/uploads/..." suffix. Stops at whitespace or HTML
    attribute/URL delimiters so it is safe to run over raw body HTML.
    """
    alternation = r'|'.join(host.replace('.', r'\.') for host in hosts)
    return re.compile(
        r'(?i)(?:(?:https?:)?//(?:[a-z0-9-]+\.)*(?:' + alternation + r')/'
        r'|(?:[a-z0-9-]+\.)*(?:' + alternation + r')/)'
        r'(?:proxy/)?'
        r'(wp-content/uploads/[^\s"\'<>)]+)'
    )


@lru_cache(maxsize=8)
def _host_upload_pattern_cached(hosts: tuple[str, ...]):
    return _host_upload_pattern(hosts)

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
    hosts = legacy_media_hosts()
    is_absolute = (
        lowered.startswith(("http://", "https://"))
        or trimmed.startswith("//")
        or any(f"{host}/" in lowered.split("/")[0] + "/" for host in hosts)
    )
    # Absolute URL pointing at a different host — leave it alone. Third-party
    # sites also serve /wp-content/uploads/ paths (they run WordPress too), so
    # matching on the path alone would corrupt genuine external links. With an
    # empty host list every absolute URL takes this branch, which is the point:
    # a site already serving its uploads at their final URL rewrites nothing.
    if is_absolute and not any(host in lowered for host in hosts):
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
    rewritten = html
    hosts = legacy_media_hosts()
    if hosts:
        pattern = _host_upload_pattern_cached(hosts)
        rewritten = pattern.sub(lambda m: f"{base}/{m.group(1)}", rewritten)
    return _RELATIVE_UPLOAD_IN_HTML.sub(lambda m: f"{m.group(1)}{base}/{m.group(2)}", rewritten)
