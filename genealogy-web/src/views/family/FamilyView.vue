<script setup lang="ts">

import { computed, onMounted, reactive, ref } from 'vue'

import { ElMessage, ElMessageBox } from 'element-plus'

import {

  createFamily,

  deleteFamily,

  fetchFamilies,

  fetchFamilyStats,

  updateFamily,

} from '@/api/family'

import type { Family, FamilyStats } from '@/types'

import { useFamilyStore } from '@/stores/family'



const familyStore = useFamilyStore()

const loading = ref(false)

const families = ref<Family[]>([])

const stats = ref<FamilyStats | null>(null)

const dialogVisible = ref(false)

const editDialogVisible = ref(false)



const form = reactive({

  name: '',

  description: '',

  origin_place: '',

})



const editForm = reactive({

  name: '',

  description: '',

  origin_place: '',

})



const singleFamily = computed(() => (families.value.length === 1 ? families.value[0] : null))

const activeFamily = computed(() => familyStore.currentFamily || singleFamily.value)



async function loadStats(familyId: number) {

  stats.value = await fetchFamilyStats(familyId)

}



async function loadFamilies() {

  loading.value = true

  try {

    families.value = await fetchFamilies()

    if (families.value.length === 1) {

      familyStore.setCurrentFamily(families.value[0])

    }

    if (activeFamily.value) {

      await loadStats(activeFamily.value.id)

    } else {

      stats.value = null

    }

  } catch (error) {

    ElMessage.error(error instanceof Error ? error.message : '加载失败')

  } finally {

    loading.value = false

  }

}



function openCreate() {

  form.name = ''

  form.description = ''

  form.origin_place = ''

  dialogVisible.value = true

}



function openEdit() {

  if (!activeFamily.value) return

  editForm.name = activeFamily.value.name

  editForm.description = activeFamily.value.description || ''

  editForm.origin_place = activeFamily.value.origin_place || ''

  editDialogVisible.value = true

}



async function handleCreate() {

  if (!form.name.trim()) {

    ElMessage.warning('请输入家族名称')

    return

  }

  await createFamily(form)

  ElMessage.success('创建成功')

  dialogVisible.value = false

  await loadFamilies()

}



async function handleUpdate() {

  if (!activeFamily.value) return

  const updated = await updateFamily(activeFamily.value.id, editForm)

  familyStore.setCurrentFamily(updated)

  ElMessage.success('更新成功')

  editDialogVisible.value = false

  await loadFamilies()

}



function selectFamily(family: Family) {

  familyStore.setCurrentFamily(family)

  loadStats(family.id)

}



async function handleDelete(family: Family) {

  await ElMessageBox.confirm(`确定删除家族「${family.name}」吗？`, '提示', { type: 'warning' })

  await deleteFamily(family.id)

  if (familyStore.currentFamily?.id === family.id) {

    familyStore.setCurrentFamily(null)

  }

  ElMessage.success('删除成功')

  await loadFamilies()

}



onMounted(loadFamilies)

</script>



<template>

  <div>

    <div class="toolbar">

      <div>

        <h1 class="page-title">家族概览</h1>

        <p class="page-subtitle">

          {{ singleFamily ? '单大家族模式：已自动选中，可直接管理人物与族谱' : '选择或创建家族作为工作上下文' }}

        </p>

      </div>

      <el-button type="primary" @click="openCreate">创建家族</el-button>

    </div>



    <template v-if="singleFamily && activeFamily">

      <div v-loading="loading" class="overview page-card">

        <div class="overview-header">

          <div>

            <h2 class="family-name">{{ activeFamily.name }}</h2>

            <p class="family-meta">籍贯：{{ activeFamily.origin_place || '未填写' }}</p>

            <p class="family-desc">{{ activeFamily.description || '暂无简介' }}</p>

          </div>

          <div class="overview-actions">

            <el-button @click="openEdit">编辑信息</el-button>

            <el-button type="danger" plain @click="handleDelete(activeFamily)">删除家族</el-button>

          </div>

        </div>



        <el-row v-if="stats" :gutter="16" class="stats-row">

          <el-col :span="6">

            <div class="stat-card">

              <div class="stat-value">{{ stats.person_count }}</div>

              <div class="stat-label">总人数</div>

            </div>

          </el-col>

          <el-col :span="6">

            <div class="stat-card">

              <div class="stat-value">{{ stats.generation_span || '—' }}</div>

              <div class="stat-label">世代跨度</div>

            </div>

          </el-col>

          <el-col :span="6">

            <div class="stat-card">

              <div class="stat-value">{{ stats.male_count }}</div>

              <div class="stat-label">男性</div>

            </div>

          </el-col>

          <el-col :span="6">

            <div class="stat-card">

              <div class="stat-value">{{ stats.female_count }}</div>

              <div class="stat-label">女性</div>

            </div>

          </el-col>

        </el-row>



        <el-alert

          v-if="stats && stats.generation_span > 12"

          class="large-family-tip"

          type="info"

          show-icon

          :closable="false"

          title="大家族提示"

          description="您的家族世代较多，族谱树默认使用「男系族谱」并按世代深度加载，可在族谱树页面调整起始祖先与显示深度。"

        />

      </div>

    </template>



    <template v-else>

      <el-row v-loading="loading" :gutter="16">

        <el-col v-for="family in families" :key="family.id" :span="8">

          <div

            class="family-card page-card"

            :class="{ active: familyStore.currentFamily?.id === family.id }"

            @click="selectFamily(family)"

          >

            <div class="family-name">{{ family.name }}</div>

            <div class="family-meta">籍贯：{{ family.origin_place || '未填写' }}</div>

            <div class="family-desc">{{ family.description || '暂无简介' }}</div>

            <div class="family-actions" @click.stop>

              <el-button link type="danger" @click="handleDelete(family)">删除</el-button>

            </div>

          </div>

        </el-col>

      </el-row>

    </template>



    <el-empty v-if="!loading && families.length === 0" description="还没有家族，先创建一个吧" />



    <el-dialog v-model="dialogVisible" title="创建家族" width="480px">

      <el-form label-width="80px">

        <el-form-item label="家族名称">

          <el-input v-model="form.name" />

        </el-form-item>

        <el-form-item label="籍贯">

          <el-input v-model="form.origin_place" />

        </el-form-item>

        <el-form-item label="简介">

          <el-input v-model="form.description" type="textarea" :rows="3" />

        </el-form-item>

      </el-form>

      <template #footer>

        <el-button @click="dialogVisible = false">取消</el-button>

        <el-button type="primary" @click="handleCreate">确定</el-button>

      </template>

    </el-dialog>



    <el-dialog v-model="editDialogVisible" title="编辑家族" width="480px">

      <el-form label-width="80px">

        <el-form-item label="家族名称">

          <el-input v-model="editForm.name" />

        </el-form-item>

        <el-form-item label="籍贯">

          <el-input v-model="editForm.origin_place" />

        </el-form-item>

        <el-form-item label="简介">

          <el-input v-model="editForm.description" type="textarea" :rows="3" />

        </el-form-item>

      </el-form>

      <template #footer>

        <el-button @click="editDialogVisible = false">取消</el-button>

        <el-button type="primary" @click="handleUpdate">确定</el-button>

      </template>

    </el-dialog>

  </div>

</template>



<style scoped>

.toolbar {

  display: flex;

  justify-content: space-between;

  align-items: flex-start;

  margin-bottom: 16px;

}



.overview {

  padding: 24px;

}



.overview-header {

  display: flex;

  justify-content: space-between;

  gap: 16px;

  margin-bottom: 20px;

}



.overview-actions {

  display: flex;

  gap: 8px;

}



.stats-row {

  margin-bottom: 16px;

}



.stat-card {

  padding: 16px;

  border-radius: 10px;

  background: rgba(22, 58, 40, 0.06);

  border: 1px solid rgba(22, 58, 40, 0.12);

  text-align: center;

}



.stat-value {

  font-size: 28px;

  font-weight: 700;

  color: var(--primary-dark);

}



.stat-label {

  margin-top: 4px;

  color: var(--text-muted);

  font-size: 13px;

}



.large-family-tip {

  margin-top: 8px;

}



.family-card {

  cursor: pointer;

  margin-bottom: 16px;

  transition: transform 0.2s ease, box-shadow 0.2s ease;

}



.family-card:hover {

  transform: translateY(-2px);

}



.family-card.active {

  border-color: var(--primary);

  box-shadow: 0 0 0 2px rgba(47, 93, 70, 0.12);

}



.family-name {

  font-size: 20px;

  font-weight: 700;

  color: var(--primary-dark);

}



.family-meta,

.family-desc {

  margin-top: 8px;

  color: var(--text-muted);

  font-size: 14px;

}



.family-actions {

  margin-top: 12px;

  text-align: right;

}

</style>

