<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePortalStore } from '@/stores/portal'

const router = useRouter()
const portalStore = usePortalStore()
const loading = ref(false)

const family = computed(() => portalStore.family)
const stats = computed(() => family.value?.stats)

onMounted(async () => {
  loading.value = true
  try {
    await portalStore.ensureFamily()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载家族失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading" class="portal-home">
    <section v-if="family" class="hero">
      <p class="eyebrow">家族展厅</p>
      <h1 class="hero-title">{{ family.name }}</h1>
      <p class="hero-origin">{{ family.origin_place || '籍贯未载' }}</p>
      <p class="hero-desc">
        {{ family.description || '承先启后，谱系分明。欢迎浏览本族世系与人物档案。' }}
      </p>
      <div class="cta-row">
        <el-button type="primary" size="large" @click="router.push('/portal/tree')">
          浏览族谱
        </el-button>
        <el-button size="large" @click="router.push('/portal/search')">
          检索人物
        </el-button>
        <el-button size="large" @click="router.push('/portal/map')">
          族人分布地图
        </el-button>
      </div>
    </section>

    <section v-if="stats" class="stats">
      <div class="stat">
        <div class="stat-value">{{ stats.person_count }}</div>
        <div class="stat-label">在谱人数</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ stats.generation_span || '—' }}</div>
        <div class="stat-label">世代跨度</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ stats.male_count }}</div>
        <div class="stat-label">男性</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ stats.female_count }}</div>
        <div class="stat-label">女性</div>
      </div>
    </section>

    <el-empty v-else-if="!loading" description="暂无展示家族数据" />
  </div>
</template>

<style scoped>
.portal-home {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.hero {
  padding: clamp(32px, 8vw, 72px) 8px 24px;
  text-align: center;
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 13px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #6b7a71;
}

.hero-title {
  margin: 0;
  font-size: clamp(40px, 8vw, 64px);
  line-height: 1.1;
  font-weight: 800;
  color: #163a28;
  letter-spacing: 0.04em;
}

.hero-origin {
  margin: 16px 0 0;
  font-size: 18px;
  color: #2f5d46;
  font-weight: 600;
}

.hero-desc {
  margin: 18px auto 0;
  max-width: 520px;
  font-size: 15px;
  line-height: 1.7;
  color: #5a6b62;
}

.cta-row {
  margin-top: 28px;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat {
  text-align: center;
  padding: 20px 12px;
  border-radius: 14px;
  background: rgba(255, 252, 247, 0.75);
  border: 1px solid rgba(36, 70, 54, 0.1);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1b3428;
}

.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: #6b7a71;
}

@media (max-width: 720px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
