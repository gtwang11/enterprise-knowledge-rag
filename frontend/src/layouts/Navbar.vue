<template>
  <div class="navbar">
    <div class="left">
      <el-icon class="collapse-btn" @click="appStore.toggleSidebar" :size="20">
        <Fold v-if="!appStore.sidebarCollapsed" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="right">
      <span class="user-info">{{ userStore.displayName }} ({{ roleLabel }})</span>
      <el-button type="primary" link @click="$router.push('/profile')">修改密码</el-button>
      <el-button type="danger" link @click="handleLogout">退出</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const roleLabel = computed(() => {
  const map: Record<string, string> = { operator: '一线运维', expert: '资深专家', admin: '管理员' }
  return map[userStore.role] || userStore.role
})

async function handleLogout() {
  try { await authApi.logout() } catch (_) { /* ignore */ }
  userStore.clearAuth()
  router.push('/login')
  ElMessage.success('已退出登录')
}
</script>

<style scoped>
.navbar { width: 100%; display: flex; justify-content: space-between; align-items: center; }
.left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { cursor: pointer; }
.right { display: flex; align-items: center; gap: 12px; }
.user-info { color: #606266; }
</style>
