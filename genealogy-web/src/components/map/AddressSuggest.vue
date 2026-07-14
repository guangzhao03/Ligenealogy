<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { hasAmapKey, loadAmap } from '@/utils/amap'

const address = defineModel<string>('address', { default: '' })
const longitude = defineModel<number | null>('longitude', { default: null })
const latitude = defineModel<number | null>('latitude', { default: null })

const props = withDefaults(
  defineProps<{
    placeholder?: string
  }>(),
  { placeholder: '输入地址搜索并选择地点' },
)

type SuggestItem = {
  value: string
  address: string
  longitude: number
  latitude: number
}

const suggestions = ref<SuggestItem[]>([])
const geocodedHint = computed(() => {
  if (longitude.value != null && latitude.value != null) {
    return `已定位：${longitude.value.toFixed(6)}, ${latitude.value.toFixed(6)}`
  }
  return hasAmapKey() ? '从下拉选择地点可自动写入坐标' : '未配置高德 Key，仅保存文字地址'
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let placeSearch: any = null
let searchSeq = 0

async function ensurePlaceSearch() {
  if (!hasAmapKey()) return null
  if (placeSearch) return placeSearch
  const AMap = await loadAmap(['AMap.PlaceSearch'])
  placeSearch = new AMap.PlaceSearch({
    pageSize: 8,
    pageIndex: 1,
    city: '全国',
    citylimit: false,
  })
  return placeSearch
}

async function querySearch(queryString: string, cb: (results: SuggestItem[]) => void) {
  const keyword = queryString.trim()
  if (!keyword || !hasAmapKey()) {
    suggestions.value = []
    cb([])
    return
  }

  const seq = ++searchSeq
  try {
    const search = await ensurePlaceSearch()
    if (!search) {
      cb([])
      return
    }
    search.search(keyword, (status: string, result: { poiList?: { pois?: Array<{ name?: string; address?: string; location?: { lng: number; lat: number } }> } }) => {
      if (seq !== searchSeq) return
      if (status !== 'complete' || !result?.poiList?.pois?.length) {
        suggestions.value = []
        cb([])
        return
      }
      const items: SuggestItem[] = []
      for (const poi of result.poiList.pois) {
        if (!poi.location) continue
        const name = poi.name || ''
        const addr = poi.address || ''
        const label = addr ? `${name}（${addr}）` : name
        items.push({
          value: label.slice(0, 200),
          address: (addr || name).slice(0, 200),
          longitude: Number(poi.location.lng),
          latitude: Number(poi.location.lat),
        })
      }
      suggestions.value = items
      cb(items)
    })
  } catch {
    cb([])
  }
}

function handleSelect(item: SuggestItem) {
  address.value = item.address || item.value
  longitude.value = item.longitude
  latitude.value = item.latitude
}

function handleClear() {
  address.value = ''
  longitude.value = null
  latitude.value = null
  suggestions.value = []
}

watch(address, (value, oldValue) => {
  // 手工改文案且未重新选地点时，清除旧坐标避免错位
  if (value !== oldValue && longitude.value != null) {
    const matched = suggestions.value.some(
      (item) => item.address === value || item.value === value,
    )
    if (!matched && value.trim()) {
      // 保持：若等于上次选中的 address 文本则不算改动；选中时已同步赋值
    }
  }
  if (!value?.trim()) {
    longitude.value = null
    latitude.value = null
  }
})

async function pickFirstOnEnter() {
  const keyword = address.value.trim()
  if (!keyword || !hasAmapKey()) return
  if (longitude.value != null && latitude.value != null) return

  const search = await ensurePlaceSearch()
  if (!search) return

  await new Promise<void>((resolve) => {
    search.search(keyword, (status: string, result: { poiList?: { pois?: Array<{ name?: string; address?: string; location?: { lng: number; lat: number } }> } }) => {
      const poi = status === 'complete' ? result?.poiList?.pois?.[0] : null
      if (poi?.location) {
        const name = poi.name || ''
        const addr = poi.address || name
        address.value = addr.slice(0, 200)
        longitude.value = Number(poi.location.lng)
        latitude.value = Number(poi.location.lat)
      }
      resolve()
    })
  })
}
</script>

<template>
  <div class="address-suggest">
    <el-autocomplete
      v-model="address"
      :fetch-suggestions="querySearch"
      :placeholder="placeholder"
      clearable
      style="width: 100%"
      @select="handleSelect"
      @clear="handleClear"
      @keyup.enter="pickFirstOnEnter"
    >
      <template #default="{ item }">
        <div class="suggest-item">
          <div class="suggest-title">{{ item.value }}</div>
          <div class="suggest-coord">{{ item.longitude.toFixed(5) }}, {{ item.latitude.toFixed(5) }}</div>
        </div>
      </template>
    </el-autocomplete>
    <p class="geo-hint">{{ geocodedHint }}</p>
  </div>
</template>

<style scoped>
.address-suggest {
  width: 100%;
}

.geo-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6b7a71;
  line-height: 1.4;
}

.suggest-item {
  line-height: 1.35;
  padding: 2px 0;
}

.suggest-title {
  font-size: 13px;
  color: #1b3428;
}

.suggest-coord {
  font-size: 11px;
  color: #8a9690;
}
</style>
