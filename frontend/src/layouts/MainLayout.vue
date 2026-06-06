<template>
  <el-container class="main-layout">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar-container">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header class="navbar-container">
        <Navbar />
      </el-header>
      <el-main class="main-content">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { computed } from 'vue'
import Sidebar from './Sidebar.vue'
import Navbar from './Navbar.vue'

const appStore = useAppStore()
const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
</script>

<style scoped>
.main-layout { height: 100vh; }
.sidebar-container { background: #304156; overflow: hidden; transition: width 0.3s; }
.navbar-container { background: #fff; border-bottom: 1px solid #e6e6e6; padding: 0 20px; height: 60px; display: flex; align-items: center; }
.main-content { background: #f0f2f5; padding: 20px; overflow-y: auto; }
</style>
