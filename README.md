# healthcare-rag

Clinical-document **RAG on Claude** with **PHI guardrails**, served via FastAPI and
orchestrated with **n8n**. Targets healthcare AI engineering: retrieval-grounded
answers, compliance-aware design, and safe LLM prompting.

> ⚠️ Demo/educational. Uses **synthetic** data only. Not a certified de-identifier
> and not for real PHI without a BAA-covered environment + vetted tooling.

## Why this is healthcare-shaped
- **PHI redaction before embed/log/LLM** (`phi.py`, HIPAA Safe-Harbor-style identifiers) — raw identifiers never reach storage or the model
- **Safety-first prompt** — grounded, cites sources, refuses to diagnose, appends a disclaimer
- **Self-hostable** (Docker) — data stays on your infra, the on-prem posture health systems require
- **`/scan-phi`** endpoint so an orchestrator can gate documents before ingest

## Stack
Anthropic Claude · FastAPI · numpy vector store · pytest (offline, LLM mocked) · Docker · n8n

## Quickstart
```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=sk-ant-...        # only for live /query
uvicorn health_rag.api:app --reload        # http://localhost:8000/docs
pytest                                      # offline, no key needed
```

## Endpoints
- `POST /ingest`  — store a guideline (PHI redacted first); returns redacted labels
- `POST /scan-phi`— report PHI categories without storing
- `POST /query`   — grounded answer + sources + disclaimer
- `GET  /health`

```bash
curl -X POST localhost:8000/ingest -H 'content-type: application/json' \
  -d '{"text":"Metformin is first-line for type 2 diabetes.","source":"dm2"}'
curl -X POST localhost:8000/query  -H 'content-type: application/json' \
  -d '{"question":"first line for type 2 diabetes?"}'
```

## n8n orchestration
`workflows/healthcare-rag.n8n.json` — import into n8n (Workflows → Import from File).
Exposes a `POST /webhook/ask` that calls this API's `/query` and shapes the response.
The API runs on the host; the workflow reaches it via `http://host.docker.internal:8000`.

```
n8n Webhook(/ask) ─▶ HTTP POST /query ─▶ Set(answer+disclaimer) ─▶ response
```

This is the "understand AI systems" piece: you can see retrieval → grounded LLM →
guardrail → delivery wired as visible nodes.

## Architecture
```
doc ─▶ /scan-phi (gate) ─▶ /ingest ─▶ redact PHI ─▶ embed ─▶ VectorStore
query ─▶ redact PHI ─▶ retrieve top-k ─▶ grounded prompt ─▶ Claude ─▶ answer+sources+disclaimer
```

## Real ICU data (MIMIC-IV)
`scripts/ingest_mimic.py` turns MIMIC-IV ICU stays into clinical summaries and ingests
them (PHI-redacted, defense-in-depth) — proving the pipeline on real de-identified data.

```bash
# MIMIC-IV DEMO (100 patients) is open — no credentialing:
#   https://physionet.org/content/mimic-iv-demo/
python scripts/ingest_mimic.py /path/to/mimic-iv-clinical-database-demo-2.2
```
Raw MIMIC data is **never committed** (PhysioNet DUA + `.gitignore`). Full MIMIC-IV
requires PhysioNet credentialing (CITI training + data use agreement).
