<template>
  <EmptyLayout v-if="route.path === '/login' || route.path === '/403'">
    <router-view />
  </EmptyLayout>
  <MainLayout v-else>
    <router-view />
  </MainLayout>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import EmptyLayout from '@/layouts/EmptyLayout.vue'

const route = useRoute()
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  font-family: 'Microsoft YaHei', sans-serif;
}
</style>
