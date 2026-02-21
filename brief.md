# FHIRBrush — Project Brief

## Elevator Pitch

FHIRBrush is a living clinical canvas that pulls real patient data from a FHIR R4 server, renders it as an interactive node graph, and uses Claude to reason over incoming lab values in real time — reorganizing the canvas, drawing relationships, and narrating what is happening clinically. It is the same FHIR R4 format used by every major hospital system in the US; FHIRBrush could plug into a real EHR with zero changes to the data layer.

---

## The Clinical Scenario

**Patient profile:** A patient with Type 2 Diabetes Mellitus and Chronic Kidney Disease (CKD), already on multiple medications. We are watching their kidneys under pressure in real time as simulated lab observations stream in every 15 seconds.

**The dramatic moment:** Creatinine rises above the threshold → potassium follows → Claude flags an acute-on-chronic kidney injury cascade → the canvas clusters the relevant nodes, draws the causal edges, and the narrative sidebar updates with one clinical sentence. The judges see the canvas react.

---

## Target Patient

| Field | Value |
|-------|-------|
| FHIR Server | `https://hapi.fhir.org/baseR4` |
| Patient ID | *(fill in after running `find_rich_patient.py`)* |
| Key conditions | Diabetes Mellitus Type 2, Chronic Kidney Disease |

To find a good patient:
```bash
pip install -r requirements.txt
python find_rich_patient.py
```
Pick the patient with the highest score (Observations + Conditions weighted). Add the ID above.

---

## LOINC Codes & Clinical Thresholds

These go into the simulation script and the Claude system prompt. Meera owns the values — fill in from her input.

| Lab | LOINC Code | Normal Range | Alert Threshold | Unit |
|-----|-----------|--------------|-----------------|------|
| Creatinine (serum) | `2160-0` | 0.6 – 1.2 | > 1.5 | mg/dL |
| Potassium | `2823-3` | 3.5 – 5.0 | > 5.5 | mEq/L |
| eGFR | *(Meera to confirm)* | > 60 | < 30 | mL/min/1.73m² |
| Hemoglobin A1c | *(Meera to confirm)* | < 5.7 | > 9.0 | % |
| BUN | *(Meera to confirm)* | 7 – 20 | > 40 | mg/dL |

---

## Node Types (FHIR → Canvas)

| FHIR Resource | Node Color | Node Shape | What it represents |
|---------------|-----------|------------|-------------------|
| `Patient` | Blue | Large circle | Central anchor node |
| `Condition` | Orange | Rounded rect | Diagnosis (e.g. CKD, DM2) |
| `Observation` | Green → Red | Small circle (color by value vs threshold) | Lab result |
| `MedicationRequest` | Purple | Diamond | Active medication |
| `Encounter` | Grey | Rect | Hospital/clinic visit |

---

## Claude Output Shape (the contract)

This is the exact JSON structure Claude must return. Meera's system prompt must instruct Claude to return **only** this JSON with no extra text.

```json
{
  "highlight_nodes": ["obs-creatinine", "condition-ckd"],
  "draw_edges": [
    {
      "from": "obs-creatinine",
      "to": "condition-ckd",
      "label": "worsening marker"
    }
  ],
  "risk_cluster": ["obs-creatinine", "obs-potassium", "condition-ckd"],
  "risk_level": "high",
  "narrative": "Rising creatinine with hyperkalemia suggests acute-on-chronic kidney injury — immediate nephrology review indicated."
}
```

**Fields:**
- `highlight_nodes` — node IDs to pulse/glow on the canvas.
- `draw_edges` — new edges to animate between nodes.
- `risk_cluster` — node IDs to visually group into a pulsing risk cluster.
- `risk_level` — `"low"` | `"moderate"` | `"high"`. Controls cluster color.
- `narrative` — exactly one sentence. Sounds like a physician. Max 25 words.

---

## Architecture

```
HAPI FHIR R4 (public)
        │
        ▼
  FastAPI Backend  (port 8000)
  ├── GET  /api/patient/{id}          — fetch Patient resource
  ├── GET  /api/patient/{id}/fhir     — fetch Conditions + Observations + Meds + Encounters
  ├── POST /api/claude/analyze        — send FHIR snapshot to Claude, return structured JSON
  └── WS   /ws/simulate              — stream simulated Observations every 15 s
        │
        ▼
  React Frontend  (port 5173)
  ├── React Flow canvas               — nodes + edges per FHIR resource
  ├── Narrative sidebar               — Claude's one-sentence reasoning
  └── FHIR event log strip            — live stream of incoming resource types
```

---

## Claude API Usage

- **Model:** Claude 3.5 Sonnet (balance of speed and reasoning quality)
- **Call point:** Every time a new simulated Observation arrives (every 15 s), send the full current FHIR snapshot to Claude and parse the JSON response.
- **System prompt:** Meera writes this. It must define each FHIR resource type clinically, include the normal ranges and thresholds from the table above, and instruct Claude to return only the JSON shape above with no surrounding text.
- **Fallback:** If Claude is unavailable or returns malformed JSON, show a hardcoded realistic response so the demo never breaks.

---

## Division of Work

| Who | What |
|-----|------|
| **You (dev)** | Backend (FastAPI, FHIR fetch, WebSocket sim loop, Claude API call + JSON parse), Frontend (React Flow canvas, node types, edge animation, sidebar, event log) |
| **Meera (clinical)** | LOINC codes + ranges + thresholds (fill table above), Claude system prompt, demo spoken script |

---

## The Triage Rule

> If it is 3:30 PM and Claude integration is not working, hardcode a beautiful, realistic Claude response and move on. A visually stunning canvas with a scripted response beats a correct but ugly live pipeline. Be honest about this in the submission write-up — judges respect it.

---

## Demo Script (3 minutes — Meera writes, you both know it)

1. **(0:00 – 0:30)** "This patient has Type 2 Diabetes and we are watching their kidneys under pressure in real time."
2. **(0:30 – 1:30)** Walk through the canvas: Patient node at center, Conditions, Medications, past lab Observations all visible as nodes.
3. **(1:30 – 2:30)** Simulate: "Watch what happens when a new creatinine result comes in." New node appears → Claude reasons → canvas clusters → narrative updates.
4. **(2:30 – 3:00)** Land the line: "This is the same FHIR R4 format used by every major hospital system in the US. FHIRBrush could plug into a real EHR with zero changes to the data layer."

---

## Submission Checklist

- [ ] Patient ID confirmed and filled in above
- [ ] LOINC table completed by Meera
- [ ] Claude system prompt written by Meera
- [ ] FHIR nodes rendering on canvas (Phase 2)
- [ ] Simulation loop running — new Observation every 15 s (Phase 2)
- [ ] Claude returning structured JSON and canvas reacting (Phase 3)
- [ ] Risk cluster pulsing, edges animating, narrative updating (Phase 4)
- [ ] Demo run-through done at least once (Phase 5)
- [ ] Fallback hardcoded Claude response tested and ready
