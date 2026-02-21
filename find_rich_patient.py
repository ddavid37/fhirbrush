#!/usr/bin/env python3
"""
Find a patient on HAPI FHIR public server with rich data for FHIRBrush Phase 1.
Fetches 20 patients, counts Conditions, Observations, MedicationRequests, and Encounters,
then prints a ranked summary so you can pick the best patient ID.
"""

import requests

BASE = "https://hapi.fhir.org/baseR4"
PATIENT_COUNT = 20 # Max is 500


def get_bundle_total(url: str) -> int:
    """Fetch a search URL with _summary=count and return bundle.total, or 0 on error."""
    try:
        r = requests.get(url, params={"_summary": "count"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("total", 0) if data.get("resourceType") == "Bundle" else 0
    except Exception:
        return 0


def get_patient_ids() -> list[str]:
    """Fetch up to PATIENT_COUNT patients and return their IDs."""
    try:
        r = requests.get(
            f"{BASE}/Patient",
            params={"_count": PATIENT_COUNT},
            timeout=15,
        )
        r.raise_for_status()
        bundle = r.json()
        if bundle.get("resourceType") != "Bundle" or "entry" not in bundle:
            return []
        ids = []
        for e in bundle.get("entry", []):
            res = e.get("resource", {})
            if res.get("resourceType") == "Patient" and res.get("id"):
                ids.append(res["id"])
        return ids
    except Exception:
        return []


def main() -> None:
    print("Fetching patients from HAPI FHIR (baseR4)...")
    patient_ids = get_patient_ids()
    if not patient_ids:
        print("No patients found. Check network or server.")
        return

    print(f"Found {len(patient_ids)} patients. Counting resources per patient...\n")

    rows = []
    for i, pid in enumerate(patient_ids):
        ref = f"Patient/{pid}"
        conditions = get_bundle_total(f"{BASE}/Condition?patient={ref}")
        observations = get_bundle_total(f"{BASE}/Observation?patient={ref}")
        med_requests = get_bundle_total(f"{BASE}/MedicationRequest?subject={ref}")
        encounters = get_bundle_total(f"{BASE}/Encounter?patient={ref}")

        # Score: prioritize Observations (labs), then Conditions, then Meds/Encounters
        score = (
            observations * 2
            + conditions * 2
            + med_requests
            + encounters
        )
        rows.append(
            (score, pid, conditions, observations, med_requests, encounters)
        )

    # Rank by score descending
    rows.sort(key=lambda x: -x[0])

    print("Ranked summary (best candidates first):")
    print("-" * 72)
    print(f"{'Rank':<5} {'Patient ID':<14} {'Cond':<6} {'Obs':<6} {'Meds':<6} {'Enc':<6} {'Score':<6}")
    print("-" * 72)
    for rank, (score, pid, c, o, m, e) in enumerate(rows, 1):
        print(f"{rank:<5} {pid:<14} {c:<6} {o:<6} {m:<6} {e:<6} {score:<6}")
    print("-" * 72)
    print("\nPick a patient ID and add it to BRIEF.md for Phase 2.")


if __name__ == "__main__":
    main()
