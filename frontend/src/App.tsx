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

const API  = 'http://localhost:8000'
const WS   = 'ws://localhost:8000'
const PID  = 'synth-001'

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([])
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  const [eventLog, setEventLog] = useState<string[]>([])
  const existingNodeIds = useRef<Set<string>>(new Set())

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

  // ── load FHIR data ────────────────────────────────────────────────────────
  useEffect(() => {
    if (backendStatus !== 'connected') return
    log(`Loading patient ${PID}…`)
    fetch(`${API}/api/patient/${PID}/fhir`)
      .then((r) => r.json())
      .then((bundle: FhirBundle) => {
        const { nodes: n, edges: e } = fhirToGraph(bundle)
        n.forEach((node) => existingNodeIds.current.add(node.id))
        setNodes(n)
        setEdges(e)
        log(`Loaded ${bundle.conditions.length} conditions, ${bundle.observations.length} observations, ${bundle.medications.length} medications, ${bundle.encounters.length} encounters`)
      })
      .catch((err) => log(`Error loading FHIR: ${err}`))
  }, [backendStatus])

  // ── WebSocket simulation ──────────────────────────────────────────────────
  useEffect(() => {
    if (backendStatus !== 'connected') return
    const ws = new WebSocket(`${WS}/ws/simulate/${PID}`)

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
            source: `patient-${PID}`,
            target: newNode.id,
            animated: true,
            style: { stroke: '#fbbf24', strokeWidth: 2 },
          },
        ])
      }
    }

    ws.onerror = () => log('WebSocket error — is backend running?')
    ws.onclose = () => log('Simulation stream closed')

    return () => ws.close()
  }, [backendStatus])

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>FHIRBrush</h1>
          <span className="patient-label">Patient: James Morrison — DM2 + CKD</span>
        </div>
        <div className="header-right">
          <span className={`backend-status ${backendStatus}`}>Backend: {backendStatus}</span>
        </div>
      </header>

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
              nodeColor={(n) => {
                const bg = (n.style?.background as string) ?? '#ccc'
                return bg
              }}
            />
          </ReactFlow>
        </div>

        <aside className="sidebar">
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
