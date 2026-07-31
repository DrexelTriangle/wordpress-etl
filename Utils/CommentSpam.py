"""Reclassify imported comments that WordPress approved but that are spam.

WordPress's WXR exporter already drops comments whose `comment_approved` is
`spam`, so nothing labelled spam ever reaches the ETL. What does reach it is
everything WordPress *approved* -- including the years of link spam that got
past (or predates) the site's own filter. On the 2025-09-25 export that was
roughly half the comment table: crypto-referral link drops, content-farm
templates posted verbatim across dozens of articles, and pingbacks from
throwaway SEO domains.

These rules are deliberately high-precision rather than exhaustive. A false
positive hides a real reader's comment, which is worse than leaving a stray
spam row visible, so every rule keys on something a genuine commenter has
effectively no reason to do. Nothing is deleted: rows are re-statused to
`spam`, which hides them from the public endpoint while leaving them in the
table for a moderator to reverse.
"""

import re
from collections import Counter
from urllib.parse import urlparse


# Referral-link farms. A reader discussing a Drexel article does not link to an
# exchange signup page, and these four hosts alone account for the single
# largest cluster in the export.
SPAM_HOSTS = frozenset(
    {
        "binance.com",
        "binance.info",
        "binance.us",
        "accounts.binance.com",
        "gate.io",
        "gate.com",
        "bybit.com",
        "kucoin.com",
        "okx.com",
        "mexc.com",
        "htx.com",
        "bitget.com",
        "coinbase-login.com",
        "gate-oi.info",
        # Long-running campaigns visible in the export's tail. Listed as exact
        # hosts rather than keywords because the obvious keywords ("mail",
        # "health") also occur inside legitimate domains.
        "healthmassive.com",
        "healthstay.org",
        "taxtmail.com",
        "taxt.email",
        "tmailgenerate.com",
        "upxmail.com",
        "dangalgym.com",
        "bwerpipes.com",
        "elitepipeiraq.com",
        "sbwlg.com",
        "snowapk.com",
        "addmeintopsite.com",
        "bet-promokod.ru",
        "20bet.com",
    }
)

# Registrar-bargain TLDs. Effectively nothing legitimate that links to a student
# newspaper lives on one of these.
SPAM_TLDS = (
    ".shop",
    ".xyz",
    ".top",
    ".icu",
    ".click",
    ".online",
    ".cyou",
    ".sbs",
    ".buzz",
    ".monster",
    ".quest",
)

# Substrings in the *host*, not the body -- matching the body would flag real
# articles about, say, a casino development or a health study.
SPAM_HOST_KEYWORDS = (
    "casino",
    "porn",
    "escort",
    "viagra",
    "cialis",
    "garcinia",
    "weightloss",
    "weight-loss",
    "teeth-whitening",
    "antlerspray",
    "payday",
    "baddiehub",
    "tempmail",
    "temp-mail",
    "weddingdresses",
    "attractwomen",
    "blackboardhub",
    "blackboardlist",
)

# Two or more links in one comment body is a link drop, not a conversation.
LINK_PATTERN = re.compile(r"https?://", re.IGNORECASE)
MIN_LINKS = 2

# Identical bodies posted by different people. Short collisions are plausible
# ("Great article!"), long ones are not, so the rule only applies past a length
# where organic repetition stops happening.
MIN_DUPLICATE_COPIES = 2
MIN_DUPLICATE_LENGTH = 40

SPAM_STATUS = "spam"


def _host(url):
    if not url:
        return ""
    try:
        host = urlparse(str(url).strip()).netloc.lower()
    except ValueError:
        return ""
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _normalize_body(body):
    return re.sub(r"\s+", " ", str(body or "").strip().lower())


def _host_reason(url):
    host = _host(url)
    if not host:
        return None
    if host in SPAM_HOSTS or any(host.endswith("." + h) for h in SPAM_HOSTS):
        return f"referral-host:{host}"
    if host.endswith(SPAM_TLDS):
        return f"spam-tld:{host}"
    for keyword in SPAM_HOST_KEYWORDS:
        if keyword in host:
            return f"spam-host-keyword:{host}"
    return None


def _duplicate_bodies(comments):
    counts = Counter()
    for comment in comments:
        body = _normalize_body(comment.get("content"))
        if len(body) >= MIN_DUPLICATE_LENGTH:
            counts[body] += 1
    return frozenset(body for body, n in counts.items() if n >= MIN_DUPLICATE_COPIES)


def classify(comment, duplicate_bodies=frozenset()):
    """Return the reason this comment is spam, or None if it looks genuine."""
    reason = _host_reason(comment.get("authorURL"))
    if reason:
        return reason

    content = str(comment.get("content") or "")
    if len(LINK_PATTERN.findall(content)) >= MIN_LINKS:
        return "link-stuffed-body"

    if _normalize_body(content) in duplicate_bodies:
        return "duplicate-body"

    return None


def mark_spam(comments):
    """Re-status spam comments in place. Returns a list of report records.

    Comments already flagged by WordPress are left alone -- there is nothing to
    re-decide -- so this only ever moves a row from approved/pending to spam.
    """
    duplicate_bodies = _duplicate_bodies(comments)
    flagged = []

    for comment in comments:
        if comment.get("status") == SPAM_STATUS:
            continue
        reason = classify(comment, duplicate_bodies)
        if not reason:
            continue
        flagged.append(
            {
                "id": comment.get("id"),
                "articleID": comment.get("articleID"),
                "type": comment.get("type"),
                "previousStatus": comment.get("status"),
                "reason": reason,
                "authorName": comment.get("authorName"),
                "authorURL": comment.get("authorURL"),
                "excerpt": _normalize_body(comment.get("content"))[:160],
            }
        )
        comment["status"] = SPAM_STATUS

    return flagged


def summarize(flagged):
    """Count flagged comments by rule, for the run log."""
    return Counter(record["reason"].split(":", 1)[0] for record in flagged)
