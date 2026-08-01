"""Tests for the author-conflict cache lookup. Run from the repo root:

    .venv/bin/python -m unittest tests.test_conflict_cache
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Sanitizer.Policy import Policy
from Translator.Author import Author


def author(id, display_name, login=None):
    return Author(id, display_name, None, None, None, login)


def policy_with(conflicts):
    policy = Policy(
        specialEdits={},
        specialFlags={},
        banList=[],
        data=[],
        isAuthor=True,
    )
    policy.conflicts = conflicts
    return policy


# One previously answered conflict: two records for the same person, resolved
# to "Mary Elizabeth Hoffman". Ids are the ones from the export it was answered
# against.
CACHED = [
    [
        {"id": 338, "display_name": "Mary Elizabeth Hoffman", "first_name": None,
         "last_name": None, "email": None, "login": "mhoffman"},
        {"id": 338, "display_name": "Mary Elizabeth Hoffman", "first_name": None,
         "last_name": None, "email": None, "login": "mhoffman"},
    ],
    [
        {"id": 359, "display_name": "Elizabeth Hoffman", "first_name": None,
         "last_name": None, "email": None, "login": "ehoffman"},
        {"id": 338, "display_name": "Mary Elizabeth Hoffman", "first_name": None,
         "last_name": None, "email": None, "login": "mhoffman"},
    ],
]


class ResolveFromConflicts(unittest.TestCase):
    def test_matches_by_id(self):
        policy = policy_with(CACHED)
        resolved = policy._resolveFromConflicts(
            author(338, "Mary Elizabeth Hoffman"),
            author(359, "Elizabeth Hoffman"),
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.data["display_name"], "Mary Elizabeth Hoffman")

    def test_matches_after_wordpress_renumbers_ids(self):
        # The regression: a fresh export renumbered these people (338 -> 343,
        # 359 -> 363). Matching on the id alone re-raised a conflict that was
        # already answered, which aborts a --headless run.
        policy = policy_with(CACHED)
        resolved = policy._resolveFromConflicts(
            author(343, "Mary Elizabeth Hoffman"),
            author(363, "Elizabeth Hoffman"),
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.data["display_name"], "Mary Elizabeth Hoffman")

    def test_name_match_ignores_case_and_punctuation(self):
        policy = policy_with(CACHED)
        resolved = policy._resolveFromConflicts(
            author(900, "mary-elizabeth hoffman"),
            author(901, "Someone Else Entirely"),
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.data["display_name"], "Mary Elizabeth Hoffman")

    def test_name_match_uses_the_current_export_id_not_the_cached_one(self):
        # The cached canonical carries id 338 from the export it was answered
        # against. Returning that stale id makes both sides of the dispute
        # collapse onto it, so the authors INSERT emits two rows with the same
        # primary key and the entire load fails.
        policy = policy_with(CACHED)
        resolved = policy._resolveFromConflicts(
            author(343, "Mary Elizabeth Hoffman"),
            author(363, "Elizabeth Hoffman"),
        )
        self.assertEqual(resolved.data["id"], 343)
        self.assertEqual(resolved.data["display_name"], "Mary Elizabeth Hoffman")

    def test_id_match_keeps_the_cached_id(self):
        policy = policy_with(CACHED)
        resolved = policy._resolveFromConflicts(
            author(338, "Mary Elizabeth Hoffman"),
            author(359, "Elizabeth Hoffman"),
        )
        self.assertEqual(resolved.data["id"], 338)

    def test_two_disputes_for_one_person_do_not_collide(self):
        # Both sides resolving through the cache must not yield the same id
        # twice, which is what produced "Duplicate entry '338' for key PRIMARY".
        policy = policy_with(CACHED)
        first = policy._resolveFromConflicts(
            author(343, "Mary Elizabeth Hoffman"), author(363, "Elizabeth Hoffman")
        )
        second = policy._resolveFromConflicts(
            author(343, "Mary Elizabeth Hoffman"), author(999, "Someone Else")
        )
        self.assertEqual(first.data["id"], 343)
        self.assertEqual(second.data["id"], 343)
        self.assertNotIn(338, {first.data["id"], second.data["id"]})

    def test_unrelated_people_are_not_matched(self):
        policy = policy_with(CACHED)
        self.assertIsNone(
            policy._resolveFromConflicts(
                author(700, "Roxana Shojaian"),
                author(701, "Roxana Shaojaian"),
            )
        )

    def test_missing_display_name_does_not_match_everything(self):
        # A None name normalizes to None; two unnamed records must not be
        # treated as the same person.
        policy = policy_with([
            [
                {"id": 1, "display_name": None, "first_name": None,
                 "last_name": None, "email": None, "login": None},
                {"id": 1, "display_name": None, "first_name": None,
                 "last_name": None, "email": None, "login": None},
            ],
        ])
        self.assertIsNone(
            policy._resolveFromConflicts(author(50, None), author(51, None))
        )


if __name__ == "__main__":
    unittest.main()
