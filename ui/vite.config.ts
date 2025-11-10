import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: './postcss.config.cjs',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3004,
    host: '0.0.0.0', // Listen on all interfaces (IPv4 and IPv6)
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
        // For insights endpoints, optionally proxy to Lambda API Gateway
        // Uncomment the following to use Lambda endpoints directly:
        // configure: (proxy, options) => {
        //   proxy.on('proxyReq', (proxyReq, req, res) => {
        //     if (req.url?.startsWith('/api/insights')) {
        //       // Could redirect to Lambda API Gateway URL here if needed
        //       // For now, insights go through local FastAPI backend which proxies to Lambda
        //     }
        //   })
        // }
      },
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

