<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchPublicPerson,
  fetchPublicPersonRelations,
  fetchPublicPersons,
} from '@/api/public'
import type { Person, PersonRelations } from '@/types'

const router = useRouter()
const keyword = ref('')
const loading = ref(false)
const searching = ref(false)
const results = ref<Person[]>([])
const selectedId = ref<number | null>(null)
const person = ref<Person | null>(null)
const relations = ref<PersonRelations | null>(null)

function genderLabel(gender: number) {
  if (gender === 1) return '男'
  if (gender === 2) return '女'
  return '未知'
}

function personLine(p: Person) {
  const parts = [p.name]
  if (p.nickname) parts.push(`（${p.nickname}）`)
  if (p.generation) parts.push(`· 第${p.generation}代`)
  if (p.birth_year) parts.push(`· ${p.birth_year}`)
  return parts.join(' ')
}

async function search() {
  searching.value = true
  try {
    const data = await fetchPublicPersons({
      keyword: keyword.value.trim() || undefined,
      page: 1,
      page_size: 50,
    })
    results.value = data.items
    if (!data.items.length) {
      person.value = null
      relations.value = null
      selectedId.value = null
      ElMessage.info('未找到匹配人物')
      return
    }
    await selectPerson(data.items[0].id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '搜索失败')
  } finally {
    searching.value = false
  }
}

async function selectPerson(id: number) {
  selectedId.value = id
  loading.value = true
  try {
    person.value = await fetchPublicPerson(id)
    relations.value = await fetchPublicPersonRelations(id)
  } catch (error) {
    person.value = null
    relations.value = null
    ElMessage.error(error instanceof Error ? error.message : '加载人物失败')
  } finally {
    loading.value = false
  }
}

function goTree() {
  if (!selectedId.value) return
  router.push({
    path: '/portal/tree',
    query: { person_id: String(selectedId.value), mode: 'lineage' },
  })
}

function goArchive(id: number) {
  router.push(`/portal/person/${id}`)
}

onMounted(() => {
  search()
})
</script>

<template>
  <div class="portal-search">
    <div class="page-head">
      <h1 class="title">检索人物</h1>
      <p class="subtitle">按姓名或小名查询，下方展示联系方式与亲属信息</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="输入姓名或小名，如：明远"
        clearable
        size="large"
        @keyup.enter="search"
      />
      <el-button type="primary" size="large" :loading="searching" @click="search">查询</el-button>
    </div>

    <div class="layout">
      <aside class="result-list" v-loading="searching">
        <div class="list-title">查询结果（{{ results.length }}）</div>
        <button
          v-for="item in results"
          :key="item.id"
          type="button"
          class="result-item"
          :class="{ active: item.id === selectedId }"
          @click="selectPerson(item.id)"
        >
          <span class="result-name">{{ item.name }}（{{ item.nickname }}）</span>
          <span class="result-meta">
            第{{ item.generation || '—' }}代
            <template v-if="item.birth_year"> · {{ item.birth_year }}</template>
          </span>
        </button>
        <el-empty v-if="!searching && !results.length" description="暂无结果" :image-size="64" />
      </aside>

      <section v-loading="loading" class="info-panel">
        <template v-if="person">
          <div class="info-header">
            <div>
              <h2>
                {{ person.name }}
                <span class="nick">（{{ person.nickname }}）</span>
              </h2>
              <p class="meta">
                {{ genderLabel(person.gender) }}
                <span v-if="person.generation"> · 第 {{ person.generation }} 代</span>
                <span v-if="person.birth_year"> · {{ person.birth_year }}</span>
              </p>
            </div>
            <div class="actions">
              <el-button @click="goArchive(person.id)">完整档案</el-button>
              <el-button type="primary" @click="goTree">在族谱中查看</el-button>
            </div>
          </div>

          <div class="info-block">
            <h3>基本信息</h3>
            <dl>
              <div><dt>籍贯</dt><dd>{{ person.birthplace || '—' }}</dd></div>
              <div><dt>出生</dt><dd>{{ person.birth_date || person.birth_year || '—' }}</dd></div>
              <div>
                <dt>去世</dt>
                <dd>{{ person.death_date || (person.is_alive === 1 ? '在世' : '—') }}</dd>
              </div>
            </dl>
          </div>

          <div class="info-block">
            <h3>联系方式</h3>
            <dl>
              <div><dt>电话</dt><dd>{{ person.phone || '—' }}</dd></div>
              <div><dt>现住址</dt><dd>{{ person.address || '—' }}</dd></div>
            </dl>
          </div>

          <div v-if="relations" class="info-block">
            <h3>亲属</h3>
            <div class="rel-group">
              <h4>配偶</h4>
              <div v-if="relations.spouses.length" class="chips">
                <button
                  v-for="item in relations.spouses"
                  :key="item.id"
                  type="button"
                  class="chip"
                  @click="selectPerson(item.id)"
                >
                  {{ personLine(item) }}
                </button>
              </div>
              <p v-else class="empty">无</p>
            </div>
            <div class="rel-group">
              <h4>子女</h4>
              <div v-if="relations.children.length" class="chips">
                <button
                  v-for="item in relations.children"
                  :key="item.id"
                  type="button"
                  class="chip"
                  @click="selectPerson(item.id)"
                >
                  {{ personLine(item) }}
                </button>
              </div>
              <p v-else class="empty">无</p>
            </div>
            <div class="rel-group">
              <h4>父母</h4>
              <div v-if="relations.parents.length" class="chips">
                <button
                  v-for="item in relations.parents"
                  :key="item.id"
                  type="button"
                  class="chip"
                  @click="selectPerson(item.id)"
                >
                  {{ personLine(item) }}
                </button>
              </div>
              <p v-else class="empty">无</p>
            </div>
            <div class="rel-group">
              <h4>兄弟姐妹</h4>
              <div v-if="relations.siblings.length" class="chips">
                <button
                  v-for="item in relations.siblings"
                  :key="item.id"
                  type="button"
                  class="chip"
                  @click="selectPerson(item.id)"
                >
                  {{ personLine(item) }}
                </button>
              </div>
              <p v-else class="empty">无</p>
            </div>
          </div>

          <p v-if="person.biography" class="bio">{{ person.biography }}</p>
        </template>
        <el-empty v-else-if="!loading" description="请搜索并选择一位人物" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.portal-search {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-head .title {
  margin: 0;
  font-size: 28px;
  color: #1b3428;
}

.subtitle {
  margin: 8px 0 0;
  color: #6b7a71;
  font-size: 14px;
}

.search-bar {
  display: flex;
  gap: 12px;
  max-width: 640px;
}

.layout {
  display: grid;
  grid-template-columns: minmax(220px, 280px) 1fr;
  gap: 16px;
  align-items: start;
}

.result-list,
.info-panel {
  background: rgba(255, 252, 247, 0.88);
  border: 1px solid rgba(36, 70, 54, 0.1);
  border-radius: 16px;
  padding: 16px;
  min-height: 420px;
}

.list-title {
  font-size: 13px;
  color: #6b7a71;
  margin-bottom: 12px;
}

.result-item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-item:hover,
.result-item.active {
  background: rgba(47, 93, 70, 0.1);
}

.result-name {
  font-weight: 600;
  color: #1b3428;
  font-size: 14px;
}

.result-meta {
  font-size: 12px;
  color: #6b7a71;
}

.info-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.info-header h2 {
  margin: 0;
  font-size: 24px;
  color: #1b3428;
}

.nick {
  font-size: 18px;
  font-weight: 500;
  color: #3d5348;
}

.meta {
  margin: 8px 0 0;
  color: #5a6b62;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.info-block {
  margin-bottom: 18px;
}

.info-block h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #1b3428;
}

.info-block dl {
  margin: 0;
  display: grid;
  gap: 8px;
}

.info-block dl > div {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 8px;
  font-size: 14px;
}

.info-block dt {
  color: #6b7a71;
}

.info-block dd {
  margin: 0;
  color: #1f2a24;
}

.rel-group + .rel-group {
  margin-top: 12px;
}

.rel-group h4 {
  margin: 0 0 6px;
  font-size: 13px;
  color: #6b7a71;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  border: 1px solid rgba(47, 93, 70, 0.2);
  background: rgba(47, 93, 70, 0.06);
  color: #1b3428;
  border-radius: 999px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
}

.chip:hover {
  background: rgba(47, 93, 70, 0.12);
}

.empty {
  margin: 0;
  font-size: 13px;
  color: #9aa59e;
}

.bio {
  margin: 0;
  line-height: 1.7;
  font-size: 14px;
  color: #3d5348;
}

@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .info-header {
    flex-direction: column;
  }
}
</style>
