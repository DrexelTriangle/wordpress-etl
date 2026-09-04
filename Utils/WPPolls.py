import datetime
import html


# wp-polls keeps its data in its own tables, so unlike posts, comments and
# authors there is nothing in wp-export.zip to read: the rows arrive as the two
# TSVs scripts/dump_wp_polls.sh writes into Data/.
#
# wp_pollsq holds one row per poll (question, run window, vote total) and
# wp_pollsa one row per option. Dates are Unix timestamps, so they need no
# timezone assumption -- worth stating because the site renders them in UTC
# rather than America/New_York, and reading the rendered page instead puts
# every poll four to five hours late.

# Historical polls all load closed. An 'active' poll whose start date has passed
# and which has no end date competes for the live slot, and would displace
# whatever poll the CMS is actually running.
IMPORT_STATUS = "closed"

# cms_polls.question is VARCHAR(255) and cms_poll_options.option_name
# VARCHAR(128); a longer value would be truncated by the database instead of
# reported, so it is dropped here with the row it came from.
MAX_QUESTION_LEN = 255
MAX_OPTION_LEN = 128


def _unescape(value):
  r"""Undo the layers between the stored text and the real string.

  mysql's batch output escapes backslashes, WordPress stored slash-escaped
  quotes, and entities like &amp; are kept encoded in the column -- so an
  apostrophe can arrive as \\' and an ampersand as &amp;.

  Some rows were slash-escaped more than once (a handful reach the dump as
  \\\\\\'), so one pass is not enough: strip to a fixed point. WordPress does the
  same on output, which is why the rendered page looks clean while the column
  does not. The loop only ever consumes a backslash that precedes a quote or
  another backslash, and is bounded so malformed input cannot spin.
  """
  if value is None:
    return None
  for _ in range(8):
    unescaped = value.replace("\\\\", "\\").replace("\\'", "'").replace('\\"', '"')
    if unescaped == value:
      break
    value = unescaped
  return html.unescape(value)


def _to_int(value):
  if value in (None, ""):
    return None
  try:
    return int(str(value).strip())
  except (TypeError, ValueError):
    return None


def _utc(timestamp):
  """Unix timestamp -> 'YYYY-MM-DD HH:MM:SS' UTC, or None.

  cms_polls.starts_at/ends_at are DATETIME columns holding UTC: the CMS opens
  its connection with parseTime=true and no loc, so the driver reads and writes
  them as UTC. wp-polls writes 0 for "no expiry".
  """
  if not timestamp:
    return None
  moment = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
  return moment.strftime("%Y-%m-%d %H:%M:%S")


def _read_tsv(path, fields):
  rows = []
  with open(path, encoding="utf-8") as handle:
    for line in handle:
      line = line.rstrip("\n")
      if not line:
        continue
      parts = line.split("\t", fields - 1)
      if len(parts) != fields:
        continue
      rows.append(parts)
  return rows


def load_wordpress_polls(questions_path, answers_path, id_offset=0):
  """Build poll records from the two dumped tables.

  Options keep wp_pollsa's own order rather than being sorted by vote count:
  the answer id is the order the editor wrote them in, which is what an archive
  should show. Ids are a per-run counter like every other table the pipeline
  emits, not the WordPress id.
  """
  options_by_poll = {}
  for qid, aid, votes, text in _read_tsv(answers_path, 4):
    pollID = _to_int(qid)
    name = (_unescape(text) or "").strip()
    if pollID is None or not name or len(name) > MAX_OPTION_LEN:
      continue
    options_by_poll.setdefault(pollID, []).append(
      {"answerID": _to_int(aid) or 0, "optionName": name, "voteCount": _to_int(votes) or 0}
    )

  polls = []
  pollID = id_offset
  optionID = id_offset
  for row in _read_tsv(questions_path, 6):
    wpPollID = _to_int(row[0])
    question = (_unescape(row[5]) or "").strip()
    options = options_by_poll.get(wpPollID, [])
    # A poll with no options cannot be rendered or voted on; it is a deleted or
    # half-created row, not content.
    if wpPollID is None or not question or not options:
      continue
    if len(question) > MAX_QUESTION_LEN:
      continue

    pollID += 1
    formatted = []
    for sortOrder, option in enumerate(sorted(options, key=lambda o: o["answerID"])):
      optionID += 1
      formatted.append({
        "id": optionID,
        "pollID": pollID,
        "optionName": option["optionName"],
        "voteCount": option["voteCount"],
        "sortOrder": sortOrder,
      })

    polls.append({
      "id": pollID,
      "wpPollID": wpPollID,
      "question": question,
      "status": IMPORT_STATUS,
      "startsAt": _utc(_to_int(row[1])),
      "endsAt": _utc(_to_int(row[2])),
      "options": formatted,
    })

  return polls


def poll_options(polls):
  """Flatten to the option rows, for the formatter that writes that table."""
  return [option for poll in polls for option in poll["options"]]
