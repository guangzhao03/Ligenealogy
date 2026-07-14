<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPerson,
  createRelation,
  deletePerson,
  fetchPersonRelations,
  fetchPersons,
  updatePerson,
} from '@/api/person'
import { formatPersonDisplayName } from '@/api/tree'
import AddressSuggest from '@/components/map/AddressSuggest.vue'
import type { Person, PersonRelations } from '@/types'
import { useFamilyStore } from '@/stores/family'

const familyStore = useFamilyStore()
const loading = ref(false)
const persons = ref<Person[]>([])
const total = ref(0)
const dialogVisible = ref(false)
const relationDialogVisible = ref(false)
const relationDrawerVisible = ref(false)
const editingId = ref<number | null>(null)
const currentRelations = ref<PersonRelations | null>(null)
const selectedPersonName = ref('')

const query = reactive({
  keyword: '',
  generation: undefined as number | undefined,
  page: 1,
  page_size: 10,
})

const form = reactive({
  name: '',
  nickname: '',
  gender: 1,
  generation: undefined as number | undefined,
  birth_year: undefined as number | undefined,
  birthplace: '',
  phone: '',
  address: '',
  address_lng: null as number | null,
  address_lat: null as number | null,
  biography: '',
  remark: '',
  is_alive: 1,
})

const relationForm = reactive({
  from_person_id: undefined as number | undefined,
  to_person_id: undefined as number | undefined,
  relation_type: 'parent' as 'parent' | 'spouse',
})

const genderText = (gender: number) => ['未知', '男', '女'][gender] || '未知'
const hasFamily = computed(() => !!familyStore.currentFamily)

function personLabel(person: Person) {
  return formatPersonDisplayName(person).replace('\n', ' · ')
}

async function loadPersons() {
  if (!familyStore.currentFamily) return
  loading.value = true
  try {
    const data = await fetchPersons({
      family_id: familyStore.currentFamily.id,
      keyword: query.keyword || undefined,
      generation: query.generation,
      page: query.page,
      page_size: query.page_size,
    })
    persons.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    nickname: '',
    gender: 1,
    generation: undefined,
    birth_year: undefined,
    birthplace: '',
    phone: '',
    address: '',
    address_lng: null,
    address_lat: null,
    biography: '',
    remark: '',
    is_alive: 1,
  })
  dialogVisible.value = true
}

function openEdit(person: Person) {
  editingId.value = person.id
  Object.assign(form, {
    ...person,
    phone: person.phone || '',
    address: person.address || '',
    address_lng: person.address_lng ?? null,
    address_lat: person.address_lat ?? null,
    birthplace: person.birthplace || '',
    biography: person.biography || '',
    remark: person.remark || '',
  })
  dialogVisible.value = true
}

function validateForm() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写姓名')
    return false
  }
  if (!form.nickname.trim()) {
    ElMessage.warning('请填写小名')
    return false
  }
  if (!form.generation || form.generation < 1) {
    ElMessage.warning('请填写辈分（第几代）')
    return false
  }
  if (!form.birth_year || form.birth_year < 1000) {
    ElMessage.warning('请填写出生年份')
    return false
  }
  return true
}

async function handleSave() {
  if (!familyStore.currentFamily || !validateForm()) return
  const payload = {
    name: form.name.trim(),
    nickname: form.nickname.trim(),
    gender: form.gender,
    generation: form.generation!,
    birth_year: form.birth_year!,
    birthplace: form.birthplace || undefined,
    phone: form.phone || undefined,
    address: form.address?.trim() || undefined,
    address_lng: form.address?.trim() ? form.address_lng ?? undefined : undefined,
    address_lat: form.address?.trim() ? form.address_lat ?? undefined : undefined,
    biography: form.biography || undefined,
    remark: form.remark || undefined,
    is_alive: form.is_alive,
  }
  if (editingId.value) {
    await updatePerson(editingId.value, {
      ...payload,
      // 显式清空坐标：无地址时传 null
      address: form.address?.trim() || null,
      address_lng: form.address?.trim() ? form.address_lng : null,
      address_lat: form.address?.trim() ? form.address_lat : null,
    })
    ElMessage.success('更新成功')
  } else {
    await createPerson({ ...payload, family_id: familyStore.currentFamily.id })
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  await loadPersons()
}

async function handleDelete(person: Person) {
  await ElMessageBox.confirm(`确定删除「${personLabel(person)}」吗？`, '提示', { type: 'warning' })
  await deletePerson(person.id)
  ElMessage.success('删除成功')
  await loadPersons()
}

function openRelationDialog() {
  relationForm.from_person_id = undefined
  relationForm.to_person_id = undefined
  relationForm.relation_type = 'parent'
  relationDialogVisible.value = true
}

async function handleCreateRelation() {
  if (!familyStore.currentFamily) return
  if (!relationForm.from_person_id || !relationForm.to_person_id) {
    ElMessage.warning('请选择关系双方')
    return
  }
  await createRelation({
    family_id: familyStore.currentFamily.id,
    ...relationForm,
    from_person_id: relationForm.from_person_id,
    to_person_id: relationForm.to_person_id,
  })
  ElMessage.success('关系创建成功')
  relationDialogVisible.value = false
}

async function showRelations(person: Person) {
  selectedPersonName.value = personLabel(person)
  currentRelations.value = await fetchPersonRelations(person.id)
  relationDrawerVisible.value = true
}

onMounted(loadPersons)
</script>

<template>
  <div>
    <div class="toolbar">
      <div>
        <h1 class="page-title">人物管理</h1>
        <p class="page-subtitle">姓名、小名、辈分、出生年份为必填项</p>
      </div>
      <div class="toolbar-actions">
        <el-button :disabled="!hasFamily" @click="openRelationDialog">添加关系</el-button>
        <el-button type="primary" :disabled="!hasFamily" @click="openCreate">添加人物</el-button>
      </div>
    </div>

    <el-alert
      v-if="!hasFamily"
      title="请先在「家族概览」中选择一个家族"
      type="warning"
      show-icon
      :closable="false"
      class="mb-16"
    />

    <div v-if="hasFamily" class="page-card">
      <div class="filters">
        <el-input v-model="query.keyword" placeholder="搜索姓名/小名" clearable style="width: 220px" />
        <el-input-number v-model="query.generation" placeholder="辈分" :min="1" controls-position="right" />
        <el-button type="primary" @click="loadPersons">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="persons" stripe>
        <el-table-column label="姓名" min-width="140">
          <template #default="{ row }">{{ personLabel(row) }}</template>
        </el-table-column>
        <el-table-column prop="nickname" label="小名" width="100" />
        <el-table-column label="性别" width="80">
          <template #default="{ row }">{{ genderText(row.gender) }}</template>
        </el-table-column>
        <el-table-column prop="generation" label="辈分" width="80" />
        <el-table-column prop="birth_year" label="出生年份" width="100" />
        <el-table-column prop="birthplace" label="籍贯" min-width="120" />
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showRelations(row)">关系</el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          layout="total, prev, pager, next"
          :total="total"
          @current-change="loadPersons"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑人物' : '添加人物'" width="560px">
      <el-form label-width="90px">
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="小名" required><el-input v-model="form.nickname" placeholder="如：狗娃、二毛" /></el-form-item>
        <el-form-item label="辈分" required>
          <el-input-number v-model="form.generation" :min="1" placeholder="第几代" />
        </el-form-item>
        <el-form-item label="出生年份" required>
          <el-input-number v-model="form.birth_year" :min="1000" :max="2100" controls-position="right" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="籍贯"><el-input v-model="form.birthplace" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" placeholder="选填" /></el-form-item>
        <el-form-item label="现住址">
          <AddressSuggest
            v-model:address="form.address"
            v-model:longitude="form.address_lng"
            v-model:latitude="form.address_lat"
            placeholder="输入地址搜索，选择后自动带入坐标"
          />
        </el-form-item>
        <el-form-item label="简介"><el-input v-model="form.biography" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="relationDialogVisible" title="添加关系" width="520px">
      <el-form label-width="100px">
        <el-form-item label="关系类型">
          <el-select v-model="relationForm.relation_type">
            <el-option label="parent（父母 → 子女）" value="parent" />
            <el-option label="spouse（配偶）" value="spouse" />
          </el-select>
        </el-form-item>
        <el-form-item label="from 人物">
          <el-select v-model="relationForm.from_person_id" filterable placeholder="选择起始人物">
            <el-option v-for="p in persons" :key="p.id" :label="personLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="to 人物">
          <el-select v-model="relationForm.to_person_id" filterable placeholder="选择目标人物">
            <el-option v-for="p in persons" :key="p.id" :label="personLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="relationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateRelation">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="relationDrawerVisible" :title="`${selectedPersonName} 的关系`" size="360px">
      <template v-if="currentRelations">
        <section class="relation-block">
          <h4>父母</h4>
          <el-tag v-for="p in currentRelations.parents" :key="p.id" class="tag">{{ personLabel(p) }}</el-tag>
          <span v-if="!currentRelations.parents.length" class="empty">无</span>
        </section>
        <section class="relation-block">
          <h4>子女</h4>
          <el-tag v-for="p in currentRelations.children" :key="p.id" class="tag">{{ personLabel(p) }}</el-tag>
          <span v-if="!currentRelations.children.length" class="empty">无</span>
        </section>
        <section class="relation-block">
          <h4>配偶</h4>
          <el-tag v-for="p in currentRelations.spouses" :key="p.id" class="tag">{{ personLabel(p) }}</el-tag>
          <span v-if="!currentRelations.spouses.length" class="empty">无</span>
        </section>
        <section class="relation-block">
          <h4>兄弟姐妹（推导）</h4>
          <el-tag v-for="p in currentRelations.siblings" :key="p.id" class="tag" type="success">{{ personLabel(p) }}</el-tag>
          <span v-if="!currentRelations.siblings.length" class="empty">无</span>
        </section>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.mb-16 {
  margin-bottom: 16px;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.relation-block {
  margin-bottom: 20px;
}

.relation-block h4 {
  margin: 0 0 8px;
  color: var(--primary-dark);
}

.tag {
  margin: 0 8px 8px 0;
}

.empty {
  color: var(--text-muted);
}
</style>
