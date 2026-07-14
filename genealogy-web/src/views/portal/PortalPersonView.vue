<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchPublicPerson, fetchPublicPersonRelations } from '@/api/public'
import type { Person, PersonRelations } from '@/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const person = ref<Person | null>(null)
const relations = ref<PersonRelations | null>(null)

const personId = computed(() => Number(route.params.id))

function genderLabel(gender: number) {
  if (gender === 1) return '男'
  if (gender === 2) return '女'
  return '未知'
}

function personLine(p: Person) {
  const parts = [p.name]
  if (p.nickname) parts.push(`（${p.nickname}）`)
  if (p.generation) parts.push(`· 第${p.generation}代`)
  return parts.join('')
}

async function load() {
  if (!personId.value || Number.isNaN(personId.value)) return
  loading.value = true
  try {
    person.value = await fetchPublicPerson(personId.value)
    relations.value = await fetchPublicPersonRelations(personId.value)
  } catch (error) {
    person.value = null
    relations.value = null
    ElMessage.error(error instanceof Error ? error.message : '加载人物失败')
  } finally {
    loading.value = false
  }
}

function goTree() {
  router.push({
    path: '/portal/tree',
    query: { person_id: String(personId.value), mode: 'lineage' },
  })
}

function goRelated(id: number) {
  router.push(`/portal/person/${id}`)
}

watch(personId, load)
onMounted(load)
</script>

<template>
  <div v-loading="loading" class="portal-person">
    <template v-if="person">
      <div class="header">
        <div>
          <p class="eyebrow">人物档案</p>
          <h1 class="name">
            {{ person.name }}
            <span v-if="person.nickname" class="nickname">（{{ person.nickname }}）</span>
          </h1>
          <p class="meta">
            {{ genderLabel(person.gender) }}
            <span v-if="person.generation"> · 第 {{ person.generation }} 代</span>
            <span v-if="person.birth_year"> · {{ person.birth_year }}</span>
            <span v-if="person.death_date"> — {{ person.death_date.slice(0, 4) }}</span>
            <span v-else-if="person.is_alive === 0"> · 已故</span>
          </p>
        </div>
        <el-button type="primary" @click="goTree">在族谱中查看</el-button>
      </div>

      <div class="grid">
        <section class="block">
          <h2>基本信息</h2>
          <dl class="info">
            <div>
              <dt>籍贯</dt>
              <dd>{{ person.birthplace || '—' }}</dd>
            </div>
            <div>
              <dt>电话</dt>
              <dd>{{ person.phone || '—' }}</dd>
            </div>
            <div>
              <dt>现住址</dt>
              <dd>{{ person.address || '—' }}</dd>
            </div>
            <div>
              <dt>出生</dt>
              <dd>{{ person.birth_date || person.birth_year || '—' }}</dd>
            </div>
            <div>
              <dt>去世</dt>
              <dd>{{ person.death_date || (person.is_alive === 1 ? '在世' : '—') }}</dd>
            </div>
          </dl>
          <p v-if="person.biography" class="bio">{{ person.biography }}</p>
          <p v-else class="bio muted">暂无简介</p>
          <p v-if="person.remark" class="remark">备注：{{ person.remark }}</p>
        </section>

        <section v-if="relations" class="block">
          <h2>亲属</h2>
          <div class="relation-group">
            <h3>父母</h3>
            <div v-if="relations.parents.length" class="chips">
              <button
                v-for="item in relations.parents"
                :key="item.id"
                type="button"
                class="chip"
                @click="goRelated(item.id)"
              >
                {{ personLine(item) }}
              </button>
            </div>
            <p v-else class="empty">无</p>
          </div>
          <div class="relation-group">
            <h3>配偶</h3>
            <div v-if="relations.spouses.length" class="chips">
              <button
                v-for="item in relations.spouses"
                :key="item.id"
                type="button"
                class="chip"
                @click="goRelated(item.id)"
              >
                {{ personLine(item) }}
              </button>
            </div>
            <p v-else class="empty">无</p>
          </div>
          <div class="relation-group">
            <h3>子女</h3>
            <div v-if="relations.children.length" class="chips">
              <button
                v-for="item in relations.children"
                :key="item.id"
                type="button"
                class="chip"
                @click="goRelated(item.id)"
              >
                {{ personLine(item) }}
              </button>
            </div>
            <p v-else class="empty">无</p>
          </div>
          <div class="relation-group">
            <h3>兄弟姐妹</h3>
            <div v-if="relations.siblings.length" class="chips">
              <button
                v-for="item in relations.siblings"
                :key="item.id"
                type="button"
                class="chip"
                @click="goRelated(item.id)"
              >
                {{ personLine(item) }}
              </button>
            </div>
            <p v-else class="empty">无</p>
          </div>
        </section>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="人物不存在" />
  </div>
</template>

<style scoped>
.portal-person {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  color: #6b7a71;
}

.name {
  margin: 0;
  font-size: 32px;
  color: #1b3428;
}

.nickname {
  font-size: 22px;
  font-weight: 500;
  color: #3d5348;
}

.meta {
  margin: 10px 0 0;
  color: #5a6b62;
  font-size: 14px;
}

.grid {
  display: grid;
  gap: 16px;
}

.block {
  padding: 22px;
  border-radius: 16px;
  background: rgba(255, 252, 247, 0.85);
  border: 1px solid rgba(36, 70, 54, 0.1);
}

.block h2 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #1b3428;
}

.info {
  display: grid;
  gap: 10px;
  margin: 0;
}

.info div {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 8px;
  font-size: 14px;
}

.info dt {
  color: #6b7a71;
}

.info dd {
  margin: 0;
  color: #1f2a24;
}

.bio {
  margin: 16px 0 0;
  line-height: 1.7;
  font-size: 14px;
  color: #3d5348;
}

.bio.muted {
  color: #8a9590;
}

.remark {
  margin: 10px 0 0;
  font-size: 13px;
  color: #6b7a71;
}

.relation-group + .relation-group {
  margin-top: 16px;
}

.relation-group h3 {
  margin: 0 0 8px;
  font-size: 13px;
  color: #6b7a71;
  font-weight: 600;
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

@media (max-width: 640px) {
  .header {
    flex-direction: column;
  }
}
</style>
