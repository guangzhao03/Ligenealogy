export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  role: 'member' | 'editor' | 'admin'
  created_at: string
  updated_at: string
}

export interface Family {
  id: number
  owner_id: number
  name: string
  description: string | null
  origin_place: string | null
  created_at: string
  updated_at: string
}

export interface Person {
  id: number
  family_id: number
  name: string
  nickname: string
  gender: number
  generation: number | null
  birth_year: number | null
  birth_date: string | null
  death_date: string | null
  birthplace: string | null
  phone: string | null
  address: string | null
  biography: string | null
  remark: string | null
  is_alive: number
  avatar_url: string | null
  created_at: string
  updated_at: string
}

export interface PersonListResult {
  total: number
  items: Person[]
}

export interface PersonRelations {
  parents: Person[]
  children: Person[]
  spouses: Person[]
  siblings: Person[]
}

export interface TreeNode {
  id: string
  label: string
  name: string
  nickname?: string | null
  birth_year?: number | null
  generation: number | null
  gender: number
  is_alive: number
  is_main_line?: boolean
  spouse_name?: string | null
  spouse_nickname?: string | null
}

export interface TreeEdge {
  source: string
  target: string
  relation: string
}

export interface TreeGraph {
  nodes: TreeNode[]
  edges: TreeEdge[]
  root_id?: string | null
  root_ids?: string[]
  is_forest?: boolean
    max_generation?: number | null
  start_generation?: number | null
  focus_person_id?: string | null
}

export interface FamilyStats {
  person_count: number
  male_count: number
  female_count: number
  min_generation: number | null
  max_generation: number | null
  generation_span: number
}

export interface ImportResult {
  success_count: number
  errors: Array<{ row: number; message: string }>
}

export type GeoPlaceType = 'distribution' | 'cemetery'

export interface GeoPlace {
  id: number
  family_id: number
  place_type: GeoPlaceType
  name: string
  longitude: number
  latitude: number
  address: string | null
  description: string | null
  related_person_id: number | null
  created_at: string
  updated_at: string
}
