<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AmapViewer from '@/components/map/AmapViewer.vue'
import { fetchPublicGeoPlaces, fetchPublicResidences } from '@/api/public'
import type { GeoPlace, GeoPlaceType, Residence } from '@/types'
import { usePortalStore } from '@/stores/portal'
import {
  buildMapReturnQuery,
  savePortalReturn,
  type MapFilterType,
} from '@/utils/portalReturn'

const route = useRoute()
const router = useRouter()
const portalStore = usePortalStore()
const loading = ref(false)
const places = ref<GeoPlace[]>([])
const residences = ref<Residence[]>([])
const filterType = ref<GeoPlaceType | 'all'>('all')
const mapReadyToShow = ref(false)
const selectedPlaceId = ref<number | null>(null)
const personSearchText = ref('')
const pendingFocusPersonId = ref<number | null>(null)
const viewerRef = ref<{
  fitAll: () => void
  focusPlace: (id: number) => boolean
} | null>(null)

interface ResidenceSuggestion {
  value: string
  residence: Residence
}

/** 住宅点使用负 ID，避免与 geo_places.id 冲突 */
function residenceToMarker(item: Residence): GeoPlace {
  return {
    id: -item.id,
    family_id: 0,
    place_type: 'residence',
    name: item.name,
    longitude: item.longitude,
    latitude: item.latitude,
    address: item.address,
    description: item.nickname ? `小名：${item.nickname}` : null,
    related_person_id: item.id,
    created_at: '',
    updated_at: '',
  }
}

function residenceLabel(item: Residence) {
  const parts = [item.name]
  if (item.nickname) parts.push(`（${item.nickname}）`)
  if (item.generation != null) parts.push(`· 第${item.generation}世`)
  return parts.join(' ')
}

const typeText: Record<GeoPlaceType, string> = {
  distribution: '族群分布',
  cemetery: '坟地',
  residence: '住宅',
}

const allMapPlaces = computed(() => [
  ...places.value,
  ...residences.value.map(residenceToMarker),
])

const filteredPlaces = computed(() => {
  if (filterType.value === 'all') return allMapPlaces.value
  return allMapPlaces.value.filter((item) => item.place_type === filterType.value)
})

function matchResidences(keyword: string): Residence[] {
  const q = keyword.trim()
  if (!q) return [...residences.value]
  return residences.value.filter(
    (item) => item.name.includes(q) || (item.nickname && item.nickname.includes(q)),
  )
}

function queryResidenceSuggestions(
  queryString: string,
  cb: (suggestions: ResidenceSuggestion[]) => void,
) {
  const items = matchResidences(queryString)
  cb(
    items.map((residence) => ({
      value: residenceLabel(residence),
      residence,
    })),
  )
}

function focusResidence(residence: Residence) {
  filterType.value = 'residence'
  personSearchText.value = residenceLabel(residence)
  handlePlaceClick(residenceToMarker(residence))
  syncMapQuery(residence.id)
}

function handleResidencePick(item: ResidenceSuggestion) {
  focusResidence(item.residence)
}

function handleResidenceClear() {
  personSearchText.value = ''
  selectedPlaceId.value = null
  syncMapQuery()
}

function searchAndFocusResidence() {
  const text = personSearchText.value.trim()
  if (!text) {
    ElMessage.warning('请输入姓名或小名')
    return
  }
  const matched = matchResidences(text)
  if (!matched.length) {
    ElMessage.info('未找到有住宅坐标的匹配人物')
    return
  }
  const exact =
    matched.find((item) => item.name === text || item.nickname === text) ?? matched[0]
  focusResidence(exact)
}

function syncMapQuery(personId?: number) {
  const query = buildMapReturnQuery({
    source: 'map',
    filterType: filterType.value as MapFilterType,
    searchText: personSearchText.value || undefined,
    selectedPlaceId: selectedPlaceId.value,
    personId:
      personId ??
      (selectedPlaceId.value != null && selectedPlaceId.value < 0
        ? -selectedPlaceId.value
        : undefined),
  })
  router.replace({ path: '/portal/map', query })
}

function applyRouteState() {
  const qFilter = route.query.filter
  if (
    typeof qFilter === 'string' &&
    ['distribution', 'cemetery', 'residence', 'all'].includes(qFilter)
  ) {
    filterType.value = qFilter as GeoPlaceType | 'all'
  }
  const qSearch = route.query.q
  if (typeof qSearch === 'string') {
    personSearchText.value = qSearch
  }
  const qPerson = route.query.person_id
  if (typeof qPerson === 'string' && qPerson) {
    const id = Number(qPerson)
    if (!Number.isNaN(id)) {
      pendingFocusPersonId.value = id
    }
  }
}

function tryFocusPendingPerson() {
  const personId = pendingFocusPersonId.value
  if (personId == null || !residences.value.length) return
  const residence = residences.value.find((item) => item.id === personId)
  if (!residence) return
  pendingFocusPersonId.value = null
  nextTick(() => {
    focusResidence(residence)
  })
}

function openPersonFromMap(personId: number) {
  savePortalReturn({
    source: 'map',
    filterType: filterType.value as MapFilterType,
    searchText: personSearchText.value || undefined,
    selectedPlaceId: selectedPlaceId.value,
    personId,
  })
  syncMapQuery(personId)
  router.push(`/portal/person/${personId}`)
}

async function loadPlaces() {
  loading.value = true
  try {
    await portalStore.ensureFamily()
    const [geoList, residenceList] = await Promise.all([
      fetchPublicGeoPlaces(),
      fetchPublicResidences(),
    ])
    places.value = geoList
    residences.value = residenceList
    mapReadyToShow.value = true
    tryFocusPendingPerson()
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

watch(filterType, () => {
  syncMapQuery()
})

onMounted(() => {
  applyRouteState()
  loadPlaces()
})
</script>

<template>
  <div class="portal-map">
    <div class="toolbar">
      <div>
        <h1 class="title">族人分布地图</h1>
        <p class="subtitle">族群分布、坟地与族人住宅 · 可拖拽缩放 · 点击列表定位</p>
      </div>
      <div class="actions">
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="distribution">族群分布</el-radio-button>
          <el-radio-button value="cemetery">坟地</el-radio-button>
          <el-radio-button value="residence">住宅</el-radio-button>
        </el-radio-group>
        <div class="person-search">
          <el-autocomplete
            v-model="personSearchText"
            :fetch-suggestions="queryResidenceSuggestions"
            placeholder="检索住宅：姓名或小名"
            clearable
            style="width: 240px"
            @select="handleResidencePick"
            @clear="handleResidenceClear"
            @keyup.enter="searchAndFocusResidence"
          >
            <template #default="{ item }">
              <div class="suggest-row">
                <span>{{ item.value }}</span>
                <span v-if="item.residence.address" class="suggest-addr">{{ item.residence.address }}</span>
              </div>
            </template>
          </el-autocomplete>
          <el-button size="small" @click="searchAndFocusResidence">查询</el-button>
        </div>
        <el-button size="small" @click="handleFitAll">适应全部</el-button>
        <el-button size="small" :loading="loading" @click="loadPlaces">刷新</el-button>
        <div class="legend">
          <span class="dot distribution" />族群分布
          <span class="dot cemetery" />坟地
          <span class="dot residence" />住宅
        </div>
      </div>
    </div>

    <div class="map-layout">
      <div class="map-panel">
        <AmapViewer
          v-if="mapReadyToShow"
          ref="viewerRef"
          :places="filteredPlaces"
          @open-person="openPersonFromMap"
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

.person-search {
  display: flex;
  align-items: center;
  gap: 8px;
}

.suggest-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.35;
  padding: 2px 0;
}

.suggest-addr {
  font-size: 12px;
  color: #8a9690;
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

.dot.residence {
  background: #2f6b9a;
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

.badge.residence {
  background: rgba(47, 107, 154, 0.12);
  color: #2f6b9a;
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
