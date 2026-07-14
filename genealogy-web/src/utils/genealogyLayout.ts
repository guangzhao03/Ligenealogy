import type { TreeEdge, TreeGraph, TreeNode } from '@/types'

export type TreeViewKind = 'patrilineal' | 'full' | 'lineage' | 'ancestors' | 'descendants'

export const NODE_WIDTH = 168
export const NODE_HEIGHT = 108
export const H_GAP = 44
export const V_GAP = 72
export const GEN_RULER_WIDTH = 80
export const ROW_PADDING_X = 160
export const FOREST_GAP = 88

const CN_NUM = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

export function toChineseGeneration(generation: number) {
  if (generation <= 10) return `第${CN_NUM[generation]}世`
  return `第${generation}世`
}

export function findSpouseOnlyNodeIds(data: TreeGraph) {
  const parentChildTargets = new Set(
    data.edges.filter((edge) => edge.relation === 'parent').map((edge) => edge.target),
  )
  const spouseOnly = new Set<string>()
  for (const edge of data.edges) {
    if (edge.relation !== 'spouse') continue
    const source = data.nodes.find((node) => node.id === edge.source)
    const target = data.nodes.find((node) => node.id === edge.target)
    if (source?.gender === 2 && !parentChildTargets.has(source.id)) {
      spouseOnly.add(source.id)
    }
    if (target?.gender === 2 && !parentChildTargets.has(target.id)) {
      spouseOnly.add(target.id)
    }
  }
  return spouseOnly
}

export function normalizeParentEdges(data: TreeGraph) {
  const nodeMap = new Map(data.nodes.map((node) => [node.id, node]))
  const childToParents = new Map<string, TreeEdge[]>()

  for (const edge of data.edges) {
    if (edge.relation !== 'parent') continue
    const list = childToParents.get(edge.target) ?? []
    list.push(edge)
    childToParents.set(edge.target, list)
  }

  const edges: TreeEdge[] = []
  for (const parentEdges of childToParents.values()) {
    const sorted = [...parentEdges].sort((a, b) => {
      const aMale = nodeMap.get(a.source)?.gender === 1 ? 0 : 1
      const bMale = nodeMap.get(b.source)?.gender === 1 ? 0 : 1
      return aMale - bMale
    })
    edges.push(sorted[0])
  }
  return edges
}

export function prepareLayoutGraph(data: TreeGraph) {
  const spouseOnlyIds = findSpouseOnlyNodeIds(data)
  const nodes = data.nodes.filter((node) => !spouseOnlyIds.has(node.id))
  const nodeIds = new Set(nodes.map((node) => node.id))
  const edges = normalizeParentEdges(data).filter(
    (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target),
  )
  return { nodes, edges }
}

export interface PositionedNode extends TreeNode {
  x: number
  y: number
}

export interface GenerationLabel {
  id: string
  generation: number
  label: string
  x: number
  y: number
  height: number
}

export interface GenerationBand {
  id: string
  generation: number
  x: number
  y: number
  width: number
  height: number
}

export interface LayoutEdge extends TreeEdge {
  id: string
  points: [number, number][]
}

export interface LayoutResult {
  nodes: PositionedNode[]
  genLabels: GenerationLabel[]
  genBands: GenerationBand[]
  edgeLines: LayoutEdge[]
  minGeneration: number
  maxGeneration: number
  width: number
  height: number
}

function sortChildren(children: string[], nodeMap: Map<string, TreeNode>) {
  return [...children].sort((a, b) => {
    const na = nodeMap.get(a)
    const nb = nodeMap.get(b)
    const aMale = na?.gender === 1 ? 0 : 1
    const bMale = nb?.gender === 1 ? 0 : 1
    if (aMale !== bMale) return aMale - bMale
    return (na?.birth_year ?? 9999) - (nb?.birth_year ?? 9999)
  })
}

function buildChildrenMap(edges: TreeEdge[], nodeMap: Map<string, TreeNode>) {
  const childrenMap = new Map<string, string[]>()
  for (const edge of edges) {
    const list = childrenMap.get(edge.source) ?? []
    list.push(edge.target)
    childrenMap.set(edge.source, list)
  }
  for (const [parentId, children] of childrenMap) {
    childrenMap.set(parentId, sortChildren(children, nodeMap))
  }
  return childrenMap
}

function findRootIds(nodes: TreeNode[], edges: TreeEdge[]) {
  const hasParent = new Set(edges.map((edge) => edge.target))
  const roots = nodes
    .filter((node) => !hasParent.has(node.id))
    .sort((a, b) => (a.generation ?? 9999) - (b.generation ?? 9999) || a.id.localeCompare(b.id))
    .map((node) => node.id)
  return roots.length ? roots : nodes.map((node) => node.id)
}

function generationY(generation: number, minGeneration: number) {
  return (generation - minGeneration) * (NODE_HEIGHT + V_GAP)
}

function layoutBottomUp(
  nodeId: string,
  leftEdge: number,
  nodeMap: Map<string, TreeNode>,
  childrenMap: Map<string, string[]>,
  positionedById: Map<string, PositionedNode>,
  minGeneration: number,
): { center: number; right: number } {
  const node = nodeMap.get(nodeId)
  if (!node) return { center: leftEdge + NODE_WIDTH / 2, right: leftEdge + NODE_WIDTH }

  const children = childrenMap.get(nodeId) ?? []
  const y = generationY(node.generation ?? minGeneration, minGeneration)

  if (!children.length) {
    const positioned = { ...node, x: leftEdge, y }
    positionedById.set(nodeId, positioned)
    return { center: leftEdge + NODE_WIDTH / 2, right: leftEdge + NODE_WIDTH }
  }

  let cursor = leftEdge
  const childCenters: number[] = []
  let maxRight = leftEdge

  for (let index = 0; index < children.length; index += 1) {
    if (index > 0) cursor += H_GAP
    const result = layoutBottomUp(
      children[index],
      cursor,
      nodeMap,
      childrenMap,
      positionedById,
      minGeneration,
    )
    childCenters.push(result.center)
    cursor = result.right
    maxRight = result.right
  }

  const parentCenter = (childCenters[0] + childCenters[childCenters.length - 1]) / 2
  let parentX = parentCenter - NODE_WIDTH / 2

  if (parentX < leftEdge) {
    const shift = leftEdge - parentX
    parentX = leftEdge
    shiftSubtree(children, shift, childrenMap, positionedById)
    maxRight += shift
    for (let i = 0; i < childCenters.length; i += 1) {
      childCenters[i] += shift
    }
  }

  positionedById.set(nodeId, { ...node, x: parentX, y })
  return {
    center: parentX + NODE_WIDTH / 2,
    right: Math.max(maxRight, parentX + NODE_WIDTH),
  }
}

function shiftSubtree(
  nodeIds: string[],
  dx: number,
  childrenMap: Map<string, string[]>,
  positionedById: Map<string, PositionedNode>,
) {
  for (const nodeId of nodeIds) {
    const positioned = positionedById.get(nodeId)
    if (positioned) {
      positionedById.set(nodeId, { ...positioned, x: positioned.x + dx })
    }
    shiftSubtree(childrenMap.get(nodeId) ?? [], dx, childrenMap, positionedById)
  }
}

function buildConnectorPoints(parent: PositionedNode, child: PositionedNode): [number, number][] {
  const parentCx = parent.x + NODE_WIDTH / 2
  const parentBottom = parent.y + NODE_HEIGHT
  const childCx = child.x + NODE_WIDTH / 2
  const childTop = child.y
  const midY = parentBottom + (childTop - parentBottom) / 2
  return [
    [parentCx, parentBottom],
    [parentCx, midY],
    [childCx, midY],
    [childCx, childTop],
  ]
}

export function layoutGenealogyTree(data: TreeGraph): LayoutResult {
  const { nodes, edges } = prepareLayoutGraph(data)
  if (!nodes.length) {
    return {
      nodes: [],
      genLabels: [],
      genBands: [],
      edgeLines: [],
      minGeneration: 1,
      maxGeneration: 1,
      width: 800,
      height: 600,
    }
  }

  const nodeMap = new Map(nodes.map((node) => [node.id, node]))
  const childrenMap = buildChildrenMap(edges, nodeMap)
  const generations = nodes.map((node) => node.generation ?? 1)
  const minGeneration = Math.min(...generations)
  const maxGeneration = Math.max(...generations)

  const positionedById = new Map<string, PositionedNode>()
  const rootIds = findRootIds(nodes, edges)
  let cursor = ROW_PADDING_X

  for (const rootId of rootIds) {
    const result = layoutBottomUp(
      rootId,
      cursor,
      nodeMap,
      childrenMap,
      positionedById,
      minGeneration,
    )
    cursor = result.right + FOREST_GAP
  }

  const positionedNodes = [...positionedById.values()].sort(
    (a, b) => (a.generation ?? 0) - (b.generation ?? 0) || a.x - b.x,
  )

  let maxX = ROW_PADDING_X
  for (const node of positionedNodes) {
    maxX = Math.max(maxX, node.x + NODE_WIDTH)
  }

  const contentWidth = maxX + ROW_PADDING_X
  const rowHeight = NODE_HEIGHT + V_GAP

  const genLabels: GenerationLabel[] = []
  const genBands: GenerationBand[] = []
  for (let generation = minGeneration; generation <= maxGeneration; generation += 1) {
    const y = generationY(generation, minGeneration)
    genLabels.push({
      id: `__gen_${generation}`,
      generation,
      label: toChineseGeneration(generation),
      x: 16,
      y: y + NODE_HEIGHT / 2 - 18,
      height: NODE_HEIGHT,
    })
    genBands.push({
      id: `__band_${generation}`,
      generation,
      x: GEN_RULER_WIDTH,
      y: y - V_GAP / 2,
      width: contentWidth,
      height: rowHeight,
    })
  }

  const edgeLines: LayoutEdge[] = edges
    .map((edge) => {
      const parent = positionedById.get(edge.source)
      const child = positionedById.get(edge.target)
      if (!parent || !child) return null
      return {
        ...edge,
        id: `${edge.source}-${edge.target}-parent`,
        points: buildConnectorPoints(parent, child),
      }
    })
    .filter((edge): edge is LayoutEdge => edge != null)

  const height = (maxGeneration - minGeneration + 1) * rowHeight + V_GAP
  return {
    nodes: positionedNodes,
    genLabels,
    genBands,
    edgeLines,
    minGeneration,
    maxGeneration,
    width: contentWidth,
    height,
  }
}

export function buildNodeLabel(node: TreeNode) {
  const lines: string[] = []
  const genderMark = node.gender === 1 ? '♂' : node.gender === 2 ? '♀' : ''
  lines.push(`${genderMark} ${node.label}`.trim())
  const meta: string[] = []
  if (node.birth_year) meta.push(String(node.birth_year))
  if (node.generation != null) meta.push(`第${node.generation}世`)
  if (meta.length) lines.push(meta.join(' · '))
  if (node.spouse_name && node.gender === 1) {
    const spouse = node.spouse_nickname
      ? `${node.spouse_name}（${node.spouse_nickname}）`
      : node.spouse_name
    lines.push(`配 ${spouse}`)
  }
  return lines.join('\n')
}

export function collectLineagePath(data: TreeGraph, nodeId: string) {
  const parentMap = new Map<string, string>()
  const childrenMap = new Map<string, string[]>()
  for (const edge of normalizeParentEdges(data)) {
    parentMap.set(edge.target, edge.source)
    const children = childrenMap.get(edge.source) ?? []
    children.push(edge.target)
    childrenMap.set(edge.source, children)
  }

  const nodeIds = new Set<string>([nodeId])
  const edgeIds = new Set<string>()

  let current = nodeId
  while (parentMap.has(current)) {
    const parent = parentMap.get(current)!
    nodeIds.add(parent)
    edgeIds.add(`${parent}-${current}-parent`)
    current = parent
  }

  const queue = [nodeId]
  while (queue.length) {
    const parent = queue.shift()!
    for (const child of childrenMap.get(parent) ?? []) {
      nodeIds.add(child)
      edgeIds.add(`${parent}-${child}-parent`)
      queue.push(child)
    }
  }

  return { nodeIds, edgeIds }
}

export function collectAncestorPath(data: TreeGraph, nodeId: string) {
  const parentMap = new Map<string, string>()
  for (const edge of normalizeParentEdges(data)) {
    parentMap.set(edge.target, edge.source)
  }
  const nodeIds = new Set<string>([nodeId])
  const edgeIds = new Set<string>()
  let current = nodeId
  while (parentMap.has(current)) {
    const parent = parentMap.get(current)!
    nodeIds.add(parent)
    edgeIds.add(`${parent}-${current}-parent`)
    current = parent
  }
  return { nodeIds, edgeIds }
}

export function collectDescendantPath(data: TreeGraph, nodeId: string) {
  const childrenMap = new Map<string, string[]>()
  for (const edge of normalizeParentEdges(data)) {
    const children = childrenMap.get(edge.source) ?? []
    children.push(edge.target)
    childrenMap.set(edge.source, children)
  }
  const nodeIds = new Set<string>([nodeId])
  const edgeIds = new Set<string>()
  const queue = [nodeId]
  while (queue.length) {
    const parent = queue.shift()!
    for (const child of childrenMap.get(parent) ?? []) {
      nodeIds.add(child)
      edgeIds.add(`${parent}-${child}-parent`)
      queue.push(child)
    }
  }
  return { nodeIds, edgeIds }
}
