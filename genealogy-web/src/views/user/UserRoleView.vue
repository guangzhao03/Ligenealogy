<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchUsers, updateUserRole } from '@/api/user'
import type { UserInfo } from '@/types'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const users = ref<UserInfo[]>([])

const roleOptions: Array<{ value: UserInfo['role']; label: string }> = [
  { value: 'member', label: '普通族民' },
  { value: 'editor', label: '信息发布员' },
  { value: 'admin', label: '管理员' },
]

async function loadUsers() {
  loading.value = true
  try {
    users.value = await fetchUsers()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载用户失败')
  } finally {
    loading.value = false
  }
}

async function handleRoleChange(row: UserInfo, role: UserInfo['role']) {
  try {
    const updated = await updateUserRole(row.id, role)
    row.role = updated.role
    ElMessage.success('角色已更新')
    if (row.id === authStore.user?.id) {
      await authStore.fetchProfile()
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新失败')
    await loadUsers()
  }
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <div class="toolbar">
      <div>
        <h1 class="page-title">用户权限</h1>
        <p class="page-subtitle">
          普通族民 · 信息发布员（后续看板发布）· 管理员（后台）。游客仍可免登录阅览展厅。
        </p>
      </div>
      <el-button @click="loadUsers">刷新</el-button>
    </div>

    <div v-loading="loading" class="page-card">
      <el-table :data="users" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column label="角色" min-width="180">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              style="width: 150px"
              @change="(value: UserInfo['role']) => handleRoleChange(row, value)"
            >
              <el-option
                v-for="opt in roleOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" min-width="180" />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
}
</style>
