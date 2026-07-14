<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ensureAmapSecurityConfig, hasAmapKey, loadAmap } from '@/utils/amap'

const props = defineProps<{
  longitude?: number | null
  latitude?: number | null
}>()

const emit = defineEmits<{
  pick: [payload: { longitude: number; latitude: number }]
}>()

const containerRef = ref<HTMLDivElement>()
const errorText = ref('')
const ready = ref(false)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let map: any = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let marker: any = null

async function initMap() {
  if (!containerRef.value) return
  if (!hasAmapKey()) {
    errorText.value = '未配置 VITE_AMAP_KEY，可手动填写经纬度'
    return
  }
  ensureAmapSecurityConfig()
  try {
    await nextTick()
    const AMap = await loadAmap()
    const lng = props.longitude ?? 112.52832
    const lat = props.latitude ?? 32.99076
    map = new AMap.Map(containerRef.value, {
      zoom: 10,
      center: [lng, lat],
      viewMode: '2D',
      resizeEnable: true,
      layers: [new AMap.TileLayer()],
    })
    marker = new AMap.Marker({
      position: [lng, lat],
      draggable: true,
    })
    map.add(marker)
    map.on('click', (event: { lnglat: { getLng: () => number; getLat: () => number } }) => {
      const longitude = event.lnglat.getLng()
      const latitude = event.lnglat.getLat()
      marker.setPosition([longitude, latitude])
      emit('pick', { longitude, latitude })
    })
    marker.on('dragend', () => {
      const position = marker.getPosition()
      emit('pick', { longitude: position.getLng(), latitude: position.getLat() })
    })
    map.on('complete', () => {
      map.resize()
      ready.value = true
      errorText.value = ''
    })
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : '地图加载失败'
  }
}

function syncMarker() {
  if (!map || !marker || props.longitude == null || props.latitude == null) return
  marker.setPosition([props.longitude, props.latitude])
  map.setCenter([props.longitude, props.latitude])
}

watch(() => [props.longitude, props.latitude], syncMarker)

onMounted(() => {
  initMap()
})

onBeforeUnmount(() => {
  if (map) {
    map.destroy()
    map = null
    marker = null
  }
})
</script>

<template>
  <div class="amap-picker">
    <div v-if="errorText" class="picker-hint">{{ errorText }}</div>
    <div class="picker-frame">
      <div ref="containerRef" class="picker-map" />
    </div>
    <p v-if="ready" class="picker-tip">点击地图或拖动标记选择坐标</p>
  </div>
</template>

<style scoped>
.amap-picker {
  width: 100%;
}

.picker-frame {
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(36, 70, 54, 0.15);
  background: #eef2ee;
}

.picker-map {
  width: 100%;
  height: 260px;
}

.picker-hint,
.picker-tip {
  margin: 0 0 8px;
  font-size: 12px;
  color: #6b7a71;
}

.picker-tip {
  margin: 8px 0 0;
}
</style>
