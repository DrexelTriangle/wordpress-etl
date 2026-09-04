import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Formatter.PollFormatter import PollFormatter  # noqa: E402
from Formatter.PollOptionFormatter import PollOptionFormatter  # noqa: E402
from Utils.WPPolls import load_wordpress_polls, poll_options  # noqa: E402


def write_dumps(questions, answers):
  directory = Path(tempfile.mkdtemp())
  questionsPath = directory / "wp-pollsq.tsv"
  answersPath = directory / "wp-pollsa.tsv"
  questionsPath.write_text("".join("\t".join(str(f) for f in row) + "\n" for row in questions), encoding="utf-8")
  answersPath.write_text("".join("\t".join(str(f) for f in row) + "\n" for row in answers), encoding="utf-8")
  return questionsPath, answersPath


class TestLoadWordPressPolls(unittest.TestCase):
  def test_timestamps_are_read_as_utc(self):
    # 1389340800 is 2014-01-10 08:00:00 UTC. The site renders its poll dates in
    # UTC too, so anything that treats them as America/New_York lands the whole
    # archive four to five hours late.
    q, a = write_dumps(
      [(2, 1389340800, 1389945600, 56, 0, "Do you like the new website?")],
      [(2, 6, 30, "Yes."), (2, 7, 11, "No.")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertEqual(polls[0]["startsAt"], "2014-01-10 08:00:00")
    self.assertEqual(polls[0]["endsAt"], "2014-01-17 08:00:00")

  def test_zero_expiry_is_no_end_date(self):
    q, a = write_dumps(
      [(186, 1764842400, 0, 46, 1, "Where do you stream music?")],
      [(186, 700, 25, "Spotify")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertIsNone(polls[0]["endsAt"])

  def test_escaped_text_is_decoded(self):
    # An apostrophe arrives double-escaped (mysql's batch escaping over
    # WordPress's stored slashes) and an ampersand as an entity.
    q, a = write_dumps(
      [(135, 1400000000, 0, 10, 0, "It\\\\'s a question &amp; a test")],
      [(135, 400, 5, "alcohol &amp; drug abuse"), (135, 401, 5, "Ed\\\\'s Pizza")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertEqual(polls[0]["question"], "It's a question & a test")
    self.assertEqual(
      [o["optionName"] for o in polls[0]["options"]],
      ["alcohol & drug abuse", "Ed's Pizza"],
    )

  def test_repeatedly_escaped_text_is_stripped_to_a_fixed_point(self):
    # Seven Triangle polls were slash-escaped more than once and reach the dump
    # with six backslashes before the apostrophe. One pass leaves two behind,
    # which is enough to stop the row matching anything by question text.
    backslashes = "\\" * 6
    q, a = write_dumps(
      [(76, 1455264000, 0, 67, 0, f"How do you feel about Valentine{backslashes}'s Day?")],
      [(76, 600, 40, f"It{backslashes}'s fine")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertEqual(polls[0]["question"], "How do you feel about Valentine's Day?")
    self.assertEqual(polls[0]["options"][0]["optionName"], "It's fine")

  def test_options_keep_editor_order_not_vote_order(self):
    q, a = write_dumps(
      [(70, 1400000000, 0, 9, 0, "Santa?")],
      [(70, 300, 1, "Meet Santa"), (70, 301, 7, "Be Santa"), (70, 302, 1, "Get cozy")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertEqual(
      [o["optionName"] for o in polls[0]["options"]],
      ["Meet Santa", "Be Santa", "Get cozy"],
    )
    self.assertEqual([o["sortOrder"] for o in polls[0]["options"]], [0, 1, 2])

  def test_polls_without_options_are_dropped(self):
    q, a = write_dumps(
      [(31, 1400000000, 0, 0, 0, "Deleted poll"), (32, 1400000000, 0, 3, 0, "Real poll")],
      [(32, 500, 3, "Yes")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertEqual([p["wpPollID"] for p in polls], [32])

  def test_oversized_values_are_dropped_not_truncated(self):
    q, a = write_dumps(
      [(1, 1400000000, 0, 1, 0, "x" * 256), (2, 1400000000, 0, 1, 0, "fine")],
      [(1, 1, 1, "a"), (2, 2, 1, "y" * 129), (2, 3, 1, "ok")],
    )
    polls = load_wordpress_polls(q, a)
    self.assertEqual([p["wpPollID"] for p in polls], [2])
    self.assertEqual([o["optionName"] for o in polls[0]["options"]], ["ok"])

  def test_ids_are_a_run_counter_honouring_the_offset(self):
    q, a = write_dumps(
      [(2, 1400000000, 0, 1, 0, "First"), (9, 1400000000, 0, 1, 0, "Second")],
      [(2, 10, 1, "a"), (9, 11, 1, "b")],
    )
    polls = load_wordpress_polls(q, a, id_offset=100)
    self.assertEqual([p["id"] for p in polls], [101, 102])
    self.assertEqual([o["pollID"] for o in poll_options(polls)], [101, 102])
    self.assertEqual([o["id"] for o in poll_options(polls)], [101, 102])

  def test_everything_loads_closed(self):
    q, a = write_dumps(
      [(186, 1764842400, 0, 46, 1, "Live in WordPress")],
      [(186, 700, 25, "Spotify")],
    )
    self.assertEqual(load_wordpress_polls(q, a)[0]["status"], "closed")


class TestPollFormatters(unittest.TestCase):
  def setUp(self):
    q, a = write_dumps(
      [(2, 1389340800, 1389945600, 41, 0, "Do you like it?")],
      [(2, 6, 30, "Yes."), (2, 7, 11, "It's fine")],
    )
    self.polls = load_wordpress_polls(q, a)

  def test_poll_sql_creates_table_and_inserts_dates(self):
    sql = "\n".join(PollFormatter(self.polls).format())
    self.assertIn("CREATE TABLE cms_polls", sql)
    self.assertIn("`question` VARCHAR(255) NOT NULL", sql)
    self.assertIn("'2014-01-10 08:00:00'", sql)
    self.assertIn("'closed'", sql)
    # created_at/updated_at are defaulted, never written.
    self.assertIn("`created_at` TIMESTAMP", sql)
    self.assertNotIn("INSERT INTO cms_polls (`id`, `question`, `status`, `starts_at`, `ends_at`, `created_at`", sql)

  def test_option_sql_carries_vote_counts_and_escapes_quotes(self):
    sql = "\n".join(PollOptionFormatter(poll_options(self.polls)).format())
    self.assertIn("CREATE TABLE cms_poll_options", sql)
    self.assertIn("uq_cms_poll_options_poll_name", sql)
    self.assertIn("fk_cms_poll_options_poll", sql)
    self.assertIn("30", sql)
    self.assertIn("'It''s fine'", sql)

  def test_empty_input_writes_nothing(self):
    self.assertEqual(PollFormatter([]).format(), [])
    self.assertEqual(PollOptionFormatter([]).format(), [])


if __name__ == "__main__":
  unittest.main()
