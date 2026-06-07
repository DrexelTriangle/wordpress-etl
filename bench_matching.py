"""Benchmark the author-matching hot paths: old O(n^2) compare vs new LSH.

Runs on the real pipeline data in logs/. Reconstructs the previous
implementations faithfully so the speedup reflects the actual change.
"""
import json
import time

from minhashlib import MinHash, MinHashLSH, similarity
from Utils.Utility import Utility
from Utils.ArticleAuthorMatching import AuthorSimilarityIndex, collect_unique_author_names

clean = lambda s: Utility.cleanDocument(str(s), "similarity")


def timed(label, fn, *args):
    start = time.perf_counter()
    result = fn(*args)
    elapsed = time.perf_counter() - start
    print(f"  {label:34} {elapsed:8.3f}s   {result}")
    return elapsed, result


# ---------------------------------------------------------------------------
# Stage 1: author dedup (Policy._autoResolve comparison core)
# ---------------------------------------------------------------------------
def autoresolve_old(names):
    mh = MinHash()
    keep = [True] * len(names)
    merges = flags = 0
    for i in range(len(names)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(names)):
            if not keep[j]:
                continue
            s = mh.compare(names[i], names[j])      # recompute both sigs every call
            if s >= 0.9:
                keep[j] = False
                merges += 1
            elif s >= 0.8:
                flags += 1
    return f"merges={merges} flags={flags}"


def autoresolve_new(names):
    mh = MinHash()
    sigs = [mh.signature(n) for n in names]          # O(n) signatures
    lsh = MinHashLSH(threshold=0.7, num_perm=mh.num_perm)
    for i, s in enumerate(sigs):
        lsh.insert(i, s)
    cand = [sorted(c for c in lsh.query(sigs[i]) if c > i) for i in range(len(names))]
    keep = [True] * len(names)
    merges = flags = 0
    for i in range(len(names)):
        if not keep[i]:
            continue
        for j in cand[i]:
            if not keep[j]:
                continue
            s = similarity(sigs[i], sigs[j])
            if s >= 0.9:
                keep[j] = False
                merges += 1
            elif s >= 0.8:
                flags += 1
    return f"merges={merges} flags={flags}"


# ---------------------------------------------------------------------------
# Stage 2: article->author similarity matching (apply_similarity_match)
# ---------------------------------------------------------------------------
def match_old(unknown_keys, lookup):
    matched = flagged = unknown = 0
    for clean_key in unknown_keys:
        checker = MinHash()                          # fresh engine per unknown name
        best, best_sim, similar = None, 0.0, []
        for candidate_key, (aid, dname) in lookup.items():
            s = checker.compare(clean_key, candidate_key)  # recompute both sigs every call
            if s >= 0.9 and s > best_sim:
                best, best_sim = (aid, dname), s
            elif s >= 0.8:
                similar.append((aid, dname, s))
        if best:
            matched += 1
        elif similar:
            flagged += 1
        else:
            unknown += 1
    return f"matched={matched} flagged={flagged} unknown={unknown}"


def match_new(unknown_keys, lookup):
    index = AuthorSimilarityIndex(lookup)            # signatures + LSH built once
    matched = flagged = unknown = 0
    for clean_key in unknown_keys:
        best, similar = index.match(clean_key)
        if best:
            matched += 1
        elif similar:
            flagged += 1
        else:
            unknown += 1
    return f"matched={matched} flagged={flagged} unknown={unknown}"


def main():
    MinHash().signature("warm up the numba jit before timing")  # exclude JIT cost

    authors = json.load(open("logs/auth_output.json"))
    merged = json.load(open("logs/merged_auth_output.json"))
    articles = list(json.load(open("logs/article_output.json")).values())

    names = [clean(a["display_name"]) for a in authors.values() if a.get("display_name")]
    print(f"\nStage 1 - author dedup  (n={len(names)} authors, {len(names)*(len(names)-1)//2:,} possible pairs)")
    old1, _ = timed("old  O(n^2) compare", autoresolve_old, names)
    new1, _ = timed("new  LSH", autoresolve_new, names)
    print(f"  -> speedup x{old1/new1:.1f}")

    lookup = {}
    for a in merged.values():
        dn = a.get("display_name")
        if dn:
            lookup.setdefault(clean(dn), (a.get("id"), dn))
    unique = collect_unique_author_names(articles, Utility.cleanDocument)
    unknown_keys = [k for k in unique if k not in lookup]   # the similarity workload
    print(f"\nStage 2 - article->author match  (unknown names={len(unknown_keys)} x authors={len(lookup)} = {len(unknown_keys)*len(lookup):,} comparisons)")
    old2, _ = timed("old  scan + per-call MinHash", match_old, unknown_keys, lookup)
    new2, _ = timed("new  shared LSH index", match_new, unknown_keys, lookup)
    print(f"  -> speedup x{old2/new2:.1f}")

    print(f"\nCombined matching time:  old {old1+old2:.3f}s  ->  new {new1+new2:.3f}s   (x{(old1+old2)/(new1+new2):.1f})")


if __name__ == "__main__":
    main()
