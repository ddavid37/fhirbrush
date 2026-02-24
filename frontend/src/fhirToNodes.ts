/**
 * Converts a FHIR bundle into React Flow nodes and edges.
 * Node colors / shapes follow the contract in brief.md:
 *   Patient      → blue   (large, center)
 *   Condition    → orange
 *   Observation  → green (normal) → red (above threshold)
 *   Medication   → purple
 *   Encounter    → grey
 */
import type { Node, Edge } from 'reactflow'
import type { FhirBundle, FhirObservation } from './types'

// Alert thresholds from brief.md
const THRESHOLDS: Record<string, number> = {
  '2160-0': 1.5,   // Creatinine mg/dL
  '2823-3': 5.5,   // Potassium mEq/L
  '33914-3': 30,   // eGFR — alert if BELOW this
  '4548-4': 9.0,   // HbA1c %
  '3094-0': 40,    // BUN mg/dL
}

function loincCode(obs: FhirObservation): string {
  return obs.code?.coding?.[0]?.code ?? ''
}

function isAbnormal(obs: FhirObservation): boolean {
  const code = loincCode(obs)
  const val = obs.valueQuantity?.value
  if (val === undefined || !code) return false
  const threshold = THRESHOLDS[code]
  if (threshold === undefined) return false
  // eGFR: alert if BELOW threshold
  if (code === '33914-3') return val < threshold
  return val > threshold
}

const NODE_WIDTH = 200

export function fhirToGraph(
  bundle: FhirBundle,
  existingNodeIds: Set<string> = new Set(),
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  // ── Patient (center) ──────────────────────────────────────────────────────
  const patientId = `patient-${bundle.patient.id}`
  if (!existingNodeIds.has(patientId)) {
    const name = bundle.patient.name?.[0]
    const fullName = `${name?.given?.[0] ?? ''} ${name?.family ?? ''}`.trim()
    nodes.push({
      id: patientId,
      type: 'default',
      position: { x: 600, y: 400 },
      data: { label: `👤 ${fullName}` },
      style: {
        background: '#1d4ed8',
        color: '#fff',
        border: '2px solid #1e40af',
        borderRadius: '50%',
        width: 140,
        height: 140,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 13,
        fontWeight: 700,
      },
    })
  }

  // ── Conditions (left column) ──────────────────────────────────────────────
  bundle.conditions.forEach((c, i) => {
    const nid = `condition-${c.id}`
    if (existingNodeIds.has(nid)) return
    const label = c.code?.text ?? c.code?.coding?.[0]?.display ?? 'Condition'
    const x = 60
    const y = 80 + i * 110
    nodes.push({
      id: nid,
      type: 'default',
      position: { x, y },
      data: { label: `🔶 ${label}` },
      style: {
        background: '#ea580c',
        color: '#fff',
        border: '2px solid #c2410c',
        borderRadius: 8,
        width: NODE_WIDTH,
        fontSize: 11,
        fontWeight: 600,
      },
    })
    edges.push({
      id: `e-${patientId}-${nid}`,
      source: patientId,
      target: nid,
      style: { stroke: '#ea580c', strokeWidth: 1.5 },
    })
  })

  // ── Observations (right column — most recent 12) ──────────────────────────
  const sorted = [...bundle.observations].sort(
    (a, b) =>
      new Date(b.effectiveDateTime ?? 0).getTime() -
      new Date(a.effectiveDateTime ?? 0).getTime(),
  )
  const displayed = sorted.slice(0, 12)
  displayed.forEach((o, i) => {
    const nid = `obs-${o.id}`
    if (existingNodeIds.has(nid)) return
    const abnormal = isAbnormal(o)
    const label = o.code?.text ?? o.code?.coding?.[0]?.display ?? loincCode(o) ?? 'Observation'
    const val = o.valueQuantity ? `${o.valueQuantity.value} ${o.valueQuantity.unit}` : ''
    const col = 1000 + Math.floor(i / 6) * 220
    const row = (i % 6) * 100 + 80
    nodes.push({
      id: nid,
      type: 'default',
      position: { x: col, y: row },
      data: { label: `🧪 ${label}\n${val}` },
      style: {
        background: abnormal ? '#dc2626' : '#16a34a',
        color: '#fff',
        border: `2px solid ${abnormal ? '#b91c1c' : '#15803d'}`,
        borderRadius: '50%',
        width: 110,
        height: 110,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 10,
        fontWeight: abnormal ? 700 : 500,
        whiteSpace: 'pre-wrap',
        textAlign: 'center',
      },
    })
    edges.push({
      id: `e-${patientId}-${nid}`,
      source: patientId,
      target: nid,
      style: { stroke: abnormal ? '#dc2626' : '#16a34a', strokeWidth: 1 },
      animated: abnormal,
    })
  })

  // ── Medications (bottom) ──────────────────────────────────────────────────
  bundle.medications.forEach((m, i) => {
    const nid = `med-${m.id}`
    if (existingNodeIds.has(nid)) return
    const label = m.medicationCodeableConcept?.text ?? 'Medication'
    const dose = m.dosageInstruction?.[0]?.text ?? ''
    const x = 200 + i * 180
    const y = 780
    nodes.push({
      id: nid,
      type: 'default',
      position: { x, y },
      data: { label: `💊 ${label}\n${dose}` },
      style: {
        background: '#7c3aed',
        color: '#fff',
        border: '2px solid #6d28d9',
        borderRadius: 4,
        width: 160,
        fontSize: 10,
        whiteSpace: 'pre-wrap',
        textAlign: 'center',
      },
    })
    edges.push({
      id: `e-${patientId}-${nid}`,
      source: patientId,
      target: nid,
      style: { stroke: '#7c3aed', strokeWidth: 1 },
    })
  })

  // ── Encounters (far left, small) ──────────────────────────────────────────
  bundle.encounters.slice(0, 5).forEach((enc, i) => {
    const nid = `enc-${enc.id}`
    if (existingNodeIds.has(nid)) return
    const label = enc.type?.[0]?.text ?? 'Encounter'
    const date = enc.period?.start?.slice(0, 10) ?? ''
    const x = -200
    const y = 100 + i * 120
    nodes.push({
      id: nid,
      type: 'default',
      position: { x, y },
      data: { label: `🏥 ${label}\n${date}` },
      style: {
        background: '#6b7280',
        color: '#fff',
        border: '1px solid #4b5563',
        borderRadius: 6,
        width: 160,
        fontSize: 10,
        whiteSpace: 'pre-wrap',
        textAlign: 'center',
      },
    })
    edges.push({
      id: `e-${patientId}-${nid}`,
      source: patientId,
      target: nid,
      style: { stroke: '#6b7280', strokeWidth: 1 },
    })
  })

  return { nodes, edges }
}

/** Convert a single incoming simulated Observation into a new node. */
export function simObsToNode(obs: FhirObservation): Node {
  const nid = `obs-${obs.id}`
  const abnormal = isAbnormal(obs)
  const label = obs.code?.text ?? 'Creatinine'
  const val = obs.valueQuantity ? `${obs.valueQuantity.value} ${obs.valueQuantity.unit}` : ''
  const step = obs._step ?? 0
  return {
    id: nid,
    type: 'default',
    position: { x: 1440 + step * 20, y: 200 + (step % 5) * 80 },
    data: { label: `🔴 LIVE\n${label}\n${val}` },
    style: {
      background: abnormal ? '#dc2626' : '#16a34a',
      color: '#fff',
      border: `3px solid ${abnormal ? '#fbbf24' : '#15803d'}`,
      borderRadius: '50%',
      width: 120,
      height: 120,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 11,
      fontWeight: 700,
      whiteSpace: 'pre-wrap',
      textAlign: 'center',
      boxShadow: abnormal ? '0 0 20px #fbbf24' : 'none',
    },
  }
}
