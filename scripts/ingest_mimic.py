"""Ingest MIMIC-IV (demo) ICU stays as clinical summaries into healthcare-rag.

MIMIC is already de-identified, but summaries are still passed through the PHI
redactor (defense in depth). Raw MIMIC data is NEVER committed (license + .gitignore).

Usage:
    python scripts/ingest_mimic.py /path/to/mimic-iv-clinical-database-demo-2.2 [--api http://localhost:8000]
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd


def build_summaries(root: Path, limit: int = 50) -> list[dict]:
    h, icu = root / "hosp", root / "icu"
    patients = pd.read_csv(h / "patients.csv.gz")
    adm = pd.read_csv(h / "admissions.csv.gz")
    stays = pd.read_csv(icu / "icustays.csv.gz")
    dx = pd.read_csv(h / "diagnoses_icd.csv.gz")
    dxd = pd.read_csv(h / "d_icd_diagnoses.csv.gz")
    dx = dx.merge(dxd, on=["icd_code", "icd_version"], how="left")

    pmap = patients.set_index("subject_id")
    amap = adm.set_index("hadm_id")
    out = []
    for _, s in stays.head(limit).iterrows():
        sid, hadm = s["subject_id"], s["hadm_id"]
        p = pmap.loc[sid] if sid in pmap.index else None
        a = amap.loc[hadm] if hadm in amap.index else None
        codes = dx[dx["hadm_id"] == hadm]["long_title"].dropna().head(5).tolist()
        age = int(p["anchor_age"]) if p is not None else "?"
        gender = p["gender"] if p is not None else "?"
        atype = a["admission_type"] if a is not None else "?"
        died = (int(a["hospital_expire_flag"]) == 1) if a is not None else None
        los = round(float(s["los"]), 1) if pd.notna(s["los"]) else "?"
        text = (
            f"ICU stay {s['stay_id']}: {age}yo {gender}. "
            f"Admission type: {atype}. ICU unit: {s['first_careunit']}. "
            f"Length of stay: {los} days. "
            f"Diagnoses: {'; '.join(codes) if codes else 'none coded'}. "
            f"Hospital outcome: {'expired' if died else 'survived' if died is not None else 'unknown'}."
        )
        out.append({"text": text, "source": f"mimic-stay-{s['stay_id']}"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--limit", type=int, default=50)
    a = ap.parse_args()
    summaries = build_summaries(a.root, a.limit)
    print(f"Built {len(summaries)} ICU-stay summaries.")
    try:
        import requests
        for s in summaries:
            requests.post(f"{a.api}/ingest", json=s, timeout=10)
        print(f"Ingested into {a.api}. Sample:\n  {summaries[0]['text']}")
    except Exception as e:
        print(f"(API not reachable: {e}) - sample summary:\n  {summaries[0]['text']}")


if __name__ == "__main__":
    main()
