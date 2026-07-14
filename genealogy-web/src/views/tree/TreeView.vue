<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import FamilyTree from '@/components/tree/FamilyTree.vue'
import {
  fetchFullTree,
  fetchAncestorsTree,
  fetchDescendantsTree,
  fetchCenterPersonTree,
  fetchPatrilinealTree,
  formatPersonDisplayName,
} from '@/api/tree'
import { fetchFamilyStats } from '@/api/family'
import { fetchPersons } from '@/api/person'
import type { Person, TreeGraph } from '@/types'
import { useFamilyStore } from '@/stores/family'
import type { TreeViewKind } from '@/utils/genealogyLayout'

const familyStore = useFamilyStore()
const loading = ref(false)
const mode = ref<TreeViewKind>('full')
const rawTreeData = ref<TreeGraph | null>(null)
const persons = ref<Person[]>([])
const focusPersonId = ref<number>()
const personSearchText = ref('')
const maxGenerations = ref(20)
const upGenerations = ref(5)
const downGenerations = ref(5)
const generationRange = ref<{ min: number; max: number } | null>(null)
const viewGenFrom = ref<number>()
const viewGenTo = ref<number>()

const hasFamily = computed(() => !!familyStore.currentFamily)

const modeDescription = computed(() => {
  switch (mode.value) {
    case 'full':
      return '全部成员按树形展开，子女居中排列于父母下方，左侧世代标尺'
    case 'patrilineal':
      return '从指定祖先向下展示男系世系，女儿显示但不延续其后代'
    case 'lineage':
      return '指定人物为中心，向上查祖、向下查孙，自动聚焦到该人物'
    case 'ancestors':
      return '指定人物或某一世全部成员，向上追溯祖先'
    case 'descendants':
      return '指定人物或某一世全部成员，向下展开后代'
    default:
      return ''
  }
})

const sortedPersons = computed(() =>
  [...persons.value].sort(
    (a, b) => (a.generation ?? 9999) - (b.generation ?? 9999) || a.id - b.id,
  ),
)

const generationOptions = computed(() => {
  if (!generationRange.value) return []
  const options: number[] = []
  for (let i = generationRange.value.min; i <= generationRange.value.max; i += 1) {
    options.push(i)
  }
  return options
})

const focusPersonIdStr = computed(() => {
  if (rawTreeData.value?.focus_person_id) return rawTreeData.value.focus_person_id
  return focusPersonId.value != null ? String(focusPersonId.value) : null
})

const treeData = computed(() => {
  const data = rawTreeData.value
  if (!data || mode.value !== 'full') return data
  if (viewGenFrom.value == null || viewGenTo.value == null) return data

  const nodeIds = new Set(
    data.nodes
      .filter((node) => {
        const generation = node.generation
        if (generation == null) return true
        return generation >= viewGenFrom.value! && generation <= viewGenTo.value!
      })
      .map((node) => node.id),
  )

  return {
    ...data,
    nodes: data.nodes.filter((node) => nodeIds.has(node.id)),
    edges: data.edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)),
  }
})

function personOptionLabel(person: Person) {
  return formatPersonDisplayName(person).replace('\n', ' · ')
}

interface PersonSuggestion {
  value: string
  person: Person
}

const focusPersonName = computed(() => {
  if (!focusPersonId.value) return ''
  const person = persons.value.find((item) => item.id === focusPersonId.value)
  return person ? personOptionLabel(person) : personSearchText.value
})

function syncSearchTextFromFocus() {
  if (focusPersonId.value) {
    const person = persons.value.find((item) => item.id === focusPersonId.value)
    if (person) {
      personSearchText.value = personOptionLabel(person)
    }
  }
}

async function searchPersonsRemote(keyword?: string): Promise<Person[]> {
  if (!familyStore.currentFamily) return []
  const data = await fetchPersons({
    family_id: familyStore.currentFamily.id,
    keyword: keyword?.trim() || undefined,
    page: 1,
    page_size: 100,
  })
  return data.items
}

async function resolvePersonFromInput(options?: { silent?: boolean }): Promise<Person | null> {
  if (focusPersonId.value) {
    const cached = persons.value.find((item) => item.id === focusPersonId.value)
    if (cached) return cached
  }

  const keyword = personSearchText.value.trim()
  if (!keyword) return null

  let matches = sortedPersons.value.filter(
    (person) => person.name.includes(keyword) || person.nickname.includes(keyword),
  )

  if (!matches.length) {
    try {
      matches = await searchPersonsRemote(keyword)
      mergePersons(matches)
    } catch {
      if (!options?.silent) {
        ElMessage.error('人物查询失败，请稍后重试')
      }
      return null
    }
  }

  if (!matches.length) return null

  const exact = matches.find((person) => person.name === keyword || person.nickname === keyword)
  return exact ?? matches[0]
}

function mergePersons(items: Person[]) {
  if (!items.length) return
  const map = new Map(persons.value.map((person) => [person.id, person]))
  for (const person of items) {
    map.set(person.id, person)
  }
  persons.value = [...map.values()].sort(
    (a, b) => (a.generation ?? 9999) - (b.generation ?? 9999) || a.id - b.id,
  )
}

async function queryPersonSuggestions(queryString: string, cb: (results: PersonSuggestion[]) => void) {
  const keyword = queryString.trim()
  try {
    const remoteMatches = keyword ? await searchPersonsRemote(keyword) : await searchPersonsRemote()
    mergePersons(remoteMatches)
    const matched = keyword
      ? remoteMatches.filter(
          (person) => person.name.includes(keyword) || person.nickname.includes(keyword),
        )
      : remoteMatches
    cb(
      matched.slice(0, 15).map((person) => ({
        value: personOptionLabel(person),
        person,
      })),
    )
  } catch {
    const matched = keyword
      ? sortedPersons.value.filter(
          (person) => person.name.includes(keyword) || person.nickname.includes(keyword),
        )
      : sortedPersons.value
    cb(
      matched.slice(0, 15).map((person) => ({
        value: personOptionLabel(person),
        person,
      })),
    )
  }
}

function pickPerson(person: Person) {
  focusPersonId.value = person.id
  personSearchText.value = personOptionLabel(person)
  mergePersons([person])
  return loadTree()
}

function handlePersonPick(item: PersonSuggestion) {
  void pickPerson(item.person)
}

async function searchAndLoadPerson() {
  const keyword = personSearchText.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入姓名或小名')
    return
  }
  const person = await resolvePersonFromInput()
  if (!person) {
    ElMessage.warning(`未找到「${keyword}」相关人物`)
    focusPersonId.value = undefined
    rawTreeData.value = null
    return
  }
  if (person.name !== keyword && person.nickname !== keyword) {
    const remote = await searchPersonsRemote(keyword)
    const exact = remote.find((item) => item.name === keyword || item.nickname === keyword)
    if (exact) {
      await pickPerson(exact)
      return
    }
    if (remote.length > 1) {
      await pickPerson(person)
      ElMessage.info(`共 ${remote.length} 个匹配，已显示第一个，请从下拉建议中精确选择`)
      return
    }
  }
  await pickPerson(person)
}

function handlePersonClear() {
  focusPersonId.value = undefined
  personSearchText.value = ''
  if (mode.value !== 'full') {
    rawTreeData.value = null
  }
}

async function ensureFocusPerson() {
  if (focusPersonId.value) {
    syncSearchTextFromFocus()
    return true
  }

  const resolved = await resolvePersonFromInput({ silent: true })
  if (resolved) {
    focusPersonId.value = resolved.id
    personSearchText.value = personOptionLabel(resolved)
    return true
  }

  if (sortedPersons.value.length) {
    focusPersonId.value = sortedPersons.value[0].id
    syncSearchTextFromFocus()
    return true
  }

  return false
}

async function loadGenerationRange() {
  if (!familyStore.currentFamily) return
  const stats = await fetchFamilyStats(familyStore.currentFamily.id)
  if (stats.min_generation != null && stats.max_generation != null) {
    generationRange.value = { min: stats.min_generation, max: stats.max_generation }
    if (viewGenFrom.value == null) viewGenFrom.value = stats.min_generation
    if (viewGenTo.value == null) viewGenTo.value = stats.max_generation
  }
}

async function loadPersonOptions() {
  if (!familyStore.currentFamily) return
  try {
    const data = await fetchPersons({
      family_id: familyStore.currentFamily.id,
      page: 1,
      page_size: 100,
    })
    persons.value = data.items
    await ensureFocusPerson()
  } catch (error) {
    persons.value = []
    ElMessage.error(error instanceof Error ? error.message : '加载人物列表失败')
  }
}

async function loadTree(options?: { silent?: boolean }) {
  if (!familyStore.currentFamily) return
  loading.value = true
  try {
    const familyId = familyStore.currentFamily.id

    if (mode.value === 'full') {
      rawTreeData.value = await fetchFullTree(familyId)
      return
    }

    const ready = await ensureFocusPerson()
    if (!ready || !focusPersonId.value) {
      rawTreeData.value = null
      if (!options?.silent) {
        ElMessage.warning('请输入姓名或小名后查询，或从下拉建议中选择人物')
      }
      return
    }

    const personId = focusPersonId.value
    const person = persons.value.find((item) => item.id === personId)
    const startGeneration = person?.generation ?? 1

    switch (mode.value) {
      case 'patrilineal':
        rawTreeData.value = await fetchPatrilinealTree({
          family_id: familyId,
          root_person_id: personId,
          max_generations: maxGenerations.value,
        })
        break
      case 'ancestors':
        rawTreeData.value = await fetchAncestorsTree({
          family_id: familyId,
          person_id: personId,
          start_generation: startGeneration,
          max_generations: maxGenerations.value,
        })
        break
      case 'descendants':
        rawTreeData.value = await fetchDescendantsTree({
          family_id: familyId,
          person_id: personId,
          start_generation: startGeneration,
          max_generations: maxGenerations.value,
        })
        break
      case 'lineage':
        rawTreeData.value = await fetchCenterPersonTree({
          family_id: familyId,
          person_id: personId,
          start_generation: startGeneration,
          up_generations: upGenerations.value,
          down_generations: downGenerations.value,
        })
        break
    }
    if (rawTreeData.value && !rawTreeData.value.nodes.length) {
      ElMessage.warning('指定人物暂无关联族谱数据')
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载族谱失败')
  } finally {
    loading.value = false
  }
}

async function handleModeChange() {
  await loadTree({ silent: true })
}

watch(
  () => familyStore.currentFamily?.id,
  async () => {
    focusPersonId.value = undefined
    personSearchText.value = ''
    viewGenFrom.value = undefined
    viewGenTo.value = undefined
    await loadGenerationRange()
    await loadPersonOptions()
    await loadTree()
  },
)

onMounted(async () => {
  await loadGenerationRange()
  await loadPersonOptions()
  await loadTree()
})
</script>

<template>
  <div class="tree-page">
    <div class="toolbar">
      <div>
        <h1 class="page-title">族谱树</h1>
        <p class="page-subtitle">{{ modeDescription }}</p>
      </div>
      <div class="toolbar-actions">
        <el-radio-group v-model="mode" @change="handleModeChange">
          <el-radio-button value="full">世系全图</el-radio-button>
          <el-radio-button value="patrilineal">男系世系</el-radio-button>
          <el-radio-button value="lineage">以人为中心</el-radio-button>
          <el-radio-button value="ancestors">向上查祖</el-radio-button>
          <el-radio-button value="descendants">向下查孙</el-radio-button>
        </el-radio-group>

        <div v-if="mode !== 'full'" class="person-search">
          <el-autocomplete
            v-model="personSearchText"
            :fetch-suggestions="queryPersonSuggestions"
            placeholder="输入姓名或小名查询"
            clearable
            style="width: 240px"
            @select="handlePersonPick"
            @clear="handlePersonClear"
            @keyup.enter="searchAndLoadPerson"
          />
          <el-button @click="searchAndLoadPerson">查询</el-button>
        </div>

        <template v-if="mode === 'patrilineal' || mode === 'ancestors' || mode === 'descendants'">
          <div class="depth-control">
            <span>{{ mode === 'ancestors' ? '向上' : '向下' }} {{ maxGenerations }} 世</span>
            <el-slider v-model="maxGenerations" :min="3" :max="30" :step="1" @change="loadTree" />
          </div>
        </template>

        <template v-if="mode === 'lineage'">
          <div class="depth-control">
            <span>向上 {{ upGenerations }} 世</span>
            <el-slider v-model="upGenerations" :min="0" :max="20" :step="1" @change="loadTree" />
          </div>
          <div class="depth-control">
            <span>向下 {{ downGenerations }} 世</span>
            <el-slider v-model="downGenerations" :min="0" :max="20" :step="1" @change="loadTree" />
          </div>
        </template>

        <template v-if="mode === 'full' && generationRange">
          <el-select v-model="viewGenFrom" placeholder="起始世" style="width: 120px">
            <el-option
              v-for="generation in generationOptions"
              :key="`from-${generation}`"
              :label="`第 ${generation} 世`"
              :value="generation"
            />
          </el-select>
          <span class="range-sep">至</span>
          <el-select v-model="viewGenTo" placeholder="结束世" style="width: 120px">
            <el-option
              v-for="generation in generationOptions"
              :key="`to-${generation}`"
              :label="`第 ${generation} 世`"
              :value="generation"
            />
          </el-select>
        </template>

        <el-button type="primary" :disabled="!hasFamily" @click="loadTree">刷新</el-button>
      </div>
    </div>

    <el-alert
      v-if="!hasFamily"
      title="请先在「家族概览」中创建或选择家族"
      type="warning"
      show-icon
      :closable="false"
    />

    <div v-else v-loading="loading" class="tree-panel page-card">
      <div v-if="treeData?.nodes?.length" class="tree-meta">
        共 {{ treeData.nodes.length }} 人
        <span v-if="treeData.is_forest"> · 森林（{{ treeData.root_ids?.length || '多' }} 个根）</span>
        <span v-else> · 单树</span>
        <span v-if="focusPersonIdStr && mode !== 'full'">
          · 当前：{{ focusPersonName }}
        </span>
        <span v-if="treeData.start_generation"> · 中心第 {{ treeData.start_generation }} 世</span>
      </div>
      <FamilyTree :data="treeData" :focus-person-id="mode !== 'full' ? focusPersonIdStr : null" />
    </div>
  </div>
</template>

<style scoped>
.tree-page {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 16px;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.depth-control {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 180px;
  font-size: 13px;
  color: var(--text-muted);
}

.depth-control :deep(.el-slider) {
  width: 100px;
}

.range-sep {
  font-size: 13px;
  color: var(--text-muted);
}

.person-search {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tree-panel {
  flex: 1;
  min-height: 560px;
  display: flex;
  flex-direction: column;
}

.tree-meta {
  padding: 8px 12px 0;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
