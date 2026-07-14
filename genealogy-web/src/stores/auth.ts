import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getMe, login as loginApi } from '@/api/auth'
import type { UserInfo } from '@/types'

const TOKEN_KEY = 'genealogy_token'

const ROLE_RANK: Record<string, number> = {
  member: 1,
  editor: 2,
  admin: 3,
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<UserInfo | null>(null)

  const role = computed(() => user.value?.role ?? null)
  const isAdmin = computed(() => role.value === 'admin')
  const isEditor = computed(() => ROLE_RANK[role.value ?? ''] >= ROLE_RANK.editor)
  const canAccessAdmin = computed(() => isAdmin.value)

  function homePathAfterLogin() {
    return canAccessAdmin.value ? '/families' : '/portal'
  }

  async function login(username: string, password: string) {
    const data = await loginApi({ username, password })
    token.value = data.access_token
    localStorage.setItem(TOKEN_KEY, data.access_token)
    await fetchProfile()
  }

  async function fetchProfile() {
    if (!token.value) return
    user.value = await getMe()
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return {
    token,
    user,
    role,
    isAdmin,
    isEditor,
    canAccessAdmin,
    homePathAfterLogin,
    login,
    fetchProfile,
    logout,
  }
})
