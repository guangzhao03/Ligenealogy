import { apiGet } from '@/utils/request'
import type { TreeGraph } from '@/types'

export type PersonTreeDirection = 'center' | 'ancestors' | 'descendants' | 'patrilineal'

export function fetchFullTree(family_id: number) {
  return apiGet<TreeGraph>('/api/tree/full', { family_id })
}

/** 指定人物查谱（统一接口） */
export function fetchPersonTree(params: {
  family_id: number
  person_id: number
  direction: PersonTreeDirection
  up_generations?: number
  down_generations?: number
}) {
  return apiGet<TreeGraph>('/api/tree/person', params)
}

export function fetchAncestorsTree(params: {
  family_id: number
  start_generation?: number
  max_generations?: number
  person_id?: number
}) {
  return apiGet<TreeGraph>('/api/tree/ancestors', params)
}

export function fetchDescendantsTree(params: {
  family_id: number
  start_generation?: number
  max_generations?: number
  person_id?: number
}) {
  return apiGet<TreeGraph>('/api/tree/descendants', params)
}

export function fetchPatrilinealTree(params: {
  family_id: number
  root_person_id?: number
  max_generations?: number
}) {
  return apiGet<TreeGraph>('/api/tree/patrilineal', params)
}

export function fetchLineageTree(params: {
  family_id: number
  person_id: number
  up_generations?: number
  down_generations?: number
}) {
  return apiGet<TreeGraph>('/api/tree/lineage', params)
}

function mergeTreeGraphs(
  ancestors: TreeGraph,
  descendants: TreeGraph,
  focusPersonId: number,
): TreeGraph {
  const nodeMap = new Map(ancestors.nodes.map((node) => [node.id, node]))
  for (const node of descendants.nodes) {
    nodeMap.set(node.id, node)
  }

  const edgeKeys = new Set<string>()
  const edges = [...ancestors.edges, ...descendants.edges].filter((edge) => {
    const key = `${edge.source}|${edge.target}|${edge.relation}`
    if (edgeKeys.has(key)) return false
    edgeKeys.add(key)
    return true
  })

  const generations = [...nodeMap.values()]
    .map((node) => node.generation)
    .filter((generation): generation is number => generation != null)

  return {
    nodes: [...nodeMap.values()],
    edges,
    root_id: String(focusPersonId),
    is_forest: false,
    start_generation: ancestors.start_generation ?? descendants.start_generation ?? null,
    max_generation: generations.length ? Math.max(...generations) : null,
    focus_person_id: String(focusPersonId),
  }
}

function isRouteMissingError(error: unknown): boolean {
  if (!(error instanceof Error)) return false
  const message = error.message.toLowerCase()
  return message.includes('not found') || message.includes('404') || message.includes('接口不存在')
}

/** 以人为中心：优先统一接口，兼容旧后端 */
export async function fetchCenterPersonTree(params: {
  family_id: number
  person_id: number
  start_generation?: number
  up_generations?: number
  down_generations?: number
}) {
  const personParams = {
    family_id: params.family_id,
    person_id: params.person_id,
    direction: 'center' as const,
    up_generations: params.up_generations,
    down_generations: params.down_generations,
  }

  try {
    return await fetchPersonTree(personParams)
  } catch (error) {
    if (!isRouteMissingError(error)) throw error
  }

  try {
    return await fetchLineageTree(params)
  } catch (error) {
    if (!isRouteMissingError(error)) throw error
  }

  const startGeneration = params.start_generation ?? 1
  const [ancestors, descendants] = await Promise.all([
    fetchAncestorsTree({
      family_id: params.family_id,
      person_id: params.person_id,
      start_generation: startGeneration,
      max_generations: params.up_generations ?? 5,
    }),
    fetchDescendantsTree({
      family_id: params.family_id,
      person_id: params.person_id,
      start_generation: startGeneration,
      max_generations: params.down_generations ?? 5,
    }),
  ])

  return mergeTreeGraphs(ancestors, descendants, params.person_id)
}

export function formatPersonDisplayName(person: {
  name: string
  nickname?: string | null
  birth_year?: number | null
  generation?: number | null
}) {
  const base = person.nickname ? `${person.name}（${person.nickname}）` : person.name
  const meta: string[] = []
  if (person.birth_year) meta.push(String(person.birth_year))
  if (person.generation) meta.push(`第${person.generation}代`)
  return meta.length ? `${base}\n${meta.join(' · ')}` : base
}

export function modeToDirection(
  mode: 'patrilineal' | 'lineage' | 'ancestors' | 'descendants',
): PersonTreeDirection {
  if (mode === 'lineage') return 'center'
  return mode
}
