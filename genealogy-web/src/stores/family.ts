import { defineStore } from 'pinia'

import { ref } from 'vue'

import { fetchFamilies } from '@/api/family'

import type { Family } from '@/types'



const FAMILY_KEY = 'genealogy_current_family'



export const useFamilyStore = defineStore('family', () => {

  const currentFamily = ref<Family | null>(null)

  const initialized = ref(false)



  const saved = localStorage.getItem(FAMILY_KEY)

  if (saved) {

    try {

      currentFamily.value = JSON.parse(saved) as Family

    } catch {

      localStorage.removeItem(FAMILY_KEY)

    }

  }



  function setCurrentFamily(family: Family | null) {

    currentFamily.value = family

    if (family) {

      localStorage.setItem(FAMILY_KEY, JSON.stringify(family))

    } else {

      localStorage.removeItem(FAMILY_KEY)

    }

  }



  async function ensureFamilySelected() {

    const families = await fetchFamilies()

    if (currentFamily.value) {

      const matched = families.find((family) => family.id === currentFamily.value?.id)

      if (matched) {

        setCurrentFamily(matched)

        initialized.value = true

        return matched

      }

    }

    if (families.length === 1) {

      setCurrentFamily(families[0])

      initialized.value = true

      return families[0]

    }

    initialized.value = true

    return currentFamily.value

  }



  return { currentFamily, initialized, setCurrentFamily, ensureFamilySelected }

})

