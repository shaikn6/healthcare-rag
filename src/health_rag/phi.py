"""PHI detection + redaction — HIPAA Safe Harbor style identifiers.

This is a *defense-in-depth demo*, not a certified de-identifier. Real PHI
handling needs a vetted tool (e.g. Microsoft Presidio, AWS Comprehend Medical)
plus a BAA-covered environment. Here we redact obvious identifiers before any
text is embedded, logged, or sent to an LLM.
"""
from __future__ import annotations
import re

# (label, pattern) — order matters; more specific first
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("MRN", re.compile(r"\bMRN[:#]?\s*\d{6,10}\b", re.I)),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("DOB", re.compile(r"\b(?:DOB|D\.O\.B\.?)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.I)),
    ("DATE", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")),
    ("ZIP", re.compile(r"\b\d{5}(?:-\d{4})?\b")),
]


def detect(text: str) -> list[str]:
    """Return labels of PHI categories found (deduped, order-preserving)."""
    found: list[str] = []
    for label, pat in _PATTERNS:
        if pat.search(text) and label not in found:
            found.append(label)
    return found


def redact(text: str) -> tuple[str, list[str]]:
    """Replace detected PHI with [LABEL] tokens. Returns (clean_text, labels)."""
    labels: list[str] = []
    out = text
    for label, pat in _PATTERNS:
        if pat.search(out):
            out = pat.sub(f"[{label}]", out)
            labels.append(label)
    return out, labels


def has_phi(text: str) -> bool:
    return bool(detect(text))
