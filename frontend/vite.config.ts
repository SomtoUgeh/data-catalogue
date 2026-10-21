import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import viteReact from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  resolve: {
    tsconfigPaths: true,
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  plugins: [
    tailwindcss(),
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    viteReact(),
  ],
  server: {
    port: 3000,
    host: '127.0.0.1',
    proxy: {
      '/datasets': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
