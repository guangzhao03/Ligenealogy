import request from '@/utils/request'
import type { ImportResult } from '@/types'

export function importPersons(family_id: number, file: File) {
  const form = new FormData()
  form.append('family_id', String(family_id))
  form.append('file', file)
  return request.post<{ code: number; message: string; data: ImportResult }>(
    '/api/import/persons',
    form,
  )
}

export function importRelations(family_id: number, file: File) {
  const form = new FormData()
  form.append('family_id', String(family_id))
  form.append('file', file)
  return request.post<{ code: number; message: string; data: ImportResult }>(
    '/api/import/relations',
    form,
  )
}

export async function exportPersons(family_id: number) {
  const res = await request.get('/api/export/persons', {
    params: { family_id },
    responseType: 'blob',
  })
  return res.data as Blob
}

export async function exportRelations(family_id: number) {
  const res = await request.get('/api/export/relations', {
    params: { family_id },
    responseType: 'blob',
  })
  return res.data as Blob
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
