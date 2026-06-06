"""Vector store that REDACTS PHI before anything is persisted or embedded."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from .embeddings import embed
from .phi import redact


@dataclass
class Chunk:
    text: str            # already PHI-redacted
    source: str
    vector: np.ndarray
    phi_labels: tuple[str, ...]


@dataclass
class VectorStore:
    chunks: list[Chunk] = field(default_factory=list)

    def add(self, text: str, source: str, chunk_size: int = 400) -> dict:
        added, all_labels = 0, set()
        for i in range(0, len(text), chunk_size):
            piece = text[i : i + chunk_size].strip()
            if not piece:
                continue
            clean, labels = redact(piece)          # PHI stripped HERE, pre-embed
            self.chunks.append(Chunk(clean, source, embed(clean), tuple(labels)))
            all_labels.update(labels)
            added += 1
        return {"chunks": added, "phi_redacted": sorted(all_labels)}

    def search(self, query: str, k: int = 3) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        q = embed(query)
        scored = [(c, float(np.dot(q, c.vector))) for c in self.chunks]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
