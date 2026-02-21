import { useCallback, useEffect, useState } from 'react'
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

const initialNodes: Node[] = [
  { id: '1', type: 'default', position: { x: 0, y: 0 }, data: { label: 'FHIRBrush' } },
  { id: '2', type: 'default', position: { x: 200, y: 100 }, data: { label: 'Canvas' } },
]
const initialEdges: Edge[] = [{ id: 'e1-2', source: '1', target: '2' }]

const API_BASE = 'http://localhost:8000'

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [backendStatus, setBackendStatus] = useState<string>('checking…')

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === 'ok' ? 'connected' : 'unexpected'))
      .catch(() => setBackendStatus('disconnected'))
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>FHIRBrush</h1>
        <span className={`backend-status ${backendStatus}`}>Backend: {backendStatus}</span>
      </header>
      <div className="flow-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  )
}

export default App
