<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { GeoPlace } from '@/types'
import { ensureAmapSecurityConfig, hasAmapKey, loadAmap } from '@/utils/amap'

const props = defineProps<{
  places: GeoPlace[]
}>()

const emit = defineEmits<{
  'open-person': [personId: number]
}>()

const containerRef = ref<HTMLDivElement>()
const errorText = ref('')

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let map: any = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let markers: any[] = []
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let infoWindow: any = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let toolBar: any = null
let mapReady = false
let lastPlaceSignature = ''
let pendingFocusId: number | null = null

const typeLabel: Record<string, string> = {
  distribution: '族群分布',
  cemetery: '坟地',
  residence: '住宅',
}

function placeSignature(list: GeoPlace[]) {
  return list
    .map((item) => item.id)
    .slice()
    .sort((a, b) => a - b)
    .join(',')
}

function buildInfoHtml(place: GeoPlace) {
  const personId =
    place.place_type === 'residence' && place.related_person_id
      ? place.related_person_id
      : null
  // 对标地图信息窗惯例：文字超链接，而非按钮
  const detailLink = personId
    ? `<div style="margin-top:10px">
         <a class="amap-person-detail-link" data-person-id="${personId}" href="/portal/person/${personId}"
            style="color:#2f6b9a;font-size:13px;text-decoration:underline;text-underline-offset:2px;cursor:pointer">
           查看详细信息
         </a>
       </div>`
    : ''
  return `
    <div style="min-width:180px;padding:4px 2px;line-height:1.5;text-align:left">
      <div style="font-weight:700;margin-bottom:4px">${place.name}</div>
      <div style="color:#5b6b62;font-size:12px">${typeLabel[place.place_type] || place.place_type}</div>
      ${place.address ? `<div style="margin-top:6px;font-size:13px">${place.address}</div>` : ''}
      ${place.description ? `<div style="margin-top:4px;font-size:12px;color:#6b7a71">${place.description}</div>` : ''}
      ${detailLink}
    </div>`
}

function bindDetailLink() {
  window.setTimeout(() => {
    const link = document.querySelector('.amap-person-detail-link') as HTMLAnchorElement | null
    if (!link) return
    link.onclick = (event) => {
      event.preventDefault()
      event.stopPropagation()
      const personId = Number(link.dataset.personId)
      if (!Number.isNaN(personId)) {
        emit('open-person', personId)
      }
    }
  }, 0)
}

async function initMap() {
  if (!containerRef.value) return
  if (!hasAmapKey()) {
    errorText.value = '未配置高德地图 Key（VITE_AMAP_KEY）。标记列表仍可查看，配置后显示地图。'
    return
  }

  ensureAmapSecurityConfig()

  try {
    await nextTick()
    const AMap = await loadAmap(['AMap.ToolBar', 'AMap.InfoWindow'])

    const el = containerRef.value
    if (el.clientHeight < 100) {
      el.style.height = '560px'
    }

    map = new AMap.Map(el, {
      zoom: 7,
      center: [113.0, 33.5],
      viewMode: '2D',
      resizeEnable: true,
      dragEnable: true,
      zoomEnable: true,
      doubleClickZoom: true,
      scrollWheel: true,
      touchZoom: true,
      layers: [new AMap.TileLayer()],
    })

    infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -28), isCustom: false })
    toolBar = new AMap.ToolBar({ position: { right: '16px', bottom: '16px' } })
    map.addControl(toolBar)

    map.on('complete', () => {
      mapReady = true
      map.resize()
      syncMarkers({ fit: true })
      flushPendingFocus()
      errorText.value = ''
    })
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : '地图加载失败'
  }
}

function syncMarkers(options?: { fit?: boolean }) {
  if (!map || !window.AMap) return
  const AMap = window.AMap

  markers.forEach((item) => map.remove(item))
  markers = []

  if (!props.places.length) {
    lastPlaceSignature = ''
    infoWindow?.close()
    return
  }

  const signature = placeSignature(props.places)
  const shouldFit = options?.fit === true || signature !== lastPlaceSignature

  for (const place of props.places) {
    const markerClass =
      place.place_type === 'cemetery'
        ? 'cemetery'
        : place.place_type === 'residence'
          ? 'residence'
          : 'distribution'
    const marker = new AMap.Marker({
      position: [place.longitude, place.latitude],
      title: place.name,
      content: `<div class="geo-marker ${markerClass}"></div>`,
      offset: new AMap.Pixel(-10, -10),
      // 事件冒泡到地图，避免标记层抢走拖拽
      bubble: true,
      extData: { id: place.id },
    })
    marker.on('click', () => {
      openPlace(place, marker)
    })
    map.add(marker)
    markers.push(marker)
  }

  lastPlaceSignature = signature

  if (shouldFit && pendingFocusId == null) {
    fitAll()
  }

  flushPendingFocus()
}

function openPlace(place: GeoPlace, marker?: { getPosition: () => unknown } | null) {
  if (!map || !infoWindow || !window.AMap) return
  infoWindow.setContent(buildInfoHtml(place))
  const resolved =
    marker || markers.find((item) => item.getExtData?.()?.id === place.id) || null
  const position = resolved
    ? resolved.getPosition()
    : new window.AMap.LngLat(place.longitude, place.latitude)
  infoWindow.open(map, position)
  bindDetailLink()
}

function fitAll() {
  if (!map || !markers.length) return
  if (markers.length === 1) {
    const pos = markers[0].getPosition()
    map.setZoomAndCenter(11, pos, false, 300)
    return
  }
  map.setFitView(markers, false, [60, 60, 60, 60], 12)
}

function flushPendingFocus() {
  if (pendingFocusId == null) return
  const id = pendingFocusId
  pendingFocusId = null
  focusPlace(id)
}

/** @returns 是否已成功定位（地图未就绪时会排队，返回 false） */
function focusPlace(id: number): boolean {
  if (!map || !window.AMap || !mapReady) {
    pendingFocusId = id
    return false
  }

  const place = props.places.find((item) => item.id === id)
  if (!place) {
    // 当前筛选列表中没有该点，放弃排队避免死循环
    pendingFocusId = null
    return false
  }

  const marker = markers.find((item) => item.getExtData?.()?.id === id)
  const center: [number, number] = [place.longitude, place.latitude]
  map.setZoomAndCenter(13, center, false, 300)
  // 动画过程中略延迟开窗，避免信息窗锚点偏移
  window.setTimeout(() => {
    openPlace(place, marker)
  }, 280)
  pendingFocusId = null
  return true
}

watch(
  () => placeSignature(props.places),
  () => {
    if (!mapReady) return
    syncMarkers({ fit: true })
  },
)

onMounted(() => {
  initMap()
})

onBeforeUnmount(() => {
  if (map) {
    if (toolBar) map.removeControl(toolBar)
    map.destroy()
    map = null
    markers = []
    infoWindow = null
    toolBar = null
    mapReady = false
    lastPlaceSignature = ''
    pendingFocusId = null
  }
})

defineExpose({
  fitAll,
  focusPlace,
})
</script>

<template>
  <div class="amap-viewer">
    <div v-if="errorText" class="viewer-hint">{{ errorText }}</div>
    <div class="viewer-frame">
      <div ref="containerRef" class="viewer-map" />
    </div>
  </div>
</template>

<style scoped>
.amap-viewer {
  width: 100%;
  height: 100%;
  min-height: 560px;
  position: relative;
}

.viewer-frame {
  width: 100%;
  height: 100%;
  min-height: 560px;
  border-radius: 14px;
  border: 1px solid rgba(36, 70, 54, 0.12);
  overflow: hidden;
  background: #dfe6e0;
}

.viewer-map {
  width: 100%;
  height: 100%;
  min-height: 560px;
  /* 保证拖拽落在地图画布上 */
  cursor: grab;
  touch-action: none;
}

.viewer-map:active {
  cursor: grabbing;
}

.viewer-map :deep(.amap-container) {
  width: 100% !important;
  height: 100% !important;
}

.viewer-hint {
  position: absolute;
  z-index: 5;
  left: 12px;
  right: 12px;
  top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 252, 247, 0.95);
  border: 1px solid rgba(36, 70, 54, 0.12);
  font-size: 13px;
  color: #5b6b62;
  pointer-events: none;
}

:global(.geo-marker) {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  pointer-events: none;
}

:global(.geo-marker.distribution) {
  background: #2f6f4e;
}

:global(.geo-marker.cemetery) {
  background: #8b5a2b;
}

:global(.geo-marker.residence) {
  background: #2f6b9a;
}
</style>
