# FHIRBrush

![FHIRBrush v1 — React Flow canvas with FHIR nodes](version1.png)

# FHIRBrush — Project Description

## Overview

**FHIRBrush** is a living clinical intelligence canvas that transforms static patient health records into a dynamic, reasoning-driven graph — where artificial intelligence doesn't just answer questions, it *paints the screen*.

Traditional healthcare dashboards are passive: they show you data and wait. FHIRBrush inverts this entirely. The moment a new lab result arrives from the FHIR stream, Claude analyzes the full patient context — conditions, medications, history, trending values — and responds by **reorganizing the canvas itself**: highlighting nodes that matter, drawing causal edges between a rising creatinine and a deteriorating kidney condition, clustering risk factors into a pulsing danger zone, and generating a single physician-grade sentence of clinical reasoning. The interface is not a window into Claude's output. The interface *is* Claude's output.

---

## How It Shatters UI Conventions

Standard AI interfaces present a chat window. You type, it responds in text. FHIRBrush eliminates the chat box entirely. There is no prompt. There is no text field. The user's only interaction is watching a real-time FHIR event stream — simulated lab observations arriving every 15 seconds — and witnessing the canvas reorganize itself as Claude reasons. The graph is the conversation. The node positions, edge animations, color transitions from green to red, and risk cluster pulses are the language Claude speaks back to the clinician. This is what "the screen knowing what it should look like now that the AI is powerful" actually means in practice.

The 20-patient priority dot bar at the top further breaks convention: instead of a list or a table, clinical urgency is expressed as a spatial, color-coded organism — red patients cluster to the left, green to the right. A single click drills into any patient's full canvas. The UI does the triage before the clinician even reads a word.

---

## Stability of the Working Prototype

The prototype is stable across all five phases of the build:

- **Data layer** — 20 fully-formed synthetic FHIR R4 patient bundles are generated deterministically from `generate_patients.py` and served entirely from local JSON — no external API dependency during the demo, zero network risk.
- **Backend** — FastAPI with async WebSocket support streams new observations every 15 seconds. All endpoints (`/api/patients/severity`, `/api/patient/{id}/fhir`, `/ws/simulate/{id}`) are live and returning correctly shaped responses.
- **Frontend** — React Flow canvas populates from FHIR data with color-coded node types (Patient, Condition, Observation, Medication, Encounter), real-time severity thresholding (creatinine > 1.5 mg/dL → red, eGFR < 30 → red), animated edges, a live event log, and a node-type legend.
- **Fallback guarantee** — If Claude's API is unavailable, a hardcoded realistic JSON response fires automatically — the demo never breaks.
- **Patient switching** — Clicking any priority dot instantly switches the canvas, resets the WebSocket, and reloads FHIR data for the selected patient — no page reload, no state leak.

---

## How Claude Drives the Interface

Claude does not generate prose. It generates **canvas instructions** — a structured JSON payload that the frontend executes directly:

```json
{
  "highlight_nodes": ["obs-creatinine", "condition-ckd"],
  "draw_edges": [
    { "from": "obs-creatinine", "to": "condition-ckd", "label": "worsening marker" }
  ],
  "risk_cluster": ["obs-creatinine", "obs-potassium", "condition-ckd"],
  "risk_level": "high",
  "narrative": "Rising creatinine with hyperkalemia suggests acute-on-chronic kidney injury — immediate nephrology review indicated."
}
```

Every field maps to a visual mutation on the canvas: nodes pulse, edges animate, risk clusters glow, and the narrative sidebar updates with one sentence that sounds like a physician wrote it. Claude's reasoning is the choreographer; the graph is the performance.

---

## Technologies, Frameworks & Libraries

### Frontend

| Tool | Role |
|------|------|
| **React 19** | Component framework |
| **React Flow 11** | Interactive node-graph canvas — the core visual primitive |
| **TypeScript** | Type safety across all FHIR resource shapes |
| **Vite 7** | Fast dev server and bundler |
| **WebSocket (native browser API)** | Real-time FHIR observation stream |
| **CSS custom properties** | Dark clinical UI with severity color system |

### Backend

| Tool | Role |
|------|------|
| **FastAPI** | REST API + WebSocket server |
| **Uvicorn** | ASGI async server |
| **Python asyncio** | Async WebSocket simulation loop |
| **`websockets` library** | WebSocket protocol support |
| **JSON (stdlib)** | FHIR R4 bundle storage and serving |

### Data & Clinical Standards

| Tool | Role |
|------|------|
| **FHIR R4** | Healthcare interoperability standard — all patient data is valid FHIR R4 JSON, the same format used by every major US hospital system |
| **LOINC codes** | Creatinine (`2160-0`), Potassium (`2823-3`), eGFR (`33914-3`), HbA1c (`4548-4`), BUN (`3094-0`) |
| **ICD-10-CM codes** | Condition classification (E11.9, N18.3, I10, E78.5, E11.40, N18.4, I50.9, J44.1) |
| **SNOMED CT** | Supplementary condition coding |
| **Synthea-style synthetic data** | Clinically coherent patient generation via `generate_patients.py` — 20 patients, 5 clinical scenarios |

### AI

| Tool | Role |
|------|------|
| **Anthropic Claude 3.5 Sonnet** | Clinical reasoning engine — returns structured JSON that drives canvas mutations: node highlights, edge draws, risk clusters, narrative |

### Infrastructure

| Tool | Role |
|------|------|
| **Git + GitHub** | Version control with feature branch workflow |
| **Python 3.12** | Backend runtime |
| **Node.js 25 / npm** | Frontend runtime and package management |

---

## The One-Line Demo Thesis

> The same FHIR R4 format used by every major hospital system in the US means FHIRBrush could plug into a real EHR with zero changes to the data layer — Claude's reasoning is the only new ingredient, and the graph is how it speaks.


# Version 1

[FHIRBrush v1 — React Flow canvas with FHIR nodes](version1.png)

# Version 2

[FHIRBrush v2 — React Flow canvas with FHIR nodes - menu to handle and jump between 20 patients simultaneously](version2.png)


## Demo Script (3 minutes)

1. **(0:00 – 0:30)** "This patient has Type 2 Diabetes and we are watching their kidneys under pressure in real time."
2. **(0:30 – 1:30)** Walk the canvas: Patient node at center, Conditions on the left, lab Observations on the right, Medications below. The dot bar shows 20 patients — red ones are the most critical, already sorted to the left.
3. **(1:30 – 2:30)** "Watch what happens when a new creatinine result comes in." New node appears → canvas reorganizes → narrative updates → edges animate.
4. **(2:30 – 3:00)** Land the line above.


# Demo Video

https://youtu.be/yQ0zFj2tk3Q


