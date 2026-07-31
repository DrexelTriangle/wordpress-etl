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
    ".lol",
)

# Product names used as the author name. Kept short and unambiguous on purpose:
# a real business does comment under its own name (Legendary Coffee Company did),
# so this only covers categories no legitimate commenter falls into.
SPAM_AUTHOR_KEYWORDS = (
    "erectile dysfunction",
    "viagra",
    "cialis",
    "casino",
    "betting",
    "escort",
    "temp mail",
    "coupons",
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

# Anything shaped like host.tld, anywhere in a URL string. See _hosts.
HOST_TOKEN_PATTERN = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}")

# Two or more links in one comment body is a link drop, not a conversation.
LINK_PATTERN = re.compile(r"https?://", re.IGNORECASE)
MIN_LINKS = 2

# One author name posting from several unrelated domains. Real commenters reuse
# one URL or none; rotating domains is how host-parasite campaigns evade a
# domain blocklist, and it is the only invariant they leave behind.
MIN_ROTATING_HOSTS = 3

# Identical bodies posted by different people. Short collisions are plausible
# ("Great article!"), long ones are not, so the rule only applies past a length
# where organic repetition stops happening.
MIN_DUPLICATE_COPIES = 2
MIN_DUPLICATE_LENGTH = 40

SPAM_STATUS = "spam"


def _host(url):
    """The registered host of a URL, or "" if there isn't one.

    Only for reporting and for the rotating-domain rule. Matching goes through
    _hosts, which does not trust the URL to be well-formed.
    """
    if not url:
        return ""
    try:
        host = urlparse(str(url).strip()).netloc.lower()
    except ValueError:
        return ""
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _hosts(url):
    """Every host-shaped token in a URL, not just the one urlparse finds.

    Two things in the real data defeat netloc alone. `http://https//fexie.xyz/x`
    parses to a netloc of "https", hiding a .xyz domain; and host-parasite spam
    puts its actual domain in the path, as in
    `southsidesox.com/users/www.20bet.com`. Both are still matchable if the
    whole string is scanned, and a false positive here needs a spam domain to
    appear somewhere in a genuine commenter's URL, which does not happen.
    """
    if not url:
        return []
    found = []
    for token in HOST_TOKEN_PATTERN.findall(str(url).lower()):
        token = token.strip(".")
        found.append(token[4:] if token.startswith("www.") else token)
    return found


def _normalize_body(body):
    return re.sub(r"\s+", " ", str(body or "").strip().lower())


def _host_reason(url):
    for host in _hosts(url):
        if host in SPAM_HOSTS or any(host.endswith("." + h) for h in SPAM_HOSTS):
            return f"referral-host:{host}"
        if host.endswith(SPAM_TLDS):
            return f"spam-tld:{host}"
        for keyword in SPAM_HOST_KEYWORDS:
            if keyword in host:
                return f"spam-host-keyword:{host}"
    return None


def _rotating_authors(comments):
    """Author names that posted from MIN_ROTATING_HOSTS or more distinct hosts."""
    hosts_by_author = {}
    for comment in comments:
        name = str(comment.get("authorName") or "").strip().lower()
        host = _host(comment.get("authorURL"))
        if name and host:
            hosts_by_author.setdefault(name, set()).add(host)
    return {
        name
        for name, hosts in hosts_by_author.items()
        if len(hosts) >= MIN_ROTATING_HOSTS
    }


def _duplicate_bodies(comments):
    counts = Counter()
    for comment in comments:
        body = _normalize_body(comment.get("content"))
        if len(body) >= MIN_DUPLICATE_LENGTH:
            counts[body] += 1
    return frozenset(body for body, n in counts.items() if n >= MIN_DUPLICATE_COPIES)


def classify(comment, duplicate_bodies=frozenset(), rotating_authors=frozenset()):
    """Return the reason this comment is spam, or None if it looks genuine."""
    reason = _host_reason(comment.get("authorURL"))
    if reason:
        return reason

    name = str(comment.get("authorName") or "").strip().lower()
    if name and name in rotating_authors:
        return f"rotating-domains:{name}"
    for keyword in SPAM_AUTHOR_KEYWORDS:
        if keyword in name:
            return f"spam-author-keyword:{name}"

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
    rotating_authors = _rotating_authors(comments)
    flagged = []

    for comment in comments:
        if comment.get("status") == SPAM_STATUS:
            continue
        reason = classify(comment, duplicate_bodies, rotating_authors)
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
