<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import FamilyTree from '@/components/tree/FamilyTree.vue'
import { formatPersonDisplayName } from '@/api/tree'
import {
  fetchPublicFullTree,
  fetchPublicLineageTree,
  fetchPublicPatrilinealTree,
  fetchPublicPerson,
  fetchPublicPersons,
} from '@/api/public'
import type { Person, TreeGraph } from '@/types'
import { usePortalStore } from '@/stores/portal'

type PortalTreeMode = 'full' | 'patrilineal' | 'lineage'

const route = useRoute()
const router = useRouter()
const portalStore = usePortalStore()

const loading = ref(false)
/** 打开族谱默认进入全系视图；带 person_id 从检索进入时会切到 lineage */
const mode = ref<PortalTreeMode>('full')
const treeReady = ref(false)
const rawTreeData = ref<TreeGraph | null>(null)
const persons = ref<Person[]>([])
const focusPersonId = ref<number>()
const personSearchText = ref('')
const maxGenerations = ref(20)
const upGenerations = ref(5)
const downGenerations = ref(5)
const searchInputRef = ref<{ focus?: () => void } | null>(null)

const modeDescription = computed(() => {
  switch (mode.value) {
    case 'full':
      return '全部成员按树形展开，可检索并高亮指定人物'
    case 'patrilineal':
      return '从指定祖先向下展示男系世系'
    case 'lineage':
      return '指定人物为中心，向上查祖、向下查孙'
    default:
      return ''
  }
})

const focusPersonIdStr = computed(() => {
  if (focusPersonId.value != null) return String(focusPersonId.value)
  if (rawTreeData.value?.focus_person_id) return rawTreeData.value.focus_person_id
  return null
})

function personOptionLabel(person: Person) {
  return formatPersonDisplayName(person).replace('\n', ' · ')
}

interface PersonSuggestion {
  value: string
  person: Person
}

async function searchPersonsRemote(keyword?: string): Promise<Person[]> {
  const data = await fetchPublicPersons({
    keyword: keyword?.trim() || undefined,
    page: 1,
    page_size: 100,
  })
  return data.items
}

function mergePersons(list: Person[]) {
  if (!list.length) return
  const map = new Map(persons.value.map((item) => [item.id, item]))
  for (const item of list) map.set(item.id, item)
  persons.value = [...map.values()].sort(
    (a, b) => (a.generation ?? 9999) - (b.generation ?? 9999) || a.id - b.id,
  )
}

async function queryPersonSuggestions(
  queryString: string,
  cb: (suggestions: PersonSuggestion[]) => void,
) {
  try {
    const items = await searchPersonsRemote(queryString)
    mergePersons(items)
    cb(
      items.map((person) => ({
        value: personOptionLabel(person),
        person,
      })),
    )
  } catch {
    cb([])
  }
}

function handlePersonPick(item: PersonSuggestion) {
  focusPersonId.value = item.person.id
  personSearchText.value = item.value
  if (mode.value !== 'full') {
    loadTree()
  }
}

function handlePersonClear() {
  focusPersonId.value = undefined
  personSearchText.value = ''
}

async function resolvePersonFromInput(options?: { silent?: boolean }): Promise<Person | null> {
  if (focusPersonId.value) {
    const existing = persons.value.find((item) => item.id === focusPersonId.value)
    if (existing) return existing
  }
  const text = personSearchText.value.trim()
  if (!text) return null
  let matched = persons.value.filter(
    (item) => item.name.includes(text) || item.nickname.includes(text),
  )
  if (!matched.length) {
    try {
      matched = await searchPersonsRemote(text)
      mergePersons(matched)
    } catch {
      if (!options?.silent) ElMessage.error('人物查询失败')
      return null
    }
  }
  if (!matched.length) return null
  return matched.find((item) => item.name === text || item.nickname === text) ?? matched[0]
}

async function ensureFocusPerson(): Promise<boolean> {
  if (focusPersonId.value) return true
  const resolved = await resolvePersonFromInput({ silent: true })
  if (resolved) {
    focusPersonId.value = resolved.id
    personSearchText.value = personOptionLabel(resolved)
    return true
  }
  if (persons.value.length) {
    focusPersonId.value = persons.value[0].id
    const person = persons.value[0]
    personSearchText.value = personOptionLabel(person)
    return true
  }
  return false
}

async function loadPersonOptions() {
  try {
    const data = await fetchPublicPersons({ page: 1, page_size: 100 })
    persons.value = data.items
    // 非全图模式需要默认人物；全图仅在用户检索时高亮
    if (mode.value !== 'full') {
      await ensureFocusPerson()
    }
  } catch (error) {
    persons.value = []
    ElMessage.error(error instanceof Error ? error.message : '加载人物失败')
  }
}

async function loadTree() {
  loading.value = true
  try {
    if (mode.value === 'full') {
      rawTreeData.value = await fetchPublicFullTree()
      return
    }

    const ready = await ensureFocusPerson()
    if (!ready || !focusPersonId.value) {
      rawTreeData.value = null
      ElMessage.warning('请先选择或搜索一位人物')
      return
    }

    if (mode.value === 'patrilineal') {
      rawTreeData.value = await fetchPublicPatrilinealTree({
        root_person_id: focusPersonId.value,
        max_generations: maxGenerations.value,
      })
    } else {
      try {
        rawTreeData.value = await fetchPublicLineageTree({
          person_id: focusPersonId.value,
          up_generations: upGenerations.value,
          down_generations: downGenerations.value,
        })
      } catch {
        rawTreeData.value = await fetchPublicPatrilinealTree({
          root_person_id: focusPersonId.value,
          max_generations: downGenerations.value,
        })
      }
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载族谱失败')
  } finally {
    loading.value = false
  }
}

async function searchAndLoadPerson() {
  // 全图检索：优先按输入关键词匹配，避免沿用旧的 focusPersonId
  if (mode.value === 'full') {
    focusPersonId.value = undefined
  }
  const person = await resolvePersonFromInput()
  if (!person) {
    ElMessage.warning('未找到匹配人物')
    return
  }
  focusPersonId.value = person.id
  personSearchText.value = personOptionLabel(person)
  if (mode.value === 'full') {
    // 全图数据不变，仅高亮并定位
    return
  }
  await loadTree()
}

function openPerson() {
  if (!focusPersonId.value) {
    ElMessage.warning('请先指定人物')
    return
  }
  router.push(`/portal/person/${focusPersonId.value}`)
}

watch(mode, () => {
  if (!treeReady.value) return
  loadTree()
})

async function applyRouteFocus() {
  const qMode = route.query.mode
  const qPerson = route.query.person_id

  if (typeof qMode === 'string' && ['full', 'patrilineal', 'lineage'].includes(qMode)) {
    mode.value = qMode as PortalTreeMode
  } else if (typeof qPerson === 'string' && qPerson) {
    // 从检索/档案「在族谱中查看」进入 → 以人为中心
    mode.value = 'lineage'
  }

  if (typeof qPerson === 'string' && qPerson) {
    const id = Number(qPerson)
    if (!Number.isNaN(id)) {
      focusPersonId.value = id
      let person = persons.value.find((item) => item.id === id)
      if (!person) {
        try {
          person = await fetchPublicPerson(id)
          mergePersons([person])
        } catch {
          /* ignore */
        }
      }
      if (person) {
        personSearchText.value = personOptionLabel(person)
      }
    }
  }
}

watch(
  () => [route.query.person_id, route.query.mode] as const,
  async () => {
    if (!treeReady.value) return
    await applyRouteFocus()
    await loadTree()
  },
)

onMounted(async () => {
  await portalStore.ensureFamily().catch(() => null)
  await loadPersonOptions()
  await applyRouteFocus()
  await loadTree()
  treeReady.value = true

  if (route.query.focus === 'search') {
    searchInputRef.value?.focus?.()
  }
})
</script>

<template>
  <div class="portal-tree">
    <div class="toolbar">
      <div>
        <h1 class="title">族谱浏览</h1>
        <p class="subtitle">{{ modeDescription }}</p>
      </div>
      <div class="actions">
        <el-radio-group v-model="mode" size="small">
          <el-radio-button value="full">世系全图</el-radio-button>
          <el-radio-button value="patrilineal">男系世系</el-radio-button>
          <el-radio-button value="lineage">以人为中心</el-radio-button>
        </el-radio-group>

        <div class="person-search">
          <el-autocomplete
            ref="searchInputRef"
            v-model="personSearchText"
            :fetch-suggestions="queryPersonSuggestions"
            placeholder="检索姓名或小名"
            clearable
            style="width: 220px"
            @select="handlePersonPick"
            @clear="handlePersonClear"
            @keyup.enter="searchAndLoadPerson"
          />
          <el-button @click="searchAndLoadPerson">查询</el-button>
          <el-button link type="primary" @click="openPerson">人物档案</el-button>
        </div>

        <div v-if="mode === 'patrilineal'" class="depth">
          <span>向下 {{ maxGenerations }} 世</span>
          <el-slider v-model="maxGenerations" :min="3" :max="30" :step="1" @change="loadTree" />
        </div>

        <template v-if="mode === 'lineage'">
          <div class="depth">
            <span>向上 {{ upGenerations }}</span>
            <el-slider v-model="upGenerations" :min="0" :max="20" @change="loadTree" />
          </div>
          <div class="depth">
            <span>向下 {{ downGenerations }}</span>
            <el-slider v-model="downGenerations" :min="0" :max="20" @change="loadTree" />
          </div>
        </template>

        <el-button type="primary" @click="loadTree">刷新</el-button>
      </div>
    </div>

    <div v-loading="loading" class="tree-panel">
      <div v-if="rawTreeData?.nodes?.length" class="tree-meta">
        共 {{ rawTreeData.nodes.length }} 人
        <span v-if="focusPersonIdStr"> · 已高亮检索人物，可点击节点切换聚焦</span>
      </div>
      <FamilyTree :data="rawTreeData" :focus-person-id="focusPersonIdStr" />
    </div>
  </div>
</template>

<style scoped>
.portal-tree {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: calc(100vh - 180px);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
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

.person-search,
.depth {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7a71;
}

.depth {
  width: 170px;
}

.depth :deep(.el-slider) {
  width: 90px;
}

.tree-panel {
  flex: 1;
  min-height: 560px;
  background: rgba(255, 252, 247, 0.8);
  border: 1px solid rgba(36, 70, 54, 0.1);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tree-meta {
  padding: 10px 14px 0;
  font-size: 13px;
  color: #6b7a71;
}
</style>
