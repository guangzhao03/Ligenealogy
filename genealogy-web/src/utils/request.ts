import axios from 'axios'
import type { ApiResponse } from '@/types'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiResponse
    if (payload && typeof payload.code === 'number' && payload.code !== 0) {
      return Promise.reject(new Error(payload.message || '请求失败'))
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    }
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : status === 404
          ? '接口不存在，请确认后端服务已重启'
          : error.message || '请求失败'
    return Promise.reject(new Error(message))
  },
)

export default request

export async function apiGet<T>(url: string, params?: Record<string, unknown>) {
  const res = await request.get<ApiResponse<T>>(url, { params })
  return res.data.data
}

export async function apiPost<T>(url: string, data?: unknown) {
  const res = await request.post<ApiResponse<T>>(url, data)
  return res.data.data
}

export async function apiPut<T>(url: string, data?: unknown) {
  const res = await request.put<ApiResponse<T>>(url, data)
  return res.data.data
}

export async function apiDelete<T>(url: string) {
  const res = await request.delete<ApiResponse<T>>(url)
  return res.data.data
}
