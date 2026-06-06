#!/usr/bin/env bash
# Start healthcare-rag API with your Claude key + load MIMIC ICU data.
# 1. cp .env.example .env  and put your real ANTHROPIC_API_KEY in it
# 2. ./run-local.sh
set -e
cd "$(dirname "$0")"
PY=/opt/anaconda3/bin/python3
[ -f .env ] && export $(grep -v '^#' .env | xargs) || { echo "No .env — copy .env.example to .env and add your key"; exit 1; }

# free port 8000 if something's on it
PID=$(lsof -nP -iTCP:8000 -sTCP:LISTEN -t 2>/dev/null || true)
[ -n "$PID" ] && { echo "killing old API on :8000 (pid $PID)"; kill "$PID"; sleep 2; }

echo "starting API with live Claude ($([ -n "$ANTHROPIC_API_KEY" ] && echo 'key set' || echo 'NO KEY'))..."
PYTHONPATH=src nohup $PY -m uvicorn health_rag.api:app --host 0.0.0.0 --port 8000 > /tmp/health-rag-api.log 2>&1 &
for i in $(seq 1 15); do curl -s localhost:8000/health >/dev/null 2>&1 && break; sleep 1; done

MIMIC="${MIMIC_PATH:-$HOME/.mimic-demo/mimic-iv-clinical-database-demo-2.2}"
if [ -d "$MIMIC" ]; then
  echo "ingesting MIMIC ICU stays..."
  PYTHONPATH=src $PY scripts/ingest_mimic.py "$MIMIC" --limit 40 2>/dev/null | tail -1
fi
echo "READY. live_llm=$(curl -s localhost:8000/health | $PY -c 'import sys,json;print(json.load(sys.stdin)["live_llm"])')"
echo "Test: curl -X POST localhost:5678/webhook/ask -H 'content-type: application/json' -d '{\"question\":\"ICU heart failure patients?\"}'"
