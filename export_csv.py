"""Export synthetic_patients.json → patients_summary.csv"""
import json
import csv

with open("synthetic_patients.json") as f:
    data = json.load(f)

rows = []
for bundle in data["patients"]:
    patient = {}
    conditions, observations, medications, encounters = [], [], [], []

    for entry in bundle["entry"]:
        r = entry["resource"]
        rt = r["resourceType"]
        if rt == "Patient":
            patient = r
        elif rt == "Condition":
            conditions.append(r)
        elif rt == "Observation":
            observations.append(r)
        elif rt == "MedicationRequest":
            medications.append(r)
        elif rt == "Encounter":
            encounters.append(r)

    name = patient.get("name", [{}])[0]
    full_name = (name.get("given", [""])[0] + " " + name.get("family", "")).strip()

    rows.append({
        "patient_id":       patient.get("id"),
        "name":             full_name,
        "gender":           patient.get("gender"),
        "dob":              patient.get("birthDate"),
        "num_conditions":   len(conditions),
        "conditions":       " | ".join(c.get("code", {}).get("text", "") for c in conditions),
        "num_observations": len(observations),
        "num_medications":  len(medications),
        "medications":      " | ".join(m.get("medicationCodeableConcept", {}).get("text", "") for m in medications),
        "num_encounters":   len(encounters),
        "score":            len(observations) * 2 + len(conditions) * 2 + len(medications) + len(encounters),
    })

rows.sort(key=lambda x: -x["score"])

with open("patients_summary.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. patients_summary.csv — {len(rows)} rows.")
