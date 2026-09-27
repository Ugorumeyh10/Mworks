from __future__ import annotations

import hashlib
import math
import re
import struct

_TOKEN = re.compile(r"[a-z0-9]{3,32}", re.I)
_HASHES = 64


def sha256_hex(blob: bytes | str) -> str:
    if isinstance(blob, str):
        blob = blob.encode("utf-8", errors="ignore")
    return hashlib.sha256(blob).hexdigest()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def minhash_sig(text: str) -> str:
    tokens = set(_TOKEN.findall(_norm(text)))
    if not tokens:
        return ""
    mins: list[int] = []
    for i in range(_HASHES):
        lowest = 2**32 - 1
        prefix = f"{i}:".encode()
        for tok in tokens:
            digest = hashlib.sha256(prefix + tok.encode()).digest()
            val = struct.unpack(">I", digest[:4])[0]
            if val < lowest:
                lowest = val
        mins.append(lowest)
    return ",".join(f"{n:08x}" for n in mins)


def bow_embed(text: str, dim: int = 64) -> tuple[float, ...]:
    """Hashed bag-of-words vector. Local only; never calls a model."""
    vec = [0.0] * dim
    for tok in _TOKEN.findall(_norm(text)):
        h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return tuple(x / norm for x in vec)


def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right, strict=False))))


def jaccard(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    a = left.split(",")
    b = right.split(",")
    if len(a) != len(b) or not a:
        return 0.0
    hits = sum(1 for x, y in zip(a, b, strict=False) if x == y)
    return hits / len(a)
