import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

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
