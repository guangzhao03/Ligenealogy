<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function handleSubmit() {
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push(authStore.homePathAfterLogin())
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-panel page-card">
      <div class="auth-header">
        <div class="seal">谱</div>
        <div>
          <h1>族谱管理系统</h1>
          <p>传承家族脉络，记录世代荣光</p>
        </div>
      </div>

      <el-form label-width="70px" @submit.prevent="handleSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-button type="primary" class="submit-btn" :loading="loading" @click="handleSubmit">
          登录
        </el-button>
        <div class="footer-link">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
          <span class="sep">·</span>
          <router-link to="/portal">进入族谱展厅</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background:
    linear-gradient(rgba(47, 93, 70, 0.18), rgba(47, 93, 70, 0.18)),
    url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"><rect fill="%23f4efe4" width="800" height="400"/><path d="M0 280 C200 180 300 320 500 220 C650 140 720 180 800 120 L800 400 L0 400 Z" fill="%23e8ddc8"/></svg>')
      center/cover;
}

.auth-panel {
  width: 420px;
}

.auth-header {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
}

.seal {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 28px;
  font-weight: 700;
}

.auth-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--primary-dark);
}

.auth-header p {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 13px;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
}

.footer-link {
  margin-top: 16px;
  text-align: center;
  color: var(--text-muted);
}

.footer-link a {
  color: var(--primary);
}

.sep {
  margin: 0 8px;
  color: var(--text-muted);
}
</style>
