# first line: 52
@memory.cache # Disk cache for repeated runs
def _generateKShingles_impl(document: str, k: int) -> NDArray[np.int64]:
    if len(document) < k:
        return np.array([], dtype=np.int64)
    return np.unique([int(hashlib.sha1(document[i:i + k].encode()).hexdigest(), 16) % (2**31 - 1) for i in range(len(document) - k + 1)]) # Uses deterministic hashing function to reduce overhead
