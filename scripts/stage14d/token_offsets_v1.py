"""Locate requested character boundaries in saved IDs without retokenization."""
from bisect import bisect_left, bisect_right


def valid_boundaries_for_offsets(tok, ids, raw, offsets, stride=256):
    assert stride > 0
    assert tok.decode(ids, skip_special_tokens=True) == raw
    points = sorted(set(offsets))
    assert all(0 <= p <= len(raw) for p in points)
    cache = {0: (0, 0)}

    def boundary(n):
        if n not in cache:
            prefix = tok.decode(ids[:n], skip_special_tokens=True)
            # Partial UTF-8 prefixes may decode to replacement characters.
            cache[n] = (n, len(prefix)) if raw.startswith(prefix) else None
        return cache[n]

    coarse = [boundary(n) for n in sorted(set(range(0, len(ids) + 1, stride)) | {len(ids)})]
    coarse = [v for v in coarse if v is not None]
    chars = [c for _, c in coarse]
    assert chars == sorted(chars), 'Decoder is not prefix-monotone on valid boundaries'
    for p in points:
        # Bracket strictly outside the requested offset to include plateaus
        # created by skipped special tokens. Refine every saved ID in between.
        left = max(0, bisect_left(chars, p) - 1)
        right = min(len(coarse) - 1, bisect_right(chars, p))
        for n in range(coarse[left][0], coarse[right][0] + 1):
            boundary(n)
    return sorted(v for v in cache.values() if v is not None)
