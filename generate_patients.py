#!/usr/bin/env python3
"""
Generates 20 realistic synthetic FHIR R4 patient bundles and saves them to
synthetic_patients.json. Also prints a summary table.

Patient mix:
  - Patients 1-5:  Diabetes + CKD (our core demo scenario, richest data)
  - Patients 6-9:  Diabetes only
  - Patients 10-12: CKD only
  - Patients 13-15: Heart failure + hypertension
  - Patients 16-18: COPD + asthma
  - Patients 19-20: Healthy (minimal data, for contrast)

Run: python generate_patients.py
Output: synthetic_patients.json
"""

import json
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

# ── helpers ─────────────────────────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())

def date_str(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def datetime_str(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

def ref(resource_type: str, rid: str) -> dict:
    return {"reference": f"{resource_type}/{rid}"}

# ── FHIR resource builders ───────────────────────────────────────────────────

def make_patient(pid: str, first: str, last: str, dob: str, gender: str) -> dict:
    return {
        "resourceType": "Patient",
        "id": pid,
        "name": [{"use": "official", "family": last, "given": [first]}],
        "gender": gender,
        "birthDate": dob,
        "active": True,
    }


def make_condition(cid: str, pid: str, code: str, system: str, display: str,
                   onset_days_ago: int, clinical_status: str = "active") -> dict:
    return {
        "resourceType": "Condition",
        "id": cid,
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": clinical_status}]
        },
        "code": {
            "coding": [{"system": system, "code": code, "display": display}],
            "text": display,
        },
        "subject": ref("Patient", pid),
        "onsetDateTime": date_str(onset_days_ago),
    }


def make_observation(oid: str, pid: str, loinc: str, display: str,
                     value: float, unit: str, unit_code: str,
                     days_ago: int, category: str = "laboratory") -> dict:
    return {
        "resourceType": "Observation",
        "id": oid,
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                   "code": category}]}],
        "code": {
            "coding": [{"system": "http://loinc.org", "code": loinc, "display": display}],
            "text": display,
        },
        "subject": ref("Patient", pid),
        "effectiveDateTime": datetime_str(days_ago),
        "valueQuantity": {
            "value": round(value, 2),
            "unit": unit,
            "system": "http://unitsofmeasure.org",
            "code": unit_code,
        },
    }


def make_med_request(mid: str, pid: str, rxnorm: str, med_name: str,
                     dose_text: str, authored_days_ago: int) -> dict:
    return {
        "resourceType": "MedicationRequest",
        "id": mid,
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": rxnorm, "display": med_name}],
            "text": med_name,
        },
        "subject": ref("Patient", pid),
        "authoredOn": date_str(authored_days_ago),
        "dosageInstruction": [{"text": dose_text}],
    }


def make_encounter(eid: str, pid: str, enc_type: str, days_ago: int,
                   duration_hours: int = 2) -> dict:
    start = datetime.now() - timedelta(days=days_ago)
    end = start + timedelta(hours=duration_hours)
    return {
        "resourceType": "Encounter",
        "id": eid,
        "status": "finished",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                  "code": "AMB", "display": "ambulatory"},
        "type": [{"coding": [{"display": enc_type}], "text": enc_type}],
        "subject": ref("Patient", pid),
        "period": {
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }


# ── patient scenario templates ───────────────────────────────────────────────

PROFILES = [
    # (first, last, dob, gender, scenario_label)
    ("James",    "Morrison",  "1958-03-14", "male",   "DM2+CKD"),
    ("Patricia", "Chen",      "1963-07-22", "female", "DM2+CKD"),
    ("Robert",   "Williams",  "1955-11-05", "male",   "DM2+CKD"),
    ("Linda",    "Patel",     "1960-09-30", "female", "DM2+CKD"),
    ("David",    "Okafor",    "1952-04-18", "male",   "DM2+CKD"),
    ("Susan",    "Martinez",  "1970-02-27", "female", "DM2"),
    ("Thomas",   "Johnson",   "1968-08-15", "male",   "DM2"),
    ("Karen",    "Thompson",  "1975-12-03", "female", "DM2"),
    ("Michael",  "Garcia",    "1965-06-20", "male",   "DM2"),
    ("Nancy",    "Brown",     "1957-01-09", "female", "CKD"),
    ("Charles",  "Lee",       "1953-05-25", "male",   "CKD"),
    ("Betty",    "Wilson",    "1961-10-14", "female", "CKD"),
    ("Joseph",   "Taylor",    "1949-03-08", "male",   "HeartFailure"),
    ("Sandra",   "Anderson",  "1956-07-19", "female", "HeartFailure"),
    ("Daniel",   "Jackson",   "1967-11-28", "male",   "HeartFailure"),
    ("Dorothy",  "White",     "1972-04-02", "female", "COPD"),
    ("Mark",     "Harris",    "1962-09-16", "male",   "COPD"),
    ("Lisa",     "Martin",    "1978-01-30", "female", "COPD"),
    ("Paul",     "Thompson",  "1985-06-11", "male",   "Healthy"),
    ("Barbara",  "Clark",     "1990-08-24", "female", "Healthy"),
]

# Creatinine trajectory for DM2+CKD demo patients: rising over time
CREATININE_SERIES = [0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.55, 1.7, 1.85, 2.0,
                     2.15, 2.3, 2.5, 2.7, 2.9]
POTASSIUM_SERIES  = [4.0, 4.1, 4.2, 4.3, 4.5, 4.7, 4.9, 5.1, 5.3, 5.5,
                     5.6, 5.7, 5.8, 5.9, 6.0]
EGFR_SERIES       = [72, 68, 64, 60, 56, 52, 47, 42, 37, 32, 28, 24, 20, 17, 14]
HBA1C_SERIES      = [7.2, 7.5, 7.8, 8.1, 8.4, 8.7, 9.0, 9.2, 9.4, 9.6]
BUN_SERIES        = [18, 20, 22, 25, 28, 32, 36, 40, 45, 50, 56, 62, 68, 75, 82]


def build_dm2_ckd_bundle(pid: str, profile: tuple, richness: int) -> list[dict]:
    """richness 1-5: controls how many observations/encounters are generated."""
    first, last, dob, gender, _ = profile
    resources = [make_patient(pid, first, last, dob, gender)]

    # Conditions
    resources.append(make_condition(uid(), pid, "E11.9",
        "http://hl7.org/fhir/sid/icd-10-cm",
        "Type 2 diabetes mellitus without complications", 365 * richness))
    resources.append(make_condition(uid(), pid, "N18.3",
        "http://hl7.org/fhir/sid/icd-10-cm",
        "Chronic kidney disease, stage 3", 365 * (richness - 1) + 180))
    resources.append(make_condition(uid(), pid, "I10",
        "http://hl7.org/fhir/sid/icd-10-cm",
        "Essential (primary) hypertension", 365 * richness + 90))
    if richness >= 3:
        resources.append(make_condition(uid(), pid, "E78.5",
            "http://hl7.org/fhir/sid/icd-10-cm",
            "Hyperlipidemia, unspecified", 365 * 2))
    if richness >= 4:
        resources.append(make_condition(uid(), pid, "E11.40",
            "http://hl7.org/fhir/sid/icd-10-cm",
            "Type 2 diabetes mellitus with diabetic neuropathy", 180))

    # Observations — lab series over time
    n_labs = 5 + richness * 2
    for i in range(min(n_labs, len(CREATININE_SERIES))):
        days = 15 * (n_labs - i)
        resources.append(make_observation(uid(), pid, "2160-0", "Creatinine [Mass/volume] in Serum",
            CREATININE_SERIES[i] + random.uniform(-0.05, 0.05), "mg/dL", "mg/dL", days))
        resources.append(make_observation(uid(), pid, "2823-3", "Potassium [Moles/volume] in Serum",
            POTASSIUM_SERIES[i] + random.uniform(-0.1, 0.1), "mEq/L", "meq/L", days))
        resources.append(make_observation(uid(), pid, "33914-3", "eGFR",
            EGFR_SERIES[i] + random.uniform(-2, 2), "mL/min/1.73m2", "mL/min/{1.73_m2}", days))
        if i % 2 == 0:
            resources.append(make_observation(uid(), pid, "4548-4", "Hemoglobin A1c/Hemoglobin.total",
                HBA1C_SERIES[min(i // 2, len(HBA1C_SERIES)-1)] + random.uniform(-0.1, 0.1), "%", "%", days))
        resources.append(make_observation(uid(), pid, "3094-0", "Blood Urea Nitrogen",
            BUN_SERIES[i] + random.uniform(-2, 2), "mg/dL", "mg/dL", days))

    # Vital signs
    for i in range(richness * 2):
        days = 15 * (richness * 2 - i)
        resources.append(make_observation(uid(), pid, "55284-4", "Blood pressure systolic and diastolic",
            random.uniform(135, 165), "mmHg", "mm[Hg]", days, "vital-signs"))
        resources.append(make_observation(uid(), pid, "8867-4", "Heart rate",
            random.uniform(68, 88), "beats/min", "/min", days, "vital-signs"))

    # Medications
    resources.append(make_med_request(uid(), pid, "860975", "Metformin 500mg", "500mg twice daily", 365))
    resources.append(make_med_request(uid(), pid, "29046", "Lisinopril 10mg", "10mg once daily", 300))
    resources.append(make_med_request(uid(), pid, "197361", "Atorvastatin 40mg", "40mg at bedtime", 280))
    if richness >= 2:
        resources.append(make_med_request(uid(), pid, "977424", "Insulin glargine 20 units",
            "20 units subcutaneously at bedtime", 180))
    if richness >= 3:
        resources.append(make_med_request(uid(), pid, "392464", "Furosemide 20mg", "20mg once daily", 90))
        resources.append(make_med_request(uid(), pid, "206764", "Amlodipine 5mg", "5mg once daily", 120))
    if richness >= 4:
        resources.append(make_med_request(uid(), pid, "310429", "Sevelamer 800mg",
            "800mg three times daily with meals", 60))

    # Encounters
    enc_types = ["Outpatient nephrology follow-up", "Primary care diabetes management",
                 "Emergency department visit", "Lab review telemedicine", "Annual physical"]
    for i in range(richness * 2):
        days = 30 * (richness * 2 - i)
        resources.append(make_encounter(uid(), pid, enc_types[i % len(enc_types)], days))

    return resources


def build_dm2_bundle(pid: str, profile: tuple) -> list[dict]:
    first, last, dob, gender, _ = profile
    resources = [make_patient(pid, first, last, dob, gender)]
    resources.append(make_condition(uid(), pid, "E11.9",
        "http://hl7.org/fhir/sid/icd-10-cm", "Type 2 diabetes mellitus", 730))
    resources.append(make_condition(uid(), pid, "I10",
        "http://hl7.org/fhir/sid/icd-10-cm", "Essential hypertension", 900))
    for i in range(6):
        days = 90 * (6 - i)
        resources.append(make_observation(uid(), pid, "4548-4", "Hemoglobin A1c",
            7.0 + i * 0.3 + random.uniform(-0.2, 0.2), "%", "%", days))
        resources.append(make_observation(uid(), pid, "2345-7", "Glucose [Mass/volume] in Serum",
            120 + i * 10 + random.uniform(-5, 5), "mg/dL", "mg/dL", days))
    resources.append(make_med_request(uid(), pid, "860975", "Metformin 1000mg", "1000mg twice daily", 730))
    resources.append(make_med_request(uid(), pid, "29046", "Lisinopril 5mg", "5mg once daily", 600))
    for i in range(4):
        resources.append(make_encounter(uid(), pid, "Diabetes follow-up", 90 * (4 - i)))
    return resources


def build_ckd_bundle(pid: str, profile: tuple) -> list[dict]:
    first, last, dob, gender, _ = profile
    resources = [make_patient(pid, first, last, dob, gender)]
    resources.append(make_condition(uid(), pid, "N18.4",
        "http://hl7.org/fhir/sid/icd-10-cm", "Chronic kidney disease, stage 4", 500))
    resources.append(make_condition(uid(), pid, "I10",
        "http://hl7.org/fhir/sid/icd-10-cm", "Essential hypertension", 700))
    for i in range(8):
        days = 45 * (8 - i)
        resources.append(make_observation(uid(), pid, "2160-0", "Creatinine",
            1.8 + i * 0.2 + random.uniform(-0.05, 0.05), "mg/dL", "mg/dL", days))
        resources.append(make_observation(uid(), pid, "33914-3", "eGFR",
            38 - i * 3 + random.uniform(-1, 1), "mL/min/1.73m2", "mL/min/{1.73_m2}", days))
    resources.append(make_med_request(uid(), pid, "29046", "Lisinopril 20mg", "20mg once daily", 500))
    resources.append(make_med_request(uid(), pid, "392464", "Furosemide 40mg", "40mg once daily", 300))
    for i in range(5):
        resources.append(make_encounter(uid(), pid, "Nephrology follow-up", 60 * (5 - i)))
    return resources


def build_hf_bundle(pid: str, profile: tuple) -> list[dict]:
    first, last, dob, gender, _ = profile
    resources = [make_patient(pid, first, last, dob, gender)]
    resources.append(make_condition(uid(), pid, "I50.9",
        "http://hl7.org/fhir/sid/icd-10-cm", "Heart failure, unspecified", 400))
    resources.append(make_condition(uid(), pid, "I10",
        "http://hl7.org/fhir/sid/icd-10-cm", "Essential hypertension", 600))
    for i in range(6):
        days = 60 * (6 - i)
        resources.append(make_observation(uid(), pid, "10230-1", "Left ventricular Ejection fraction",
            35 + i * 2 + random.uniform(-1, 1), "%", "%", days))
        resources.append(make_observation(uid(), pid, "33762-6", "NT-proBNP",
            1200 - i * 80 + random.uniform(-50, 50), "pg/mL", "pg/mL", days))
    resources.append(make_med_request(uid(), pid, "203160", "Carvedilol 25mg", "25mg twice daily", 400))
    resources.append(make_med_request(uid(), pid, "392464", "Furosemide 40mg", "40mg once daily", 350))
    resources.append(make_med_request(uid(), pid, "29046", "Lisinopril 10mg", "10mg once daily", 380))
    for i in range(4):
        resources.append(make_encounter(uid(), pid, "Cardiology follow-up", 75 * (4 - i)))
    return resources


def build_copd_bundle(pid: str, profile: tuple) -> list[dict]:
    first, last, dob, gender, _ = profile
    resources = [make_patient(pid, first, last, dob, gender)]
    resources.append(make_condition(uid(), pid, "J44.1",
        "http://hl7.org/fhir/sid/icd-10-cm", "COPD with acute exacerbation", 800))
    resources.append(make_condition(uid(), pid, "J45.50",
        "http://hl7.org/fhir/sid/icd-10-cm", "Severe persistent asthma", 1000))
    for i in range(5):
        days = 60 * (5 - i)
        resources.append(make_observation(uid(), pid, "19926-5", "FEV1 % predicted",
            55 - i * 2 + random.uniform(-2, 2), "%", "%", days))
        resources.append(make_observation(uid(), pid, "59408-5", "Oxygen saturation",
            94 + random.uniform(-1, 1), "%", "%", days, "vital-signs"))
    resources.append(make_med_request(uid(), pid, "746763", "Tiotropium 18mcg inhaler",
        "1 puff inhaled once daily", 800))
    resources.append(make_med_request(uid(), pid, "2108233", "Fluticasone/salmeterol inhaler",
        "2 puffs twice daily", 600))
    for i in range(4):
        resources.append(make_encounter(uid(), pid, "Pulmonology follow-up", 70 * (4 - i)))
    return resources


def build_healthy_bundle(pid: str, profile: tuple) -> list[dict]:
    first, last, dob, gender, _ = profile
    resources = [make_patient(pid, first, last, dob, gender)]
    resources.append(make_observation(uid(), pid, "4548-4", "Hemoglobin A1c",
        5.2 + random.uniform(-0.1, 0.1), "%", "%", 180))
    resources.append(make_observation(uid(), pid, "2160-0", "Creatinine",
        0.9 + random.uniform(-0.05, 0.05), "mg/dL", "mg/dL", 180))
    resources.append(make_observation(uid(), pid, "55284-4", "Blood pressure",
        118 + random.uniform(-5, 5), "mmHg", "mm[Hg]", 180, "vital-signs"))
    resources.append(make_encounter(uid(), pid, "Annual wellness visit", 180))
    return resources


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    all_patients = []
    summary_rows = []

    for i, profile in enumerate(PROFILES):
        pid = f"synth-{i+1:03}"
        scenario = profile[4]

        if scenario == "DM2+CKD":
            richness = 5 - i          # patients 0-4, richness 5,4,3,2,1
            resources = build_dm2_ckd_bundle(pid, profile, richness)
        elif scenario == "DM2":
            resources = build_dm2_bundle(pid, profile)
        elif scenario == "CKD":
            resources = build_ckd_bundle(pid, profile)
        elif scenario == "HeartFailure":
            resources = build_hf_bundle(pid, profile)
        elif scenario == "COPD":
            resources = build_copd_bundle(pid, profile)
        else:
            resources = build_healthy_bundle(pid, profile)

        counts = {t: 0 for t in ("Condition", "Observation", "MedicationRequest", "Encounter")}
        for r in resources:
            t = r["resourceType"]
            if t in counts:
                counts[t] += 1

        score = counts["Observation"]*2 + counts["Condition"]*2 + counts["MedicationRequest"] + counts["Encounter"]

        bundle = {
            "resourceType": "Bundle",
            "id": f"bundle-{pid}",
            "type": "collection",
            "entry": [{"resource": r} for r in resources],
        }
        all_patients.append(bundle)
        summary_rows.append({
            "rank": i + 1,
            "id": pid,
            "name": f"{profile[0]} {profile[1]}",
            "scenario": scenario,
            "conditions": counts["Condition"],
            "observations": counts["Observation"],
            "medications": counts["MedicationRequest"],
            "encounters": counts["Encounter"],
            "score": score,
        })

    # Save JSON
    output = {"patients": all_patients}
    with open("synthetic_patients.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Saved synthetic_patients.json\n")

    # Print summary table
    print(f"{'#':<4} {'Patient ID':<12} {'Name':<22} {'Scenario':<14} "
          f"{'Cond':<6} {'Obs':<6} {'Meds':<6} {'Enc':<6} {'Score'}")
    print("-" * 88)
    for r in summary_rows:
        print(f"{r['rank']:<4} {r['id']:<12} {r['name']:<22} {r['scenario']:<14} "
              f"{r['conditions']:<6} {r['observations']:<6} {r['medications']:<6} "
              f"{r['encounters']:<6} {r['score']}")
    print("-" * 88)
    print(f"\nDemo patient: synth-001 ({PROFILES[0][0]} {PROFILES[0][1]}) — richest DM2+CKD data")
    print("All patients ready. Update brief.md with patient ID: synth-001")


if __name__ == "__main__":
    main()
