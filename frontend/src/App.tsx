import { useCallback, useEffect, useRef, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from 'reactflow'
import 'reactflow/dist/style.css'
import './App.css'
import { fhirToGraph, simObsToNode } from './fhirToNodes'
import type { FhirBundle, FhirObservation } from './types'
import PatientDots, { type PatientSeverity } from './PatientDots'
import Legend from './Legend'

const API = 'http://localhost:8000'
const WS  = 'ws://localhost:8000'
const DEFAULT_PID = 'synth-001'

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([])
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  const [eventLog, setEventLog] = useState<string[]>([])
  const [activePid, setActivePid] = useState(DEFAULT_PID)
  const [severityList, setSeverityList] = useState<PatientSeverity[]>([])
  const [activePatientName, setActivePatientName] = useState('James Morrison')
  const existingNodeIds = useRef<Set<string>>(new Set())
  const wsRef = useRef<WebSocket | null>(null)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  const log = (msg: string) =>
    setEventLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 49)])

  // ── health check ──────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API}/api/health`)
      .then((r) => r.json())
      .then((d) => setBackendStatus(d.status === 'ok' ? 'connected' : 'disconnected'))
      .catch(() => setBackendStatus('disconnected'))
  }, [])

  // ── load severity list (once, on connect) ────────────────────────────────
  useEffect(() => {
    if (backendStatus !== 'connected') return
    fetch(`${API}/api/patients/severity`)
      .then((r) => r.json())
      .then((data: PatientSeverity[]) => setSeverityList(data))
      .catch(() => log('Could not load severity list'))
  }, [backendStatus])

  // ── load FHIR data for active patient ────────────────────────────────────
  useEffect(() => {
    if (backendStatus !== 'connected') return

    // Reset canvas
    setNodes([])
    setEdges([])
    existingNodeIds.current = new Set()

    const name = severityList.find((p) => p.id === activePid)?.name ?? activePid
    setActivePatientName(name)
    log(`Loading patient ${name} (${activePid})…`)

    fetch(`${API}/api/patient/${activePid}/fhir`)
      .then((r) => r.json())
      .then((bundle: FhirBundle) => {
        const { nodes: n, edges: e } = fhirToGraph(bundle)
        n.forEach((node) => existingNodeIds.current.add(node.id))
        setNodes(n)
        setEdges(e)
        log(
          `Loaded ${bundle.conditions.length} conditions, ` +
          `${bundle.observations.length} obs, ` +
          `${bundle.medications.length} meds, ` +
          `${bundle.encounters.length} encounters`,
        )
      })
      .catch((err) => log(`Error loading FHIR: ${err}`))
  }, [backendStatus, activePid])

  // ── WebSocket simulation — reconnects when patient changes ───────────────
  useEffect(() => {
    if (backendStatus !== 'connected') return

    // Close previous socket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    const ws = new WebSocket(`${WS}/ws/simulate/${activePid}`)
    wsRef.current = ws

    ws.onopen = () => log('Simulation started — new creatinine every 15 s')

    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data)
      if (msg.type !== 'new_observation') return
      const obs: FhirObservation = msg.data
      const val = obs.valueQuantity?.value ?? '?'
      const unit = obs.valueQuantity?.unit ?? ''
      const abnormal = typeof val === 'number' && val > 1.5
      log(`🧪 NEW Creatinine: ${val} ${unit}${abnormal ? ' ⚠️ ABOVE THRESHOLD' : ''}`)

      const newNode = simObsToNode(obs)
      if (!existingNodeIds.current.has(newNode.id)) {
        existingNodeIds.current.add(newNode.id)
        setNodes((prev) => [...prev, newNode])
        setEdges((prev) => [
          ...prev,
          {
            id: `e-patient-${newNode.id}`,
            source: `patient-${activePid}`,
            target: newNode.id,
            animated: true,
            style: { stroke: '#fbbf24', strokeWidth: 2 },
          },
        ])
      }
    }

    ws.onerror = () => log('WebSocket error')
    ws.onclose = () => log('Simulation stream closed')

    return () => ws.close()
  }, [backendStatus, activePid])

  const activeSeverity = severityList.find((p) => p.id === activePid)

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>FHIRBrush</h1>
          <div className="active-patient-badge">
            {activeSeverity && (
              <span className={`severity-dot ${activeSeverity.severity}`} />
            )}
            <span className="patient-label">{activePatientName}</span>
          </div>
        </div>
        <div className="header-right">
          <span className={`backend-status ${backendStatus}`}>Backend: {backendStatus}</span>
        </div>
      </header>

      {/* Priority dot bar */}
      {severityList.length > 0 && (
        <PatientDots
          patients={severityList}
          activeId={activePid}
          onSelect={setActivePid}
        />
      )}

      <div className="main">
        <div className="flow-container">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
            fitViewOptions={{ padding: 0.15 }}
          >
            <Background />
            <Controls />
            <MiniMap
              nodeColor={(n) => (n.style?.background as string) ?? '#ccc'}
            />
          </ReactFlow>
        </div>

        <aside className="sidebar">
          <Legend />
          <h2>FHIR Event Log</h2>
          <ul className="event-log">
            {eventLog.map((entry, i) => (
              <li key={i} className={entry.includes('⚠️') ? 'alert' : ''}>
                {entry}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  )
}
