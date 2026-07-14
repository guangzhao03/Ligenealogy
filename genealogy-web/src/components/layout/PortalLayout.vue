<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePortalStore } from '@/stores/portal'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const portalStore = usePortalStore()
const bootstrapping = ref(true)

const navItems = [
  { path: '/portal', title: '家族', exact: true },
  { path: '/portal/tree', title: '族谱', exact: false },
  { path: '/portal/search', title: '检索', exact: false },
  { path: '/portal/map', title: '地图', exact: false },
]

const roleLabel: Record<string, string> = {
  member: '普通族民',
  editor: '信息发布员',
  admin: '管理员',
}

onMounted(async () => {
  try {
    if (authStore.token && !authStore.user) {
      await authStore.fetchProfile().catch(() => authStore.logout())
    }
    await portalStore.ensureFamily()
  } catch {
    // pages show empty/error states
  } finally {
    bootstrapping.value = false
  }
})

function isActive(item: (typeof navItems)[number]) {
  if (item.exact) return route.path === item.path
  return route.path.startsWith(item.path)
}

function goLogin() {
  router.push('/login')
}

function goAdmin() {
  router.push('/families')
}

function handleLogout() {
  authStore.logout()
  router.push('/portal')
}
</script>

<template>
  <div v-loading="bootstrapping" class="portal-root">
    <header class="portal-header">
      <router-link to="/portal" class="brand">
        <span class="brand-mark">谱</span>
        <span class="brand-text">
          <span class="brand-name">{{ portalStore.family?.name || '族谱展厅' }}</span>
          <span v-if="portalStore.family?.origin_place" class="brand-sub">
            {{ portalStore.family.origin_place }}
          </span>
        </span>
      </router-link>

      <nav class="portal-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item) }"
        >
          {{ item.title }}
        </router-link>
      </nav>

      <div class="header-actions">
        <template v-if="authStore.user">
          <span class="user-chip">
            {{ authStore.user.nickname || authStore.user.username }}
            <span class="role-tag">{{ roleLabel[authStore.user.role] || authStore.user.role }}</span>
          </span>
          <button
            v-if="authStore.canAccessAdmin"
            type="button"
            class="admin-link"
            @click="goAdmin"
          >
            进入管理后台
          </button>
          <button type="button" class="admin-link" @click="handleLogout">退出</button>
        </template>
        <button v-else type="button" class="admin-link" @click="goLogin">登录</button>
      </div>
    </header>

    <main class="portal-main">
      <router-view />
    </main>

    <footer class="portal-footer">
      <span>族谱公开展示 · 游客可阅览 · 登录后按角色使用更多能力</span>
    </footer>
  </div>
</template>

<style scoped>
.portal-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(ellipse at top, rgba(47, 93, 70, 0.12), transparent 55%),
    linear-gradient(180deg, #f3efe6 0%, #e8e0d2 100%);
  color: #1f2a24;
}

.portal-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 28px;
  border-bottom: 1px solid rgba(36, 70, 54, 0.12);
  background: rgba(255, 252, 247, 0.86);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(145deg, #2f5d46, #1b3428);
  color: #f7f2e8;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 20px;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: #1b3428;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  font-size: 12px;
  color: #6b7a71;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.portal-nav {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.nav-link {
  padding: 8px 14px;
  border-radius: 999px;
  text-decoration: none;
  color: #3d5348;
  font-size: 14px;
  font-weight: 600;
}

.nav-link.active {
  background: rgba(47, 93, 70, 0.12);
  color: #1b3428;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-chip {
  font-size: 13px;
  color: #3d5348;
  display: flex;
  align-items: center;
  gap: 6px;
}

.role-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(47, 93, 70, 0.1);
  color: #1b3428;
}

.admin-link {
  border: 1px solid rgba(36, 70, 54, 0.2);
  background: transparent;
  color: #2f5d46;
  border-radius: 999px;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 13px;
}

.admin-link:hover {
  background: rgba(47, 93, 70, 0.08);
}

.portal-main {
  flex: 1;
  width: min(1200px, 100%);
  margin: 0 auto;
  padding: 24px 20px 40px;
}

.portal-footer {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: #7a887f;
  border-top: 1px solid rgba(36, 70, 54, 0.08);
}

@media (max-width: 720px) {
  .portal-header {
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px 16px;
  }

  .portal-nav {
    order: 3;
    width: 100%;
    margin-left: 0;
  }

  .header-actions {
    margin-left: auto;
  }
}
</style>
