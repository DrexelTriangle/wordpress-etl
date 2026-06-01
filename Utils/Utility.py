from pathlib import Path
from Utils.Constants import *
import zipfile
import shutil
import re
import html

# Precompiled regex patterns to avoid recompilation overhead on hot paths.
_AMP_PATTERN = re.compile("&amp;")
_DOT_PATTERN = re.compile("\\.(?=\\w\\w)")
_AUTHOR_CLEAN_PATTERN = re.compile("^by-|^By-|^By |^by |[^\\w ^'^\\.^-]|_|\\d")
_AUTHOR_SPLIT_PATTERN = re.compile(r",|&|&amp;|\band\b")
_SIMILARITY_PATTERN = re.compile("[^\\w]| |\\d|_")
_FIGURE_PATTERN = re.compile(r"<figure\b[^>]*>.*?</figure>", re.IGNORECASE | re.DOTALL)
_IMG_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")

class Utility:
  def _obj_data(item):
    return item.data if hasattr(item, "data") else item

  def canonicalize_slug(value):
    if value is None:
      return ""
    return _SLUG_PATTERN.sub("-", str(value).strip().lower()).strip("-")

  def dedupe_slug(used, base, fallback_prefix, item_id):
    candidate_base = base if base else f"{fallback_prefix}-{item_id}"
    candidate = candidate_base
    if candidate in used:
      candidate = f"{candidate_base}-{item_id}"
    counter = 1
    while candidate in used:
      candidate = f"{candidate_base}-{counter}"
      counter += 1
    used.add(candidate)
    return candidate

  def canonicalizeAuthorLogins(authors):
    used = set()
    sorted_authors = sorted(authors, key=lambda a: (Utility._obj_data(a).get("id") is None, Utility._obj_data(a).get("id")))
    for author in sorted_authors:
      data = Utility._obj_data(author)
      author_id = data.get("id")
      base = Utility.canonicalize_slug(data.get("login")) or Utility.canonicalize_slug(data.get("display_name"))
      data["login"] = Utility.dedupe_slug(used, base, "author", author_id)

  def canonicalizeArticleSlugs(articles):
    used = set()
    sorted_articles = sorted(articles, key=lambda a: (Utility._obj_data(a).get("id") is None, Utility._obj_data(a).get("id")))
    for article in sorted_articles:
      data = Utility._obj_data(article)
      article_id = data.get("id")
      base = Utility.canonicalize_slug(data.get("slug")) or Utility.canonicalize_slug(data.get("title"))
      data["slug"] = Utility.dedupe_slug(used, base, "article", article_id)

  def cleanDocument(document: str, type: str):
    def uppercaseMatch(match):
      return match.group(0).upper()

    match type:
      case "author_single":
        document = document.split("@")
        document = _AMP_PATTERN.sub("&", document[0])
        document = _DOT_PATTERN.sub(" ", document)
        document = _AUTHOR_CLEAN_PATTERN.sub("", document).strip()
        document = re.sub("^\\w| \\w", uppercaseMatch, document)
        return document
      case "author_multiple":
        documents = _AUTHOR_SPLIT_PATTERN.split(document)
        return [_AUTHOR_CLEAN_PATTERN.sub("", doc).strip() for doc in documents]
      case "similarity":
        return _SIMILARITY_PATTERN.sub("", document).lower()
      case "article":
        return document
    return document

  def unzip(zipPath):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zipPath, 'r') as zip_ref:
      zip_ref.extractall(DATA_DIR)


  def _delete_dir(dir):
    path = Path(dir)
    if not path.exists():
      return
    if path.is_dir():
      shutil.rmtree(path, ignore_errors=True)
      return
    path.unlink(missing_ok=True)

  
  def _html_text_norm(text):
    result = ''
    
    if (text is None):
      return None 
    result = text.replace('&amp;', '&')
    result = result.replace('&nbsp;', ' ')
    return result

  def _build_excerpt(text, max_words=100):
    if text is None:
      return ""

    text_without_media = _FIGURE_PATTERN.sub(" ", str(text))
    text_without_media = _IMG_PATTERN.sub(" ", text_without_media)

    plain = html.unescape(text_without_media)
    plain = _TAG_PATTERN.sub(" ", plain)
    plain = _WHITESPACE_PATTERN.sub(" ", plain).strip()

    if not plain:
      return ""

    words = plain.split(" ")
    if len(words) <= max_words:
      return plain
    return " ".join(words[:max_words])

