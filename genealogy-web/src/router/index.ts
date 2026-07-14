import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/portal',
      component: () => import('@/components/layout/PortalLayout.vue'),
      meta: { public: true, portal: true },
      children: [
        {
          path: '',
          name: 'portal-home',
          component: () => import('@/views/portal/PortalHomeView.vue'),
          meta: { public: true, portal: true },
        },
        {
          path: 'tree',
          name: 'portal-tree',
          component: () => import('@/views/portal/PortalTreeView.vue'),
          meta: { public: true, portal: true },
        },
        {
          path: 'search',
          name: 'portal-search',
          component: () => import('@/views/portal/PortalSearchView.vue'),
          meta: { public: true, portal: true },
        },
        {
          path: 'map',
          name: 'portal-map',
          component: () => import('@/views/portal/PortalMapView.vue'),
          meta: { public: true, portal: true },
        },
        {
          path: 'person/:id',
          name: 'portal-person',
          component: () => import('@/views/portal/PortalPersonView.vue'),
          meta: { public: true, portal: true },
        },
      ],
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      meta: { requiresAdmin: true },
      redirect: '/families',
      children: [
        {
          path: 'families',
          name: 'families',
          component: () => import('@/views/family/FamilyView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'persons',
          name: 'persons',
          component: () => import('@/views/person/PersonView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'tree',
          name: 'tree',
          component: () => import('@/views/tree/TreeView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'import-export',
          name: 'import-export',
          component: () => import('@/views/import/ImportExportView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'geo-places',
          name: 'geo-places',
          component: () => import('@/views/geo/GeoPlaceView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/user/UserRoleView.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (to.meta.public) {
    if (authStore.token && (to.name === 'login' || to.name === 'register')) {
      if (!authStore.user) {
        try {
          await authStore.fetchProfile()
        } catch {
          authStore.logout()
          return true
        }
      }
      return authStore.homePathAfterLogin()
    }
    return true
  }

  if (!authStore.token) {
    return '/login'
  }

  if (!authStore.user) {
    try {
      await authStore.fetchProfile()
    } catch {
      authStore.logout()
      return '/login'
    }
  }

  if (to.meta.requiresAdmin && !authStore.canAccessAdmin) {
    ElMessage.warning('需要管理员权限才能进入后台')
    return '/portal'
  }

  return true
})

export default router
