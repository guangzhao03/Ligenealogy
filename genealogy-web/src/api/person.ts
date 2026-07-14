import { apiDelete, apiGet, apiPost, apiPut } from '@/utils/request'
import type { Person, PersonListResult, PersonRelations } from '@/types'

export function fetchPersons(params: {
  family_id: number
  keyword?: string
  generation?: number
  page?: number
  page_size?: number
}) {
  return apiGet<PersonListResult>('/api/persons', params)
}

export function createPerson(data: Partial<Person> & { family_id: number; name: string }) {
  return apiPost<Person>('/api/persons', data)
}

export function updatePerson(id: number, data: Partial<Person>) {
  return apiPut<Person>(`/api/persons/${id}`, data)
}

export function deletePerson(id: number) {
  return apiDelete(`/api/persons/${id}`)
}

export function fetchPersonRelations(id: number) {
  return apiGet<PersonRelations>(`/api/persons/${id}/relations`)
}

export function createRelation(data: {
  family_id: number
  from_person_id: number
  to_person_id: number
  relation_type: 'parent' | 'spouse'
}) {
  return apiPost('/api/relations', data)
}

export function deleteRelation(id: number) {
  return apiDelete(`/api/relations/${id}`)
}
