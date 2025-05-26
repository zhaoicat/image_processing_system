import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 从环境变量获取后端地址，默认为localhost:8000
const BACKEND_URL = process.env.VITE_BACKEND_HOST || 'http://localhost:8888'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
