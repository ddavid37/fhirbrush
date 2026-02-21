#!/usr/bin/env python3
"""
Find a patient on HAPI FHIR public server with rich data for FHIRBrush Phase 1.
Strategy: search by condition codes (diabetes + CKD) to find patients who
actually have clinical data, then rank by total resource counts.
"""

import requests

BASE = "https://hapi.fhir.org/baseR4"

# ICD-10 and SNOMED codes for diabetes and CKD
CONDITION_CODES = [
    "E11",        # ICD-10: Type 2 Diabetes
    "E11.9",      # ICD-10: Type 2 Diabetes without complications
    "44054006",   # SNOMED: Diabetes mellitus type 2
    "709044004",  # SNOMED: CKD
    "431856006",  # SNOMED: CKD Stage 2
    "431857002",  # SNOMED: CKD Stage 3
    "431858007",  # SNOMED: CKD Stage 4
    "N18",        # ICD-10: CKD
    "N18.3",      # ICD-10: CKD Stage 3
]


def get_bundle_total(url: str) -> int:
    try:
        r = requests.get(url, params={"_summary": "count"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("total", 0)
    except Exception:
        return 0


def find_patients_with_conditions() -> set[str]:
    """Search for patients who have diabetes or CKD conditions."""
    patient_ids: set[str] = set()

    code_str = ",".join(CONDITION_CODES)
    try:
        r = requests.get(
            f"{BASE}/Condition",
            params={"code": code_str, "_count": 50},
            timeout=20,
        )
        r.raise_for_status()
        bundle = r.json()
        for entry in bundle.get("entry", []):
            ref = entry.get("resource", {}).get("subject", {}).get("reference", "")
            if ref.startswith("Patient/"):
                patient_ids.add(ref.replace("Patient/", ""))
    except Exception as e:
        print(f"Condition search failed: {e}")

    # Also try searching observations for creatinine (LOINC 2160-0) as a proxy for kidney patients
    try:
        r = requests.get(
            f"{BASE}/Observation",
            params={"code": "http://loinc.org|2160-0", "_count": 50},
            timeout=20,
        )
        r.raise_for_status()
        bundle = r.json()
        for entry in bundle.get("entry", []):
            ref = entry.get("resource", {}).get("subject", {}).get("reference", "")
            if ref.startswith("Patient/"):
                patient_ids.add(ref.replace("Patient/", ""))
    except Exception as e:
        print(f"Creatinine observation search failed: {e}")

    return patient_ids


def main() -> None:
    print("Searching HAPI FHIR for patients with diabetes/CKD conditions...")
    patient_ids = find_patients_with_conditions()

    if not patient_ids:
        print("No matching patients found. The server may be slow or have limited data.")
        return

    print(f"Found {len(patient_ids)} candidate patients. Counting resources...\n")

    rows = []
    for pid in list(patient_ids)[:30]:  # cap at 30 to avoid timeout
        ref = f"Patient/{pid}"
        conditions   = get_bundle_total(f"{BASE}/Condition?patient={ref}")
        observations = get_bundle_total(f"{BASE}/Observation?patient={ref}")
        med_requests = get_bundle_total(f"{BASE}/MedicationRequest?subject={ref}")
        encounters   = get_bundle_total(f"{BASE}/Encounter?patient={ref}")

        score = observations * 2 + conditions * 2 + med_requests + encounters
        rows.append((score, pid, conditions, observations, med_requests, encounters))

    rows.sort(key=lambda x: -x[0])

    print("Ranked summary (best candidates first):")
    print("-" * 72)
    print(f"{'Rank':<5} {'Patient ID':<14} {'Cond':<6} {'Obs':<6} {'Meds':<6} {'Enc':<6} {'Score':<6}")
    print("-" * 72)
    for rank, (score, pid, c, o, m, e) in enumerate(rows, 1):
        print(f"{rank:<5} {pid:<14} {c:<6} {o:<6} {m:<6} {e:<6} {score:<6}")
    print("-" * 72)
    print("\nPick the top-ranked patient ID and tell me — I'll update brief.md and start Phase 2.")


if __name__ == "__main__":
    main()
