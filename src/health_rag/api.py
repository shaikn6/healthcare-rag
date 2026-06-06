"""FastAPI surface — designed to sit behind n8n / an app gateway."""
from __future__ import annotations
import os
from fastapi import FastAPI
from pydantic import BaseModel

from .llm import ClaudeLLM, FakeLLM
from .pipeline import answer, DISCLAIMER
from .store import VectorStore
from .phi import detect

app = FastAPI(title="Healthcare RAG (Claude)", version="0.1.0")
store = VectorStore()


def _llm():
    return ClaudeLLM() if os.environ.get("ANTHROPIC_API_KEY") else FakeLLM()


class Doc(BaseModel):
    text: str
    source: str = "guideline"


class Query(BaseModel):
    question: str
    k: int = 3


@app.get("/health")
def health():
    return {"status": "ok", "chunks": len(store.chunks),
            "live_llm": bool(os.environ.get("ANTHROPIC_API_KEY")), "disclaimer": DISCLAIMER}


@app.post("/ingest")
def ingest(doc: Doc):
    """Ingest a clinical guideline. PHI is redacted before storage/embedding."""
    return store.add(doc.text, doc.source)


@app.post("/scan-phi")
def scan_phi(doc: Doc):
    """Utility for n8n: report PHI categories without storing anything."""
    return {"phi_found": detect(doc.text)}


@app.post("/query")
def query(q: Query):
    return answer(store, _llm(), q.question, k=q.k)
