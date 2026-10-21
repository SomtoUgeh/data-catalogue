import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  // Forward API calls to FastAPI in development, so the browser sees one origin and no CORS setup is needed.
  server: { proxy: { '/datasets': 'http://127.0.0.1:8000' } },
  test: { environment: 'jsdom', setupFiles: './src/test-setup.ts' },
})
