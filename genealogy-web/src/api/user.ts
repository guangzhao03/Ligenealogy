import { apiGet, apiPut } from '@/utils/request'
import type { UserInfo } from '@/types'

export function fetchUsers() {
  return apiGet<UserInfo[]>('/api/users')
}

export function updateUserRole(userId: number, role: UserInfo['role']) {
  return apiPut<UserInfo>(`/api/users/${userId}/role`, { role })
}
