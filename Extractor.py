import zipfile
from contextlib import contextmanager

from lxml import etree  # type: ignore[attr-defined]
from Utils.Utility import Utility as U
from Utils.Constants import EXPORT_DIR

# Sentinel for "key absent" so dict values of None are handled correctly.
_MISSING = object()

_POST_ITEM_KEYS = frozenset((
  "content:encoded",
  "wp:comment_status",
  "description",
  "wp:post_name",
  "wp:post_modified_gmt",
  "wp:post_date_gmt",
  "category",
  "wp:postmeta",
  "title",
))
_GUEST_AUTHOR_ITEM_KEYS = frozenset(("wp:postmeta",))
_AUTHOR_KEYS = frozenset((
  "wp:author_display_name",
  "wp:author_first_name",
  "wp:author_last_name",
  "wp:author_email",
  "wp:author_login",
))


class Extractor:
  def __init__(self, posts, guestAuths):
    self.postsFile = posts
    self.guestAuthsFile = guestAuths
    self.data = {
      'auth': None,
      'guestAuth': None,
      'art': None
    }

  # GETTERS/SETTERS
  def getData(self, on_progress=None):
    self._xml2Dict(self.postsFile, self.guestAuthsFile, on_progress)
    U._delete_dir(EXPORT_DIR)
    return self.data

  def _setData(self, key, value):
    self.data[key] = value

  # METHODS
  def _keyFor(self, elem):
    # Reproduce xmltodict's 'prefix:local' element keys (e.g. 'content:encoded').
    # The same handful of tags repeat across every item, so memoize per parse.
    tag = elem.tag
    key = self._keyCache.get(tag)
    if key is None:
      local = tag[tag.rfind('}') + 1:] if '}' in tag else tag
      prefix = elem.prefix
      key = (prefix + ':' + local) if prefix else local
      self._keyCache[tag] = key
    return key

  def _elemToObj(self, elem):
    """Convert an lxml element subtree into an xmltodict-compatible value.

    Conventions matched: attributes -> '@name', mixed/element text -> '#text',
    repeated child tags collapse into a list, empty elements -> None.
    """
    attrib = elem.attrib
    if attrib:
      result = {}
      cache = self._attrCache
      for name, value in attrib.items():
        akey = cache.get(name)
        if akey is None:
          akey = '@' + (name[name.rfind('}') + 1:] if '}' in name else name)
          cache[name] = akey
        result[akey] = value
    else:
      result = None

    if len(elem) == 0:
      text = elem.text
      text = text.strip() if text else ""
      if result is not None:
        if text:
          result["#text"] = text
        return result
      return text or None

    if result is None:
      result = {}
    for child in elem:
      key = self._keyFor(child)
      value = self._elemToObj(child)
      existing = result.get(key, _MISSING)
      if existing is _MISSING:
        result[key] = value
      elif type(existing) is list:
        existing.append(value)
      else:
        result[key] = [existing, value]

    text = elem.text
    if text and text.strip():
      result["#text"] = text.strip()
    return result

  def _elemToSelectedObj(self, elem, keys):
    """Convert only selected direct children, preserving xmltodict shapes."""
    result = {}
    for child in elem:
      key = self._keyFor(child)
      if key not in keys:
        continue

      value = self._elemToObj(child)
      existing = result.get(key, _MISSING)
      if existing is _MISSING:
        result[key] = value
      elif type(existing) is list:
        existing.append(value)
      else:
        result[key] = [existing, value]
    return result

  @staticmethod
  @contextmanager
  def _openXml(source):
    # lxml rejects content before the XML declaration; skip any leading
    # whitespace/BOM by seeking to the first '<' (mirrors the old .lstrip()).
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

  def _parse(self, path, items, authors=None, itemKeys=_POST_ITEM_KEYS):
    """Stream `path` with iterparse, converting `item`/`wp:author` subtrees.

    iterparse is filtered to just those tags so we don't pay per-element
    dispatch on the whole document. Processed subtrees and their preceding
    siblings are freed as we go so the document is never fully held in memory.
    """
    self._keyCache = {}
    self._attrCache = {}
    tags = ("item",) if authors is None else ("item", "{*}author")
    with self._openXml(path) as handle:
      context = etree.iterparse(handle, events=("end",), tag=tags, recover=True)
      for _, elem in context:
        if elem.tag == "item":
          items.append(self._elemToSelectedObj(elem, itemKeys))
        else:
          authors.append(self._elemToSelectedObj(elem, _AUTHOR_KEYS))
        elem.clear()
        parent = elem.getparent()
        if parent is not None:
          while elem.getprevious() is not None:
            del parent[0]

  def _xml2Dict(self, posts, guestAuths, on_progress=None):
    def progress(msg):
      if on_progress:
        on_progress(msg)

    authors, articles, guestAuthors = [], [], []

    progress("parsing wp-posts.xml")
    self._parse(posts, articles, authors)
    progress("parsing wp-guestAuths.xml")
    self._parse(guestAuths, guestAuthors, itemKeys=_GUEST_AUTHOR_ITEM_KEYS)

    progress("indexing authors and articles")
    self._setData('auth', authors)
    self._setData('art', articles)
    self._setData('guestAuth', guestAuthors)
