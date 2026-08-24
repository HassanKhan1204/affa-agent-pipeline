import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Mirrors affa-ui/nginx.conf's /api/ proxy so `npm run dev` behaves
    // the same as the dockerized UI: same-origin /api/* calls, no CORS,
    // no hardcoded backend host in the app code. Run the backend with
    // `docker compose up backend` (or `uvicorn app.main:app --reload`
    // from backend/) before starting the dev server.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
