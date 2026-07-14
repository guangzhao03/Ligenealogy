import { apiGet, apiPost } from '@/utils/request'
import type { UserInfo } from '@/types'

export function register(data: {
  username: string
  password: string
  nickname?: string
}) {
  return apiPost<UserInfo>('/api/auth/register', data)
}

export function login(data: { username: string; password: string }) {
  return apiPost<{ access_token: string; token_type: string }>('/api/auth/login', data)
}

export function getMe() {
  return apiGet<UserInfo>('/api/auth/me')
}
