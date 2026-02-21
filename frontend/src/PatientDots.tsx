/**
 * PatientDots — a row of 20 colored dots, one per patient.
 * Green = stable, Orange = at-risk, Red = critical.
 * Click a dot to switch the active patient canvas.
 */

export interface PatientSeverity {
  id: string
  name: string
  initials: string
  gender: string
  severity: 'green' | 'orange' | 'red'
  reasons: string[]
}

const COLOR: Record<string, string> = {
  red:    '#ef4444',
  orange: '#f97316',
  green:  '#22c55e',
}

const GLOW: Record<string, string> = {
  red:    '0 0 10px #ef4444aa',
  orange: '0 0 8px #f97316aa',
  green:  'none',
}

const LABEL: Record<string, string> = {
  red:    'Critical',
  orange: 'At Risk',
  green:  'Stable',
}

interface Props {
  patients: PatientSeverity[]
  activeId: string
  onSelect: (id: string) => void
}

export default function PatientDots({ patients, activeId, onSelect }: Props) {
  // Sort: red first, then orange, then green
  const sorted = [...patients].sort((a, b) => {
    const order = { red: 0, orange: 1, green: 2 }
    return order[a.severity] - order[b.severity]
  })

  const counts = {
    red:    patients.filter((p) => p.severity === 'red').length,
    orange: patients.filter((p) => p.severity === 'orange').length,
    green:  patients.filter((p) => p.severity === 'green').length,
  }

  return (
    <div className="patient-dots-bar">
      <div className="dots-legend">
        <span className="legend-item red">🔴 {counts.red} Critical</span>
        <span className="legend-item orange">🟠 {counts.orange} At Risk</span>
        <span className="legend-item green">🟢 {counts.green} Stable</span>
      </div>

      <div className="dots-row">
        {sorted.map((p) => {
          const isActive = p.id === activeId
          return (
            <div key={p.id} className="dot-wrapper">
              <button
                className={`dot ${p.severity} ${isActive ? 'active' : ''}`}
                style={{
                  background: COLOR[p.severity],
                  boxShadow: isActive
                    ? `0 0 0 3px #fff, 0 0 0 5px ${COLOR[p.severity]}`
                    : GLOW[p.severity],
                }}
                onClick={() => onSelect(p.id)}
                title={`${p.name} — ${LABEL[p.severity]}`}
              >
                {p.initials}
              </button>
              <div className="dot-tooltip">
                <strong>{p.name}</strong>
                <span className={`tooltip-severity ${p.severity}`}>{LABEL[p.severity]}</span>
                {p.reasons.length > 0 && (
                  <ul>
                    {p.reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                )}
                <em>Click to open patient</em>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
