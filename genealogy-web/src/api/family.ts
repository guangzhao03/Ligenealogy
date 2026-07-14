import { apiDelete, apiGet, apiPost, apiPut } from '@/utils/request'

import type { Family, FamilyStats } from '@/types'



export function fetchFamilies() {

  return apiGet<Family[]>('/api/families')

}



export function fetchFamilyStats(id: number) {

  return apiGet<FamilyStats>(`/api/families/${id}/stats`)

}



export function createFamily(data: {

  name: string

  description?: string

  origin_place?: string

}) {

  return apiPost<Family>('/api/families', data)

}



export function updateFamily(

  id: number,

  data: { name?: string; description?: string; origin_place?: string },

) {

  return apiPut<Family>(`/api/families/${id}`, data)

}



export function deleteFamily(id: number) {

  return apiDelete(`/api/families/${id}`)

}

