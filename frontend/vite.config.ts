import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: [
      'reactflow',
      '@reactflow/core',
      '@reactflow/controls',
      '@reactflow/minimap',
      '@reactflow/background',
    ],
  },
  ssr: {
    noExternal: ['reactflow', '@reactflow/core'],
  },
})
