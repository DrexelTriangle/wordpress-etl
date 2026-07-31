import unittest

from Utils.CommentSpam import classify, mark_spam, summarize


def comment(**overrides):
    base = {
        "id": 1,
        "articleID": 100,
        "authorName": "Reader",
        "authorURL": None,
        "content": "A perfectly ordinary remark about the article.",
        "status": "approved",
        "type": "comment",
    }
    base.update(overrides)
    return base


class ClassifyTest(unittest.TestCase):
    def test_genuine_comment_is_not_flagged(self):
        self.assertIsNone(classify(comment()))

    def test_legitimate_author_url_is_not_flagged(self):
        self.assertIsNone(classify(comment(authorURL="https://drexel.edu/news")))

    def test_single_link_in_body_is_not_flagged(self):
        self.assertIsNone(
            classify(comment(content="Sources here: https://thetriangle.org/news"))
        )

    def test_referral_host_is_flagged(self):
        self.assertEqual(
            classify(comment(authorURL="https://accounts.binance.com/register?ref=99")),
            "referral-host:accounts.binance.com",
        )

    def test_referral_host_matches_subdomains_and_ignores_www(self):
        self.assertEqual(
            classify(comment(authorURL="https://www.gate.io/signup")),
            "referral-host:gate.io",
        )
        self.assertEqual(
            classify(comment(authorURL="http://promo.binance.com/x")),
            "referral-host:promo.binance.com",
        )

    def test_bargain_tld_is_flagged(self):
        self.assertEqual(
            classify(comment(authorURL="https://real-estatee.shop/")),
            "spam-tld:real-estatee.shop",
        )

    def test_host_keyword_is_flagged(self):
        self.assertEqual(
            classify(comment(authorURL="https://casinotologin.com")),
            "spam-host-keyword:casinotologin.com",
        )

    def test_keyword_in_body_alone_is_not_flagged(self):
        # A real article about a casino development draws real comments.
        self.assertIsNone(
            classify(comment(content="The casino development vote is Tuesday."))
        )

    def test_spam_domain_in_the_path_is_flagged(self):
        # Host-parasite spam: the profile page is on a real site, the payload
        # domain is in the path, so netloc alone never sees it.
        self.assertEqual(
            classify(comment(authorURL="https://www.southsidesox.com/users/www.20bet.com")),
            "referral-host:20bet.com",
        )

    def test_malformed_url_does_not_hide_the_host(self):
        # urlparse reads this netloc as "https", concealing the .xyz domain.
        self.assertEqual(
            classify(comment(authorURL="http://https//fexie.xyz/top--temporary-email")),
            "spam-tld:fexie.xyz",
        )

    def test_spam_author_keyword_is_flagged(self):
        self.assertEqual(
            classify(comment(authorName="is erectile dysfunction curable")),
            "spam-author-keyword:is erectile dysfunction curable",
        )

    def test_business_commenting_under_its_own_name_is_not_flagged(self):
        self.assertIsNone(
            classify(comment(authorName="Legendary Coffee Company",
                             authorURL="http://www.thelegendarycoffee.com"))
        )

    def test_link_stuffed_body_is_flagged(self):
        self.assertEqual(
            classify(
                comment(
                    content='<a href="https://a.example/">a</a> nice <a href="https://b.example/">b</a>'
                )
            ),
            "link-stuffed-body",
        )


class MarkSpamTest(unittest.TestCase):
    def test_repeated_long_body_is_flagged_for_every_copy(self):
        body = "Thank you for your sharing. I am worried that I lack creative ideas."
        comments = [
            comment(id=1, content=body),
            comment(id=2, content=body.upper() + "  "),
            comment(id=3, content="A genuine and quite specific reaction to the piece."),
        ]

        flagged = mark_spam(comments)

        self.assertEqual({record["id"] for record in flagged}, {1, 2})
        self.assertEqual([c["status"] for c in comments], ["spam", "spam", "approved"])
        self.assertEqual(flagged[0]["reason"], "duplicate-body")

    def test_short_repeated_body_is_left_alone(self):
        # Two readers can plausibly both write this; the rule must not fire.
        comments = [comment(id=1, content="Great article!"), comment(id=2, content="Great article!")]

        self.assertEqual(mark_spam(comments), [])
        self.assertEqual([c["status"] for c in comments], ["approved", "approved"])

    def test_pending_comment_can_be_flagged_but_spam_is_left_alone(self):
        comments = [
            comment(id=1, status="pending", authorURL="https://www.gate.io/"),
            comment(id=2, status="spam", authorURL="https://www.gate.io/"),
        ]

        flagged = mark_spam(comments)

        self.assertEqual([record["id"] for record in flagged], [1])
        self.assertEqual(flagged[0]["previousStatus"], "pending")

    def test_report_records_carry_enough_context_to_reverse_a_decision(self):
        comments = [comment(id=7, authorURL="https://www.binance.com/join")]

        record = mark_spam(comments)[0]

        self.assertEqual(record["id"], 7)
        self.assertEqual(record["articleID"], 100)
        self.assertEqual(record["type"], "comment")
        self.assertEqual(record["previousStatus"], "approved")
        self.assertIn("ordinary remark", record["excerpt"])

    def test_author_rotating_domains_is_flagged(self):
        # One name, three unrelated hosts, none of them individually suspicious.
        comments = [
            comment(id=1, authorName="20bet", authorURL="https://www.noteflight.com/profile/x"),
            comment(id=2, authorName="20bet", authorURL="https://flipboard.com/@20b"),
            comment(id=3, authorName="20bet", authorURL="https://medley-web.com/userinfo.php"),
        ]

        flagged = mark_spam(comments)

        self.assertEqual(len(flagged), 3)
        self.assertEqual(flagged[0]["reason"], "rotating-domains:20bet")

    def test_author_reusing_one_domain_is_not_flagged(self):
        # A regular contributor links their own site every time.
        comments = [
            comment(id=n, authorName="Noel Forté", authorURL="http://noelforte.com/",
                    content=f"A specific and distinct remark number {n}.")
            for n in range(1, 6)
        ]

        self.assertEqual(mark_spam(comments), [])

    def test_summarize_groups_by_rule(self):
        comments = [
            comment(id=1, authorURL="https://www.gate.io/"),
            comment(id=2, authorURL="https://accounts.binance.com/"),
            comment(id=3, authorURL="https://junk.shop/"),
        ]

        self.assertEqual(
            dict(summarize(mark_spam(comments))),
            {"referral-host": 2, "spam-tld": 1},
        )


if __name__ == "__main__":
    unittest.main()
