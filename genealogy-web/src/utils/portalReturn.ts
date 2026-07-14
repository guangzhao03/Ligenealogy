/** 门户「人物档案」往返上下文（sessionStorage） */

export type PortalTreeMode = 'full' | 'patrilineal' | 'lineage'

export type MapFilterType = 'all' | 'distribution' | 'cemetery' | 'residence'

export type TreeReturnContext = {
  source: 'tree'
  mode: PortalTreeMode
  personId?: number
  searchText?: string
  up?: number
  down?: number
  maxGenerations?: number
}

export type MapReturnContext = {
  source: 'map'
  filterType: MapFilterType
  searchText?: string
  selectedPlaceId?: number | null
  personId?: number
}

export type PortalReturnContext = TreeReturnContext | MapReturnContext

const STORAGE_KEY = 'portal_person_return'

export function savePortalReturn(ctx: PortalReturnContext): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ctx))
  } catch {
    /* ignore quota / private mode */
  }
}

export function readPortalReturn(): PortalReturnContext | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as PortalReturnContext
    if (parsed?.source !== 'tree' && parsed?.source !== 'map') return null
    return parsed
  } catch {
    return null
  }
}

export function clearPortalReturn(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export function buildTreeReturnQuery(ctx: TreeReturnContext, fallbackPersonId: number) {
  const personId = ctx.personId ?? fallbackPersonId
  const query: Record<string, string> = {
    mode: ctx.mode,
    person_id: String(personId),
  }
  if (ctx.mode === 'lineage') {
    if (ctx.up != null) query.up = String(ctx.up)
    if (ctx.down != null) query.down = String(ctx.down)
  }
  if (ctx.mode === 'patrilineal' && ctx.maxGenerations != null) {
    query.max_generations = String(ctx.maxGenerations)
  }
  return query
}

export function buildMapReturnQuery(ctx: MapReturnContext) {
  const query: Record<string, string> = {}
  if (ctx.filterType && ctx.filterType !== 'all') {
    query.filter = ctx.filterType
  }
  if (ctx.personId != null) {
    query.person_id = String(ctx.personId)
  }
  if (ctx.searchText?.trim()) {
    query.q = ctx.searchText.trim()
  }
  return query
}
