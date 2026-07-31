import csv
import json
import re
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from lxml import etree  # type: ignore[attr-defined]

from Utils.Constants import ZIP_FILE
from Utils.Utility import Utility

_WP_NS = "http://wordpress.org/export/1.2/"
_CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
_EXCERPT_NS = "http://wordpress.org/export/1.2/excerpt/"

_WP_ATTACHMENT_URL_TAG = f"{{{_WP_NS}}}attachment_url"
_WP_META_KEY_TAG = f"{{{_WP_NS}}}meta_key"
_WP_META_VALUE_TAG = f"{{{_WP_NS}}}meta_value"
_WP_POST_ID_TAG = f"{{{_WP_NS}}}post_id"
_WP_POST_PARENT_TAG = f"{{{_WP_NS}}}post_parent"
_WP_POST_TYPE_TAG = f"{{{_WP_NS}}}post_type"
_WP_POST_NAME_TAG = f"{{{_WP_NS}}}post_name"
_WP_POST_DATE_GMT_TAG = f"{{{_WP_NS}}}post_date_gmt"
_CONTENT_ENCODED_TAG = f"{{{_CONTENT_NS}}}encoded"
_EXCERPT_ENCODED_TAG = f"{{{_EXCERPT_NS}}}encoded"

_UPLOAD_SUFFIX_RE = re.compile(r"(?i)wp-content/uploads/([^\s\"'<>)]+)")
_RELATIVE_UPLOAD_RE = re.compile(r"(?i)(^|[\s\"'(=])/?(wp-content/uploads/[^\s\"'<>)]+)")
_SERIALIZED_FILE_RE = re.compile(r's:4:"file";s:\d+:"([^"]+)"')


@dataclass(frozen=True)
class MediaAttachment:
    attachment_id: str
    parent_id: str
    title: str
    post_name: str
    attachment_url: str
    guid: str
    attached_file: str
    primary_path: str
    file_paths: tuple[str, ...]
    excerpt: str
    post_date_gmt: str


@dataclass(frozen=True)
class MediaReference:
    article_id: str
    slug: str
    source: str
    original: str
    destination_path: str


def _text(elem, tag):
    value = elem.findtext(tag)
    return value.strip() if isinstance(value, str) else ""


def _clean_upload_path(value):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value:
        return ""

    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        value = parsed.path
    else:
        value = value.split("?", 1)[0].split("#", 1)[0]

    value = unquote(value).strip().lstrip("/")
    lowered = value.lower()
    marker = "wp-content/uploads/"
    idx = lowered.find(marker)
    if idx >= 0:
        return value[idx:]

    if re.match(r"^\d{4}/\d{2}/[^/].+", value):
        return f"wp-content/uploads/{value}"
    return ""


def _source_url_for_path(attachment_url, path):
    if not attachment_url or not path:
        return attachment_url
    parsed = urlparse(attachment_url)
    if not parsed.scheme or not parsed.netloc:
        return attachment_url
    base_path = _clean_upload_path(attachment_url)
    if not base_path:
        return attachment_url
    prefix = parsed.path[: parsed.path.lower().find("wp-content/uploads/")]
    return f"{parsed.scheme}://{parsed.netloc}{prefix}{path}"


def _variant_paths(attached_file, metadata):
    paths = []
    primary = _clean_upload_path(attached_file)
    if primary:
        paths.append(primary)

    base_dir = str(Path(primary).parent) if primary else ""
    if base_dir == ".":
        base_dir = ""

    for raw_file in _SERIALIZED_FILE_RE.findall(metadata or ""):
        if "/" in raw_file:
            path = _clean_upload_path(raw_file)
        elif base_dir:
            path = f"{base_dir}/{raw_file}"
        else:
            path = _clean_upload_path(raw_file)
        if path and path not in paths:
            paths.append(path)
    return tuple(paths)


@contextmanager
def _open_xml(source):
    if isinstance(source, tuple):
        zip_ref = zipfile.ZipFile(source[0], "r")
        handle = zip_ref.open(source[1], "r")
    else:
        zip_ref = None
        handle = open(source, "rb")
    try:
        head = handle.read(4096)
        start = head.find(b"<")
        handle.seek(start if start != -1 else 0)
        yield handle
    finally:
        handle.close()
        if zip_ref is not None:
            zip_ref.close()


def _postmeta(elem):
    result = {}
    for meta in elem.findall(f"{{{_WP_NS}}}postmeta"):
        key = _text(meta, _WP_META_KEY_TAG)
        if not key:
            continue
        result[key] = _text(meta, _WP_META_VALUE_TAG)
    return result


def iter_media_attachments(posts_source):
    with _open_xml(posts_source) as handle:
        context = etree.iterparse(handle, events=("end",), tag=("item",), recover=True)
        for _, elem in context:
            if _text(elem, _WP_POST_TYPE_TAG) == "attachment":
                meta = _postmeta(elem)
                attachment_url = _text(elem, _WP_ATTACHMENT_URL_TAG)
                guid = _text(elem, "guid")
                attached_file = meta.get("_wp_attached_file", "")
                primary_path = _clean_upload_path(attached_file) or _clean_upload_path(attachment_url) or _clean_upload_path(guid)
                file_paths = _variant_paths(primary_path, meta.get("_wp_attachment_metadata", ""))
                if primary_path and primary_path not in file_paths:
                    file_paths = (primary_path, *file_paths)

                yield MediaAttachment(
                    attachment_id=_text(elem, _WP_POST_ID_TAG),
                    parent_id=_text(elem, _WP_POST_PARENT_TAG),
                    title=_text(elem, "title"),
                    post_name=_text(elem, _WP_POST_NAME_TAG),
                    attachment_url=attachment_url,
                    guid=guid,
                    attached_file=attached_file,
                    primary_path=primary_path,
                    file_paths=file_paths,
                    excerpt=_text(elem, _EXCERPT_ENCODED_TAG),
                    post_date_gmt=_text(elem, _WP_POST_DATE_GMT_TAG),
                )

            elem.clear()
            parent = elem.getparent()
            if parent is not None:
                while elem.getprevious() is not None:
                    del parent[0]


def _article_data(item):
    return item.data if hasattr(item, "data") else item


def _iter_paths_in_text(text):
    if not isinstance(text, str) or "wp-content/uploads/" not in text.lower():
        return

    seen_spans = set()
    for match in _UPLOAD_SUFFIX_RE.finditer(text):
        original = match.group(0)
        path = _clean_upload_path(original)
        if path:
            seen_spans.add(match.span())
            yield original, path

    for match in _RELATIVE_UPLOAD_RE.finditer(text):
        if match.span() in seen_spans:
            continue
        original = match.group(2)
        path = _clean_upload_path(original)
        if path:
            yield original, path


def collect_media_references(articles):
    references = []
    seen = set()
    for article in articles:
        data = _article_data(article)
        if not isinstance(data, dict):
            continue
        article_id = str(data.get("id") or "")
        slug = str(data.get("slug") or "")
        for source, value in (("text", data.get("text")), ("photo_url", data.get("photoURL") or data.get("photo_url"))):
            for original, path in _iter_paths_in_text(value) or ():
                key = (article_id, source, original, path)
                if key in seen:
                    continue
                seen.add(key)
                references.append(MediaReference(article_id, slug, source, original, path))
    return references


def reconcile_media(attachments, references):
    attachments_by_path = {}
    for attachment in attachments:
        for path in attachment.file_paths:
            attachments_by_path.setdefault(path, []).append(attachment)

    references_by_path = {}
    for reference in references:
        references_by_path.setdefault(reference.destination_path, []).append(reference)

    all_paths = sorted(set(attachments_by_path) | set(references_by_path))
    rows = []
    for path in all_paths:
        path_attachments = attachments_by_path.get(path, [])
        path_references = references_by_path.get(path, [])
        if path_attachments and path_references:
            status = "referenced_with_attachment"
        elif path_references:
            status = "referenced_missing_attachment"
        else:
            status = "inventory_only"

        rows.append({
            "destination_path": path,
            "status": status,
            "attachment_ids": ";".join(a.attachment_id for a in path_attachments if a.attachment_id),
            "parent_ids": ";".join(sorted({a.parent_id for a in path_attachments if a.parent_id})),
            "reference_count": len(path_references),
            "reference_articles": ";".join(sorted({r.article_id for r in path_references if r.article_id})[:20]),
            "reference_sources": ";".join(sorted({r.source for r in path_references})),
        })
    return rows


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_media_reports(articles, output_dir=Path("logs/media"), posts_source=None):
    posts_source = posts_source or Utility.resolveExportZipMembers(ZIP_FILE)[0]
    output_dir = Path(output_dir)
    attachments = list(iter_media_attachments(posts_source))
    references = collect_media_references(articles)
    reconciliation = reconcile_media(attachments, references)

    attachment_rows = [
        {
            "attachment_id": item.attachment_id,
            "parent_id": item.parent_id,
            "title": item.title,
            "post_name": item.post_name,
            "attachment_url": item.attachment_url,
            "guid": item.guid,
            "attached_file": item.attached_file,
            "primary_path": item.primary_path,
            "file_paths": json.dumps(item.file_paths, ensure_ascii=False),
            "excerpt": item.excerpt,
            "post_date_gmt": item.post_date_gmt,
        }
        for item in attachments
    ]
    reference_rows = [
        {
            "article_id": item.article_id,
            "slug": item.slug,
            "source": item.source,
            "original": item.original,
            "destination_path": item.destination_path,
        }
        for item in references
    ]
    copy_rows = []
    for item in attachments:
        for path in item.file_paths:
            copy_rows.append({
                "attachment_id": item.attachment_id,
                "parent_id": item.parent_id,
                "source_url": _source_url_for_path(item.attachment_url or item.guid, path),
                "destination_path": path,
            })

    _write_csv(
        output_dir / "attachments.csv",
        ["attachment_id", "parent_id", "title", "post_name", "attachment_url", "guid", "attached_file", "primary_path", "file_paths", "excerpt", "post_date_gmt"],
        attachment_rows,
    )
    _write_csv(
        output_dir / "referenced_media.csv",
        ["article_id", "slug", "source", "original", "destination_path"],
        reference_rows,
    )
    _write_csv(
        output_dir / "reconciliation.csv",
        ["destination_path", "status", "attachment_ids", "parent_ids", "reference_count", "reference_articles", "reference_sources"],
        reconciliation,
    )
    _write_csv(
        output_dir / "copy_manifest.csv",
        ["attachment_id", "parent_id", "source_url", "destination_path"],
        copy_rows,
    )

    summary = {
        "attachments": len(attachments),
        "attachment_files": len(copy_rows),
        "references": len(references),
        "unique_referenced_paths": len({item.destination_path for item in references}),
        "referenced_with_attachment": sum(1 for row in reconciliation if row["status"] == "referenced_with_attachment"),
        "referenced_missing_attachment": sum(1 for row in reconciliation if row["status"] == "referenced_missing_attachment"),
        "inventory_only": sum(1 for row in reconciliation if row["status"] == "inventory_only"),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
