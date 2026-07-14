import { apiDelete, apiGet, apiPost, apiPut } from '@/utils/request'
import type { GeoPlace, GeoPlaceType } from '@/types'

export function fetchGeoPlaces(params: { family_id: number; place_type?: GeoPlaceType }) {
  return apiGet<GeoPlace[]>('/api/geo-places', params)
}

export function createGeoPlace(data: {
  family_id: number
  place_type: GeoPlaceType
  name: string
  longitude: number
  latitude: number
  address?: string
  description?: string
  related_person_id?: number | null
}) {
  return apiPost<GeoPlace>('/api/geo-places', data)
}

export function updateGeoPlace(
  id: number,
  data: Partial<{
    place_type: GeoPlaceType
    name: string
    longitude: number
    latitude: number
    address?: string
    description?: string
    related_person_id?: number | null
  }>,
) {
  return apiPut<GeoPlace>(`/api/geo-places/${id}`, data)
}

export function deleteGeoPlace(id: number) {
  return apiDelete(`/api/geo-places/${id}`)
}
