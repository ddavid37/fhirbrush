export default function Legend() {
  return (
    <div className="legend">
      <span className="legend-title">Node types</span>
      <div className="legend-item">
        <span className="legend-swatch" style={{ background: '#1d4ed8', borderRadius: '50%' }} />
        Patient
      </div>
      <div className="legend-item">
        <span className="legend-swatch" style={{ background: '#ea580c' }} />
        Condition
      </div>
      <div className="legend-item">
        <span className="legend-swatch" style={{ background: '#16a34a', borderRadius: '50%' }} />
        Observation (normal)
      </div>
      <div className="legend-item">
        <span className="legend-swatch" style={{ background: '#dc2626', borderRadius: '50%' }} />
        Observation (alert)
      </div>
      <div className="legend-item">
        <span className="legend-swatch" style={{ background: '#7c3aed' }} />
        Medication
      </div>
      <div className="legend-item">
        <span className="legend-swatch" style={{ background: '#6b7280' }} />
        Encounter
      </div>
    </div>
  )
}
