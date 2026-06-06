from health_rag.phi import detect, redact, has_phi
from health_rag.store import VectorStore
from health_rag.llm import FakeLLM
from health_rag.pipeline import answer


def test_phi_detects_common_identifiers():
    t = "Patient SSN 123-45-6789, MRN: 0099887, call 555-123-4567, dob 01/02/1990"
    labels = detect(t)
    for expected in ("SSN", "MRN", "PHONE"):
        assert expected in labels


def test_phi_redaction_removes_ssn():
    clean, labels = redact("SSN 123-45-6789 on file")
    assert "123-45-6789" not in clean
    assert "[SSN]" in clean and "SSN" in labels


def test_store_redacts_phi_before_storage():
    s = VectorStore()
    res = s.add("Patient John, SSN 111-22-3333, has hypertension.", "note")
    # raw PHI must NOT survive into stored chunk text
    assert all("111-22-3333" not in c.text for c in s.chunks)
    assert "SSN" in res["phi_redacted"]


def test_query_grounds_and_attaches_disclaimer():
    s = VectorStore()
    s.add("Metformin is first-line for type 2 diabetes.", "diabetes-guideline")
    out = answer(s, FakeLLM(), "what is first line for type 2 diabetes?")
    assert "diabetes-guideline" in out["sources"]
    assert "not medical advice" in out["disclaimer"].lower()


def test_query_strips_phi_from_question():
    s = VectorStore()
    s.add("Sepsis: start antibiotics within one hour.", "sepsis")
    out = answer(s, FakeLLM(), "My MRN: 1234567 — sepsis antibiotic timing?")
    assert "MRN" in out["question_phi_redacted"]
