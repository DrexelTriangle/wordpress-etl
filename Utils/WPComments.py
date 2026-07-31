import zipfile
from contextlib import contextmanager

from lxml import etree  # type: ignore[attr-defined]


_WP_NS = "http://wordpress.org/export/1.2/"
_WP_POST_ID_TAG = f"{{{_WP_NS}}}post_id"
_WP_COMMENT_TAG = f"{{{_WP_NS}}}comment"


def _tag(name):
  return f"{{{_WP_NS}}}{name}"


def _to_int(value):
  if value in (None, ""):
    return None
  try:
    return int(str(value).strip())
  except (TypeError, ValueError):
    return None


def _text(elem, tag):
  child = elem.find(tag)
  if child is None or child.text is None:
    return None
  return child.text.strip() or None


def _status(value):
  value = str(value or "").strip().lower()
  if value == "1":
    return "approved"
  if value == "0":
    return "pending"
  return value or "pending"


def _is_spam_status(value):
  return _status(value) == "spam"


def article_id_by_wp_post_id(articles):
  result = {}
  for article in articles or []:
    data = article.data if hasattr(article, "data") else article
    if not isinstance(data, dict):
      continue
    wp_post_id = _to_int(data.get("wpPostID"))
    article_id = _to_int(data.get("id"))
    if wp_post_id is not None and article_id is not None:
      result[wp_post_id] = article_id
  return result


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


def iter_wordpress_comments(posts_source, articles=None):
  article_map = article_id_by_wp_post_id(articles)

  with _open_xml(posts_source) as handle:
    context = etree.iterparse(handle, events=("end",), tag=("item",), recover=True)
    for _, item in context:
      wp_post_id = _to_int(_text(item, _WP_POST_ID_TAG))
      if wp_post_id is None:
        item.clear()
        continue

      comments = item.findall(_WP_COMMENT_TAG)
      if comments:
        article_id = article_map.get(wp_post_id)
        for comment in comments:
          if _is_spam_status(_text(comment, _tag("comment_approved"))):
            continue
          yield {
            "id": _to_int(_text(comment, _tag("comment_id"))),
            "articleID": article_id,
            "wpPostID": wp_post_id,
            "parentID": _to_int(_text(comment, _tag("comment_parent"))),
            "authorName": _text(comment, _tag("comment_author")),
            "authorEmail": _text(comment, _tag("comment_author_email")),
            "authorURL": _text(comment, _tag("comment_author_url")),
            "authorIP": _text(comment, _tag("comment_author_IP")),
            "authorUserID": _to_int(_text(comment, _tag("comment_user_id"))),
            "content": _text(comment, _tag("comment_content")),
            "createdAt": _text(comment, _tag("comment_date")),
            "createdAtGMT": _text(comment, _tag("comment_date_gmt")),
            "status": _status(_text(comment, _tag("comment_approved"))),
            "type": _text(comment, _tag("comment_type")),
          }

      item.clear()
      parent = item.getparent()
      if parent is not None:
        while item.getprevious() is not None:
          del parent[0]


def load_wordpress_comments(posts_source, articles=None):
  return list(iter_wordpress_comments(posts_source, articles))
