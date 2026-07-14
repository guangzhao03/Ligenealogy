<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AmapViewer from '@/components/map/AmapViewer.vue'
import { fetchPublicGeoPlaces } from '@/api/public'
import type { GeoPlace, GeoPlaceType } from '@/types'
import { usePortalStore } from '@/stores/portal'

const portalStore = usePortalStore()
const loading = ref(false)
const places = ref<GeoPlace[]>([])
const filterType = ref<GeoPlaceType | 'all'>('all')
const mapReadyToShow = ref(false)
const selectedPlaceId = ref<number | null>(null)
const viewerRef = ref<{
  fitAll: () => void
  focusPlace: (id: number) => boolean
} | null>(null)

const typeText: Record<GeoPlaceType, string> = {
  distribution: '族群分布',
  cemetery: '坟地',
}

const filteredPlaces = computed(() => {
  if (filterType.value === 'all') return places.value
  return places.value.filter((item) => item.place_type === filterType.value)
})

async function loadPlaces() {
  loading.value = true
  try {
    await portalStore.ensureFamily()
    places.value = await fetchPublicGeoPlaces()
    mapReadyToShow.value = true
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载地理标记失败')
  } finally {
    loading.value = false
  }
}

function handleFitAll() {
  viewerRef.value?.fitAll()
}

function handlePlaceClick(place: GeoPlace) {
  selectedPlaceId.value = place.id
  if (!viewerRef.value) {
    ElMessage.warning('地图加载中，请稍候')
    return
  }
  const ok = viewerRef.value.focusPlace(place.id)
  if (!ok) {
    ElMessage.info('正在定位，地图就绪后将自动跳转')
  }
}

onMounted(loadPlaces)
</script>

<template>
  <div class="portal-map">
    <div class="toolbar">
      <div>
        <h1 class="title">族人分布地图</h1>
        <p class="subtitle">查看族群分布与坟地位置 · 可拖拽、滚轮缩放 · 点击列表可定位到地图</p>
      </div>
      <div class="actions">
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="distribution">族群分布</el-radio-button>
          <el-radio-button value="cemetery">坟地</el-radio-button>
        </el-radio-group>
        <el-button size="small" @click="handleFitAll">适应全部</el-button>
        <el-button size="small" :loading="loading" @click="loadPlaces">刷新</el-button>
        <div class="legend">
          <span class="dot distribution" />族群分布
          <span class="dot cemetery" />坟地
        </div>
      </div>
    </div>

    <div class="map-layout">
      <div class="map-panel">
        <AmapViewer
          v-if="mapReadyToShow"
          ref="viewerRef"
          :places="filteredPlaces"
        />
        <div v-else class="map-placeholder">地图加载中…</div>
      </div>
      <aside v-loading="loading" class="list-panel">
        <h2>地点列表 · {{ filteredPlaces.length }}</h2>
        <p class="list-hint">点击下方地点，地图将跳转并标注</p>
        <div v-if="!filteredPlaces.length && !loading" class="empty">暂无地理标记</div>
        <button
          v-for="place in filteredPlaces"
          :key="place.id"
          type="button"
          class="place-card"
          :class="{ active: selectedPlaceId === place.id }"
          @click="handlePlaceClick(place)"
        >
          <div class="place-title">
            <span class="badge" :class="place.place_type">{{ typeText[place.place_type] }}</span>
            {{ place.name }}
          </div>
          <p v-if="place.address" class="place-meta">{{ place.address }}</p>
          <p v-if="place.description" class="place-desc">{{ place.description }}</p>
          <p class="place-coord">
            {{ place.longitude }}, {{ place.latitude }}
          </p>
        </button>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.portal-map {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: calc(100vh - 160px);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.title {
  margin: 0;
  font-size: 24px;
  color: #1b3428;
}

.subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7a71;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: flex-end;
}

.legend {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #5b6b62;
  margin-left: 4px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.dot.distribution {
  background: #2f6f4e;
}

.dot.cemetery {
  background: #8b5a2b;
}

.map-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  height: calc(100vh - 220px);
  min-height: 520px;
}

.map-panel {
  min-height: 0;
  height: 100%;
}

.map-placeholder {
  height: 100%;
  min-height: 520px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  border: 1px solid rgba(36, 70, 54, 0.12);
  background: #e8eee9;
  color: #6b7a71;
}

.list-panel {
  background: rgba(255, 252, 247, 0.9);
  border: 1px solid rgba(36, 70, 54, 0.1);
  border-radius: 14px;
  padding: 14px;
  overflow: auto;
  height: 100%;
  min-height: 0;
}

.list-panel h2 {
  margin: 0 0 4px;
  font-size: 15px;
  color: #1b3428;
}

.list-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: #6b7a71;
}

.empty {
  color: #6b7a71;
  font-size: 13px;
}

.place-card {
  display: block;
  width: 100%;
  text-align: left;
  padding: 12px 8px;
  border: none;
  border-top: 1px solid rgba(36, 70, 54, 0.08);
  background: transparent;
  cursor: pointer;
  font: inherit;
  color: inherit;
  border-radius: 8px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.place-card:first-of-type {
  border-top: none;
}

.place-card:hover {
  background: rgba(47, 93, 70, 0.08);
}

.place-card.active {
  background: rgba(47, 93, 70, 0.14);
  box-shadow: inset 3px 0 0 #2f5d46;
}

.place-title {
  font-weight: 700;
  color: #1b3428;
  font-size: 14px;
}

.badge {
  display: inline-block;
  margin-right: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.badge.distribution {
  background: rgba(47, 111, 78, 0.12);
  color: #2f6f4e;
}

.badge.cemetery {
  background: rgba(139, 90, 43, 0.12);
  color: #8b5a2b;
}

.place-meta,
.place-desc,
.place-coord {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6b7a71;
  line-height: 1.45;
}

@media (max-width: 960px) {
  .map-layout {
    grid-template-columns: 1fr;
    height: auto;
  }

  .map-panel {
    height: 520px;
  }

  .list-panel {
    max-height: 360px;
  }
}
</style>
