export interface FhirBundle {
  patient: FhirPatient
  conditions: FhirCondition[]
  observations: FhirObservation[]
  medications: FhirMedication[]
  encounters: FhirEncounter[]
}

export interface FhirPatient {
  id: string
  name: { given: string[]; family: string }[]
  gender: string
  birthDate: string
}

export interface FhirCondition {
  id: string
  code: { text?: string; coding?: { display?: string }[] }
  onsetDateTime?: string
  clinicalStatus?: { coding: { code: string }[] }
}

export interface FhirObservation {
  id: string
  code: { text?: string; coding?: { code?: string; display?: string }[] }
  effectiveDateTime?: string
  valueQuantity?: { value: number; unit: string }
  _simulated?: boolean
  _potassium?: number
  _step?: number
}

export interface FhirMedication {
  id: string
  medicationCodeableConcept?: { text?: string }
  dosageInstruction?: { text: string }[]
  status: string
}

export interface FhirEncounter {
  id: string
  type?: { text?: string }[]
  period?: { start: string; end?: string }
  status: string
}
