"""Deterministic offline embedder (swap for a clinical model in prod)."""
from __future__ import annotations
import hashlib, re
import numpy as np

DIM = 256
_token = re.compile(r"[a-z0-9]+")


def embed(text: str) -> np.ndarray:
    vec = np.zeros(DIM, dtype=np.float32)
    for tok in _token.findall(text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % DIM] += 1.0
    n = np.linalg.norm(vec)
    return vec / n if n else vec
