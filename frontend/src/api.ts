import axios from 'axios'

// В dev — прокси Vite на localhost:8000; в проде можно задать VITE_API_URL (напр. Workers-бэкенд)
// VITE_DEMO_MODE=true (сборка --mode demo) — live-демо без backend: mock-адаптер вместо HTTP
import { mockAdapter } from './demo/mockApi'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api' })

if (import.meta.env.VITE_DEMO_MODE === 'true') {
  api.defaults.adapter = mockAdapter
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('tsekh_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('tsekh_token')
      localStorage.removeItem('tsekh_user')
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function apiError(err: unknown): string {
  const e = err as { response?: { data?: { detail?: string } }; message?: string }
  return e.response?.data?.detail ?? e.message ?? 'Неизвестная ошибка'
}

export default api
