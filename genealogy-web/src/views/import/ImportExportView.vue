<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  downloadBlob,
  exportPersons,
  exportRelations,
  importPersons,
  importRelations,
} from '@/api/importExport'
import { useFamilyStore } from '@/stores/family'

const familyStore = useFamilyStore()
const personFile = ref<File | null>(null)
const relationFile = ref<File | null>(null)
const loading = ref(false)
const hasFamily = computed(() => !!familyStore.currentFamily)

function onPersonFileChange(file: File) {
  personFile.value = file
}

function onRelationFileChange(file: File) {
  relationFile.value = file
}

async function handleImportPersons() {
  if (!familyStore.currentFamily || !personFile.value) return
  loading.value = true
  try {
    const res = await importPersons(familyStore.currentFamily.id, personFile.value)
    const result = res.data.data
    if (result.errors.length) {
      ElMessage.error(`导入失败：第 ${result.errors[0].row} 行 ${result.errors[0].message}`)
    } else {
      ElMessage.success(`成功导入 ${result.success_count} 条人物`)
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '导入失败')
  } finally {
    loading.value = false
  }
}

async function handleImportRelations() {
  if (!familyStore.currentFamily || !relationFile.value) return
  loading.value = true
  try {
    const res = await importRelations(familyStore.currentFamily.id, relationFile.value)
    const result = res.data.data
    if (result.errors.length) {
      ElMessage.error(`导入失败：第 ${result.errors[0].row} 行 ${result.errors[0].message}`)
    } else {
      ElMessage.success(`成功导入 ${result.success_count} 条关系`)
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '导入失败')
  } finally {
    loading.value = false
  }
}

async function handleExportPersons() {
  if (!familyStore.currentFamily) return
  const blob = await exportPersons(familyStore.currentFamily.id)
  downloadBlob(blob, `persons_${familyStore.currentFamily.id}.xlsx`)
}

async function handleExportRelations() {
  if (!familyStore.currentFamily) return
  const blob = await exportRelations(familyStore.currentFamily.id)
  downloadBlob(blob, `relations_${familyStore.currentFamily.id}.xlsx`)
}
</script>

<template>
  <div>
    <h1 class="page-title">导入导出</h1>
    <p class="page-subtitle">批量维护人物与 parent/spouse 关系</p>

    <el-alert
      v-if="!hasFamily"
      title="请先在「家族管理」中选择一个家族"
      type="warning"
      show-icon
      :closable="false"
      class="mb-16"
    />

    <el-row v-else :gutter="16">
      <el-col :span="12">
        <div class="page-card block">
          <h3>人物 Excel</h3>
          <p>表头：姓名、性别、世代、出生日期、去世日期、籍贯、简介、备注、是否在世</p>
          <el-upload :auto-upload="false" :show-file-list="true" :limit="1" @change="(f: any) => onPersonFileChange(f.raw)">
            <el-button>选择文件</el-button>
          </el-upload>
          <div class="actions">
            <el-button type="primary" :loading="loading" @click="handleImportPersons">导入人物</el-button>
            <el-button @click="handleExportPersons">导出人物</el-button>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="page-card block">
          <h3>关系 Excel</h3>
          <p>表头：from姓名、to姓名、关系类型（parent / spouse）</p>
          <el-upload :auto-upload="false" :show-file-list="true" :limit="1" @change="(f: any) => onRelationFileChange(f.raw)">
            <el-button>选择文件</el-button>
          </el-upload>
          <div class="actions">
            <el-button type="primary" :loading="loading" @click="handleImportRelations">导入关系</el-button>
            <el-button @click="handleExportRelations">导出关系</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.mb-16 {
  margin-bottom: 16px;
}

.block h3 {
  margin-top: 0;
  color: var(--primary-dark);
}

.block p {
  color: var(--text-muted);
  font-size: 14px;
}

.actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
