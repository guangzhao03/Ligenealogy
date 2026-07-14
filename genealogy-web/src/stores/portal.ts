import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchPublicFamily, type PublicFamilyOverview } from '@/api/public'

export const usePortalStore = defineStore('portal', () => {
  const family = ref<PublicFamilyOverview | null>(null)
  const loaded = ref(false)

  async function ensureFamily() {
    if (loaded.value && family.value) return family.value
    family.value = await fetchPublicFamily()
    loaded.value = true
    return family.value
  }

  function reset() {
    family.value = null
    loaded.value = false
  }

  return { family, loaded, ensureFamily, reset }
})
