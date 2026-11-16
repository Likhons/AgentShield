import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: the Python API runs separately (uvicorn webapi.app:build_app --factory --port 8000).
// The proxy keeps the browser on one origin, the same way the Vercel rewrite will in production.
const API = process.env.AGENTSHIELD_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': API,
      '/v1': API,
      '/health': API,
    },
  },
})
