<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ZoomIn, ZoomOut, FullScreen, Refresh } from '@element-plus/icons-vue'
import type { TreeGraph } from '@/types'
import {
  NODE_HEIGHT,
  NODE_WIDTH,
  buildNodeLabel,
  collectAncestorPath,
  collectDescendantPath,
  layoutGenealogyTree,
  type PositionedNode,
} from '@/utils/genealogyLayout'

const props = defineProps<{
  data: TreeGraph | null
  focusPersonId?: string | null
}>()

const stageRef = ref<HTMLDivElement>()
const focusId = ref<string | null>(null)
const pan = ref({ x: 40, y: 40 })
const zoom = ref(1)
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0, panX: 0, panY: 0 })

const GENERATION_COLORS = [
  '#1e3d2f',
  '#244636',
  '#2f5d46',
  '#3a7354',
  '#468962',
  '#529f70',
  '#5eb57e',
  '#6acb8c',
]

const layout = computed(() => {
  if (!props.data?.nodes?.length) return null
  return layoutGenealogyTree(props.data)
})

const ancestorPath = computed(() => {
  if (!props.data || !focusId.value) return { nodeIds: new Set<string>(), edgeIds: new Set<string>() }
  return collectAncestorPath(props.data, focusId.value)
})

const descendantPath = computed(() => {
  if (!props.data || !focusId.value) return { nodeIds: new Set<string>(), edgeIds: new Set<string>() }
  return collectDescendantPath(props.data, focusId.value)
})

function generationColor(generation: number | null | undefined) {
  const index = Math.max(0, (generation ?? 1) - 1) % GENERATION_COLORS.length
  return GENERATION_COLORS[index]
}

function nodeState(id: string) {
  if (!focusId.value) return { dimmed: false, focus: false, ancestor: false, descendant: false }
  const focus = id === focusId.value
  const ancestor = ancestorPath.value.nodeIds.has(id) && !focus
  const descendant = descendantPath.value.nodeIds.has(id) && !focus
  const active = ancestor || descendant || focus
  return { dimmed: !active, focus, ancestor, descendant }
}

function edgeState(id: string) {
  if (!focusId.value) return { dimmed: false, ancestor: false, descendant: false }
  const ancestor = ancestorPath.value.edgeIds.has(id)
  const descendant = descendantPath.value.edgeIds.has(id)
  return { dimmed: !ancestor && !descendant, ancestor, descendant }
}

function connectorPath(points: [number, number][]) {
  if (!points.length) return ''
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point[0]} ${point[1]}`).join(' ')
}

function cardStyle(node: PositionedNode) {
  const state = nodeState(node.id)
  const isMale = node.gender === 1
  const isFemale = node.gender === 2
  let fill = isMale ? '#e8f1f8' : isFemale ? '#fceff4' : '#fff8eb'
  let stroke = isMale ? '#3a6d8c' : isFemale ? '#b04a78' : '#7a6f62'
  let opacity = node.is_alive === 0 ? 0.85 : 1

  if (state.focus) {
    fill = '#fff7e6'
    stroke = '#d97706'
  } else if (state.ancestor) {
    stroke = '#b8860b'
  } else if (state.descendant) {
    stroke = '#2f855a'
  } else if (state.dimmed) {
    opacity = 0.22
  }

  return { fill, stroke, opacity }
}

function handleNodeClick(id: string) {
  focusId.value = focusId.value === id ? null : id
}

function fitView() {
  const stage = stageRef.value
  if (!stage || !layout.value) return
  const padding = 40
  const scaleX = (stage.clientWidth - padding * 2) / layout.value.width
  const scaleY = (stage.clientHeight - padding * 2) / layout.value.height
  // 保底缩放，避免整树适配后字号过小、发糊
  zoom.value = Math.min(1.25, Math.max(0.62, Math.min(scaleX, scaleY)))
  pan.value = {
    x: (stage.clientWidth - layout.value.width * zoom.value) / 2,
    y: padding,
  }
}

/** 仅在人物不在可视区时微调平移，不打断「适应画布」的顶对齐布局 */
function ensurePersonVisible(personId: string | null | undefined) {
  const stage = stageRef.value
  if (!stage || !layout.value || !personId) return
  const node = layout.value.nodes.find((item) => item.id === personId)
  if (!node) return
  focusId.value = personId

  const margin = 32
  const left = pan.value.x + node.x * zoom.value
  const top = pan.value.y + node.y * zoom.value
  const right = left + NODE_WIDTH * zoom.value
  const bottom = top + NODE_HEIGHT * zoom.value

  let nextX = pan.value.x
  let nextY = pan.value.y
  if (left < margin) nextX += margin - left
  if (right > stage.clientWidth - margin) nextX += stage.clientWidth - margin - right
  if (top < margin) nextY += margin - top
  if (bottom > stage.clientHeight - margin) nextY += stage.clientHeight - margin - bottom
  pan.value = { x: nextX, y: nextY }
}

function focusOnPerson(personId: string | null | undefined) {
  const stage = stageRef.value
  if (!stage || !layout.value || !personId) return
  const node = layout.value.nodes.find((item) => item.id === personId)
  if (!node) return
  focusId.value = personId
  // 定位人物时保证可读字号
  if (zoom.value < 0.85) zoom.value = 0.85
  const centerX = node.x + NODE_WIDTH / 2
  const centerY = node.y + NODE_HEIGHT / 2
  const relativeY = node.y / Math.max(layout.value.height, 1)
  const padding = 48
  // 靠近树顶的节点（如始祖）贴顶部，避免垂直居中后画面上方大片留白
  const screenY =
    relativeY < 0.22 ? padding + (NODE_HEIGHT * zoom.value) / 2 : stage.clientHeight / 2
  pan.value = {
    x: stage.clientWidth / 2 - centerX * zoom.value,
    y: screenY - centerY * zoom.value,
  }
}

function zoomBy(factor: number) {
  const stage = stageRef.value
  if (!stage) return
  const cx = stage.clientWidth / 2
  const cy = stage.clientHeight / 2
  const nextZoom = Math.min(2.5, Math.max(0.2, zoom.value * factor))
  pan.value = {
    x: cx - (cx - pan.value.x) * (nextZoom / zoom.value),
    y: cy - (cy - pan.value.y) * (nextZoom / zoom.value),
  }
  zoom.value = nextZoom
}

function onWheel(event: WheelEvent) {
  event.preventDefault()
  zoomBy(event.deltaY < 0 ? 1.08 : 0.92)
}

function onMouseDown(event: MouseEvent) {
  if ((event.target as HTMLElement).closest('.person-card')) return
  isPanning.value = true
  panStart.value = { x: event.clientX, y: event.clientY, panX: pan.value.x, panY: pan.value.y }
}

function onMouseMove(event: MouseEvent) {
  if (!isPanning.value) return
  pan.value = {
    x: panStart.value.panX + (event.clientX - panStart.value.x),
    y: panStart.value.panY + (event.clientY - panStart.value.y),
  }
}

function onMouseUp() {
  isPanning.value = false
}

function splitLabel(text: string) {
  return text.split('\n')
}

function resolveFocusId() {
  return props.focusPersonId ?? props.data?.focus_person_id ?? null
}

watch(
  () => props.data,
  () => {
    const id = resolveFocusId()
    focusId.value = id
    // 刷新/切模式：先整树顶对齐适配，再保证高亮人物可见，勿再强制居中
    fitView()
    if (id) ensurePersonVisible(id)
  },
  { deep: true },
)

watch(
  () => props.focusPersonId,
  (personId) => {
    if (personId) {
      focusId.value = personId
      focusOnPerson(personId)
    } else {
      focusId.value = null
    }
  },
)

onMounted(() => {
  fitView()
  const id = resolveFocusId()
  if (id) {
    focusId.value = id
    ensurePersonVisible(id)
  }
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<template>
  <div class="tree-shell">
    <div class="tree-toolbar">
      <span class="toolbar-tip">树形世系图 · 点击节点高亮祖先后代 · 拖拽平移 · 滚轮缩放</span>
      <div class="toolbar-actions">
        <el-button size="small" :icon="Refresh" @click="fitView">适应画布</el-button>
        <el-button size="small" :icon="ZoomIn" @click="zoomBy(1.15)">放大</el-button>
        <el-button size="small" :icon="ZoomOut" @click="zoomBy(0.87)">缩小</el-button>
        <el-button size="small" :icon="FullScreen" @click="fitView">居中</el-button>
      </div>
    </div>

    <div
      ref="stageRef"
      class="tree-stage"
      :class="{ panning: isPanning }"
      @wheel="onWheel"
      @mousedown="onMouseDown"
    >
      <div v-if="!layout?.nodes.length" class="empty-tip">暂无族谱数据，请先添加人物和关系</div>

      <svg v-else class="tree-svg" text-rendering="geometricPrecision">
        <g :transform="`translate(${pan.x}, ${pan.y}) scale(${zoom})`">
          <!-- 世代背景带 -->
          <g v-for="band in layout.genBands" :key="band.id">
            <rect
              :x="band.x"
              :y="band.y"
              :width="band.width"
              :height="band.height"
              :fill="generationColor(band.generation)"
              opacity="0.07"
              rx="4"
            />
          </g>

          <!-- 世代标尺 -->
          <g v-for="label in layout.genLabels" :key="label.id">
            <rect
              :x="label.x"
              :y="label.y"
              width="64"
              height="40"
              rx="6"
              fill="rgba(250, 246, 238, 0.98)"
              stroke="#b8a478"
              stroke-width="1.5"
            />
            <text
              :x="label.x + 32"
              :y="label.y + 26"
              text-anchor="middle"
              class="gen-label"
            >
              {{ label.label }}
            </text>
          </g>

          <!-- 父子连线（正交折线） -->
          <g v-for="edge in layout.edgeLines" :key="edge.id">
            <path
              :d="connectorPath(edge.points)"
              fill="none"
              :stroke="edgeState(edge.id).ancestor ? '#b8860b' : edgeState(edge.id).descendant ? '#2f855a' : '#6f5d48'"
              :stroke-width="edgeState(edge.id).ancestor || edgeState(edge.id).descendant ? 2.8 : 2"
              :opacity="edgeState(edge.id).dimmed ? 0.12 : 0.9"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </g>

          <!-- 人物卡片 -->
          <g
            v-for="node in layout.nodes"
            :key="node.id"
            class="person-card"
            :transform="`translate(${node.x}, ${node.y})`"
            @click.stop="handleNodeClick(node.id)"
          >
            <rect
              :width="NODE_WIDTH"
              :height="NODE_HEIGHT"
              rx="10"
              :fill="cardStyle(node).fill"
              :stroke="cardStyle(node).stroke"
              stroke-width="2.2"
              :opacity="cardStyle(node).opacity"
            />
            <rect
              :width="NODE_WIDTH"
              height="7"
              rx="10"
              :fill="generationColor(node.generation)"
              :opacity="cardStyle(node).opacity"
            />
            <text
              v-for="(line, index) in splitLabel(buildNodeLabel(node))"
              :key="`${node.id}-${index}`"
              :x="NODE_WIDTH / 2"
              :y="30 + index * 22"
              text-anchor="middle"
              :class="['card-line', index === 0 ? 'name' : 'meta']"
              :opacity="cardStyle(node).opacity"
            >
              {{ line }}
            </text>
          </g>
        </g>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.tree-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 520px;
}

.tree-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 0 4px 10px;
}

.toolbar-tip {
  font-size: 12px;
  color: var(--text-muted);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.tree-stage {
  flex: 1;
  min-height: 480px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #c8b99a;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.35), transparent 40%),
    linear-gradient(180deg, rgba(30, 61, 47, 0.03) 0%, rgba(30, 61, 47, 0.08) 100%),
    #ebe3d3;
  position: relative;
  cursor: grab;
}

.tree-stage.panning {
  cursor: grabbing;
}

.tree-svg {
  width: 100%;
  height: 100%;
  min-height: 480px;
}

.person-card {
  cursor: pointer;
}

.person-card:hover rect:first-child {
  filter: drop-shadow(0 4px 10px rgba(30, 61, 47, 0.18));
}

.gen-label {
  font-size: 15px;
  font-weight: 700;
  fill: #163328;
  font-family: "Source Han Sans SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.card-line {
  font-size: 14px;
  fill: #2a241c;
  font-family: "Source Han Sans SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.card-line.name {
  font-size: 17px;
  font-weight: 700;
  fill: #1a1510;
  letter-spacing: 0.02em;
}

.card-line.meta {
  font-size: 13px;
  fill: #4f4338;
}

.empty-tip {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--text-muted);
  font-size: 15px;
}
</style>
