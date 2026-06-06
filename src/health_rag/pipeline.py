"""Clinical RAG orchestration with safety-first prompting."""
from __future__ import annotations
from .llm import LLM
from .store import VectorStore
from .phi import redact

DISCLAIMER = (
    "⚠️ Informational only — not medical advice. Verify against primary sources "
    "and consult a licensed clinician."
)

SYSTEM = (
    "You are a clinical information assistant for healthcare professionals. "
    "Answer ONLY from the provided guideline context. Cite sources as [source]. "
    "If the context does not contain the answer, say 'Not found in the provided "
    "guidelines.' Never invent dosages, diagnoses, or treatment claims. Do not "
    "provide a definitive diagnosis; frame guidance as decision support."
)


def answer(store: VectorStore, llm: LLM, question: str, k: int = 3) -> dict:
    # redact PHI from the inbound question too — never send PHI to the LLM
    q_clean, q_phi = redact(question)
    hits = store.search(q_clean, k=k)
    if not hits:
        return {"answer": "No guidelines ingested yet.", "sources": [],
                "disclaimer": DISCLAIMER, "question_phi_redacted": q_phi}
    context = "\n\n".join(f"[{c.source}] {c.text}" for c, _ in hits)
    user = f"Guideline context:\n{context}\n\nQuestion: {q_clean}"
    return {
        "answer": llm.complete(SYSTEM, user),
        "sources": sorted({c.source for c, _ in hits}),
        "disclaimer": DISCLAIMER,
        "question_phi_redacted": q_phi,
    }
