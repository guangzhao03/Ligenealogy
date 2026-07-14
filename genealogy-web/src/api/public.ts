import { apiGet } from '@/utils/request'
import type {
  FamilyStats,
  GeoPlace,
  GeoPlaceType,
  Person,
  PersonListResult,
  PersonRelations,
  Residence,
  TreeGraph,
} from '@/types'

export interface PublicFamilyOverview {
  id: number
  name: string
  description: string | null
  origin_place: string | null
  stats: FamilyStats
}

export function fetchPublicFamily() {
  return apiGet<PublicFamilyOverview>('/api/public/family')
}

export function fetchPublicPersons(params?: {
  keyword?: string
  generation?: number
  page?: number
  page_size?: number
}) {
  return apiGet<PersonListResult>('/api/public/persons', params)
}

export function fetchPublicPerson(id: number) {
  return apiGet<Person>(`/api/public/persons/${id}`)
}

export function fetchPublicPersonRelations(id: number) {
  return apiGet<PersonRelations>(`/api/public/persons/${id}/relations`)
}

export function fetchPublicFullTree() {
  return apiGet<TreeGraph>('/api/public/tree/full')
}

export function fetchPublicPatrilinealTree(params?: {
  root_person_id?: number
  max_generations?: number
}) {
  return apiGet<TreeGraph>('/api/public/tree/patrilineal', params)
}

export function fetchPublicLineageTree(params: {
  person_id: number
  up_generations?: number
  down_generations?: number
}) {
  return apiGet<TreeGraph>('/api/public/tree/lineage', params)
}

export function fetchPublicPersonTree(params: {
  person_id: number
  direction?: 'center' | 'ancestors' | 'descendants' | 'patrilineal'
  up_generations?: number
  down_generations?: number
}) {
  return apiGet<TreeGraph>('/api/public/tree/person', params)
}

export function fetchPublicGeoPlaces(params?: { place_type?: GeoPlaceType }) {
  return apiGet<GeoPlace[]>('/api/public/geo-places', params)
}

export function fetchPublicResidences() {
  return apiGet<Residence[]>('/api/public/residences')
}
