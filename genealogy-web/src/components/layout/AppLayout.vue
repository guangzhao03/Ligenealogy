<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Collection,
  Download,
  Location,
  Share,
  SwitchButton,
  User,
  UserFilled,
  Avatar,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useFamilyStore } from '@/stores/family'

const authStore = useAuthStore()
const familyStore = useFamilyStore()
const router = useRouter()
const bootstrapping = ref(true)

const menus = [
  { path: '/families', title: '家族概览', icon: Collection },
  { path: '/persons', title: '人物管理', icon: User },
  { path: '/tree', title: '族谱树', icon: Share },
  { path: '/geo-places', title: '地理标记', icon: Location },
  { path: '/import-export', title: '导入导出', icon: Download },
  { path: '/users', title: '用户权限', icon: Avatar },
]

onMounted(async () => {
  try {
    await familyStore.ensureFamilySelected()
  } finally {
    bootstrapping.value = false
  }
})

function handleLogout() {
  authStore.logout()
  familyStore.setCurrentFamily(null)
  router.push('/login')
}

function goPortal() {
  router.push('/portal')
}
</script>

<template>
  <el-container v-loading="bootstrapping" class="layout-root">
    <el-aside width="220px" class="layout-aside">
      <div class="brand">
        <div class="brand-mark">谱</div>
        <div>
          <div class="brand-title">族谱系统</div>
          <div class="brand-sub">管理后台</div>
        </div>
      </div>

      <el-menu :default-active="$route.path" router class="side-menu">
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <span v-if="familyStore.currentFamily" class="current-family">
            {{ familyStore.currentFamily.name }}
            <span v-if="familyStore.currentFamily.origin_place" class="family-origin">
              · {{ familyStore.currentFamily.origin_place }}
            </span>
          </span>
          <span v-else class="current-family muted">尚未选择家族</span>
        </div>
        <div class="header-right">
          <el-button link type="primary" @click="goPortal">族谱展厅</el-button>
          <el-icon><UserFilled /></el-icon>
          <span>{{ authStore.user?.nickname || authStore.user?.username }}</span>
          <el-button link type="primary" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </el-header>

      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-root {
  min-height: 100vh;
}

.layout-aside {
  background: linear-gradient(180deg, #244636 0%, #1b3428 100%);
  color: #fff;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 24px 20px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
  display: grid;
  place-items: center;
  font-size: 22px;
  font-weight: 700;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
}

.brand-sub {
  font-size: 12px;
  opacity: 0.7;
}

.side-menu {
  border-right: none;
  background: transparent;
}

.side-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.82);
}

.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--paper-card);
  border-bottom: 1px solid var(--border-soft);
}

.current-family {
  font-weight: 600;
  color: var(--primary-dark);
}

.family-origin {
  font-weight: 400;
  color: var(--text-muted);
}

.current-family.muted {
  color: var(--text-muted);
  font-weight: 400;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layout-main {
  padding: 20px;
}
</style>
