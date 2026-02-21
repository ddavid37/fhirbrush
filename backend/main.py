"""
FHIRBrush Phase 2 backend.
Serves FHIR data from synthetic_patients.json and streams simulated
creatinine observations over WebSocket every 15 seconds.
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ── app setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="FHIRBrush API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── load patient data once at startup ────────────────────────────────────────

DATA_FILE = Path(__file__).parent.parent / "synthetic_patients.json"
_raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))

# Index bundles by patient ID for O(1) lookup
PATIENT_BUNDLES: dict[str, list[dict]] = {}
for bundle in _raw["patients"]:
    for entry in bundle["entry"]:
        r = entry["resource"]
        if r["resourceType"] == "Patient":
            PATIENT_BUNDLES[r["id"]] = bundle["entry"]
            break

# ── helpers ──────────────────────────────────────────────────────────────────

def _resources_of(patient_id: str, resource_type: str) -> list[dict]:
    entries = PATIENT_BUNDLES.get(patient_id, [])
    return [e["resource"] for e in entries if e["resource"]["resourceType"] == resource_type]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Rising creatinine values to simulate CKD deterioration during the demo
CREATININE_SIM = [1.4, 1.55, 1.7, 1.85, 2.0, 2.2, 2.5, 2.8, 3.1, 3.5]
POTASSIUM_SIM  = [4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 6.0, 6.1, 6.2, 6.3]
_sim_step: dict[str, int] = {}


def _make_sim_observation(patient_id: str) -> dict:
    step = _sim_step.get(patient_id, 0)
    _sim_step[patient_id] = step + 1
    creat = CREATININE_SIM[min(step, len(CREATININE_SIM) - 1)]
    potassium = POTASSIUM_SIM[min(step, len(POTASSIUM_SIM) - 1)]
    creat += random.uniform(-0.05, 0.05)
    potassium += random.uniform(-0.05, 0.05)
    return {
        "resourceType": "Observation",
        "id": f"sim-creat-{uuid.uuid4().hex[:8]}",
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                   "code": "laboratory"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": "2160-0",
                              "display": "Creatinine [Mass/volume] in Serum"}],
                 "text": "Creatinine"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": _now_iso(),
        "valueQuantity": {"value": round(creat, 2), "unit": "mg/dL",
                          "system": "http://unitsofmeasure.org", "code": "mg/dL"},
        "_simulated": True,
        "_potassium": round(potassium, 2),   # piggyback so frontend gets both
        "_step": step,
    }


# ── severity scoring ─────────────────────────────────────────────────────────

# Thresholds match brief.md / fhirToNodes.ts
_THRESHOLDS: dict[str, dict] = {
    "2160-0":  {"label": "Creatinine", "high": 1.5,  "critical": 2.0,  "direction": "high"},
    "2823-3":  {"label": "Potassium",  "high": 5.5,  "critical": 6.0,  "direction": "high"},
    "33914-3": {"label": "eGFR",       "high": 30,   "critical": 15,   "direction": "low"},
    "4548-4":  {"label": "HbA1c",      "high": 9.0,  "critical": 11.0, "direction": "high"},
    "3094-0":  {"label": "BUN",        "high": 40,   "critical": 60,   "direction": "high"},
}

# Critical ICD-10 condition codes
_CRITICAL_CONDITIONS = {"N18.4", "N18.5", "I50.9", "J44.1"}
_MODERATE_CONDITIONS = {"E11.9", "N18.3", "I10", "J45.50"}


def _score_patient(patient_id: str) -> dict:
    entries  = PATIENT_BUNDLES.get(patient_id, [])
    patient  = next((e["resource"] for e in entries if e["resource"]["resourceType"] == "Patient"), {})
    obs_list = [e["resource"] for e in entries if e["resource"]["resourceType"] == "Observation"]
    cond_list= [e["resource"] for e in entries if e["resource"]["resourceType"] == "Condition"]

    name_obj  = patient.get("name", [{}])[0]
    full_name = (name_obj.get("given", [""])[0] + " " + name_obj.get("family", "")).strip()
    initials  = "".join(p[0].upper() for p in full_name.split() if p)[:2]

    severity  = "green"
    reasons: list[str] = []

    # Score observations — use the most recent value per LOINC code
    latest: dict[str, float] = {}
    for o in obs_list:
        code = (o.get("code", {}).get("coding") or [{}])[0].get("code", "")
        val  = (o.get("valueQuantity") or {}).get("value")
        dt   = o.get("effectiveDateTime", "")
        if code in _THRESHOLDS and val is not None:
            if code not in latest:
                latest[code] = (val, dt)
            else:
                if dt > latest[code][1]:
                    latest[code] = (val, dt)

    for code, (val, _) in latest.items():
        cfg = _THRESHOLDS[code]
        if cfg["direction"] == "high":
            if val >= cfg["critical"]:
                severity = "red"
                reasons.append(f"{cfg['label']} critically high ({val})")
            elif val >= cfg["high"]:
                if severity != "red":
                    severity = "orange"
                reasons.append(f"{cfg['label']} elevated ({val})")
        else:  # low direction (eGFR)
            if val <= cfg["critical"]:
                severity = "red"
                reasons.append(f"{cfg['label']} critically low ({val})")
            elif val <= cfg["high"]:
                if severity != "red":
                    severity = "orange"
                reasons.append(f"{cfg['label']} low ({val})")

    # Score conditions
    for cond in cond_list:
        for coding in (cond.get("code", {}).get("coding") or []):
            code = coding.get("code", "")
            if code in _CRITICAL_CONDITIONS:
                severity = "red"
                reasons.append(f"Critical condition: {coding.get('display', code)}")
            elif code in _MODERATE_CONDITIONS and severity == "green":
                severity = "orange"
                reasons.append(f"Chronic condition: {coding.get('display', code)}")

    return {
        "id":       patient_id,
        "name":     full_name,
        "initials": initials,
        "gender":   patient.get("gender"),
        "severity": severity,
        "reasons":  reasons[:3],   # top 3 reasons to show in tooltip
    }


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "fhirbrush-backend"}


@app.get("/api/patients")
def list_patients():
    """List all available patients (id + name + scenario summary)."""
    result = []
    for pid, entries in PATIENT_BUNDLES.items():
        patient = next(e["resource"] for e in entries if e["resource"]["resourceType"] == "Patient")
        name_obj = patient.get("name", [{}])[0]
        full_name = (name_obj.get("given", [""])[0] + " " + name_obj.get("family", "")).strip()
        conditions = [e["resource"] for e in entries if e["resource"]["resourceType"] == "Condition"]
        observations = [e["resource"] for e in entries if e["resource"]["resourceType"] == "Observation"]
        medications = [e["resource"] for e in entries if e["resource"]["resourceType"] == "MedicationRequest"]
        result.append({
            "id": pid,
            "name": full_name,
            "gender": patient.get("gender"),
            "birthDate": patient.get("birthDate"),
            "num_conditions": len(conditions),
            "num_observations": len(observations),
            "num_medications": len(medications),
        })
    return result


@app.get("/api/patients/severity")
def patients_severity():
    """
    Return severity (red/orange/green) for all patients.
    Used by the priority dot bar at the top of the dashboard.
    """
    return [_score_patient(pid) for pid in PATIENT_BUNDLES]


@app.get("/api/patient/{patient_id}")
def get_patient(patient_id: str):
    """Return the Patient resource."""
    entries = PATIENT_BUNDLES.get(patient_id)
    if not entries:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    patient = next(e["resource"] for e in entries if e["resource"]["resourceType"] == "Patient")
    return patient


@app.get("/api/patient/{patient_id}/fhir")
def get_patient_fhir(patient_id: str):
    """
    Return all FHIR resources for this patient, grouped by type.
    This is the main endpoint the canvas uses to populate nodes.
    """
    if patient_id not in PATIENT_BUNDLES:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return {
        "patient":          _resources_of(patient_id, "Patient")[0],
        "conditions":       _resources_of(patient_id, "Condition"),
        "observations":     _resources_of(patient_id, "Observation"),
        "medications":      _resources_of(patient_id, "MedicationRequest"),
        "encounters":       _resources_of(patient_id, "Encounter"),
    }


# ── WebSocket simulation ──────────────────────────────────────────────────────

@app.websocket("/ws/simulate/{patient_id}")
async def simulate(websocket: WebSocket, patient_id: str):
    """
    Stream a new creatinine Observation every 15 seconds.
    The frontend adds it as a new node and sends it to Claude.
    """
    if patient_id not in PATIENT_BUNDLES:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    _sim_step[patient_id] = 0
    try:
        while True:
            obs = _make_sim_observation(patient_id)
            await websocket.send_json({"type": "new_observation", "data": obs})
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        pass
