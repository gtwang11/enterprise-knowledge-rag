<template>
  <div class="sidebar">
    <div class="logo">
      <span v-if="!appStore.sidebarCollapsed">运维数字员工</span>
      <span v-else>运维</span>
    </div>
    <el-menu
      :default-active="currentRoute"
      :collapse="appStore.sidebarCollapsed"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
      router
    >
      <el-menu-item index="/qa">
        <el-icon><ChatDotRound /></el-icon>
        <span>自助问答</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.role === 'operator'" index="/tickets/my">
        <el-icon><Document /></el-icon>
        <span>我的工单</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.role === 'expert'" index="/tickets/pending">
        <el-icon><List /></el-icon>
        <span>工单处理</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.role === 'admin'" index="/tickets/all">
        <el-icon><List /></el-icon>
        <span>工单管理</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.role === 'admin' || userStore.role === 'expert'" index="/faq">
        <el-icon><Collection /></el-icon>
        <span>知识库</span>
      </el-menu-item>
      <el-menu-item v-if="userStore.role === 'admin'" index="/users">
        <el-icon><User /></el-icon>
        <span>账号管理</span>
      </el-menu-item>
      <el-menu-item index="/dashboard">
        <el-icon><DataAnalysis /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()
const currentRoute = computed(() => route.path)
</script>

<style scoped>
.logo { height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold; }
.el-menu { border-right: none; }
</style>
