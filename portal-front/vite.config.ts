import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // Default Vite on Windows may listen only on IPv6 (::1), which makes
    // http://127.0.0.1:<port>/ fail while http://localhost:<port>/ works.
    host: '127.0.0.1',
    port: 5173,
  },
})
