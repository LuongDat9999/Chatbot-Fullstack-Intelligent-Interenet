import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Load environment variables
import 'dotenv/config'

// Get port from environment
const port = process.env.WEB_PORT || '5180'

// Log startup information
console.log('[Vite] Serving on http://localhost:' + port)

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: Number(port),
    strictPort: true
  },
  preview: {
    host: true,
    port: Number(port)
  }
})
