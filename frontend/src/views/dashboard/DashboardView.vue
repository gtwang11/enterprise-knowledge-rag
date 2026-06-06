<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">{{ roleLabel }}工作台</h3>
    <div class="stat-cards">
      <div v-for="card in cards" :key="card.label" class="stat-card">
        <div class="stat-value">{{ card.value }}</div>
        <div class="stat-label">{{ card.label }}</div>
      </div>
    </div>
    <div v-if="userStore.role === 'admin' || userStore.role === 'expert'" style="margin-top:20px">
      <h4>近7天趋势</h4>
      <div ref="chartRef" style="width:100%;height:300px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { dashboardApi } from '@/api/dashboard'
import * as echarts from 'echarts'

const userStore = useUserStore()
const data = ref<any>({})
const chartRef = ref<HTMLElement>()

const roleLabel = computed(() => ({ operator: '一线运维', expert: '资深专家', admin: '管理员' }[userStore.role] || ''))

const cards = computed(() => {
  const d = data.value
  if (userStore.role === 'operator') return [
    { label: '待处理工单', value: d.pending_count || 0 },
    { label: '处理中', value: d.processing_count || 0 },
    { label: '已完成', value: d.completed_count || 0 },
  ]
  if (userStore.role === 'expert') return [
    { label: '待处理总数', value: d.pending_total || 0 },
    { label: '我处理中', value: d.my_processing || 0 },
    { label: '待回访确认', value: d.my_awaiting || 0 },
    { label: '我已完成', value: d.my_completed || 0 },
  ]
  return [
    { label: '总账号数', value: d.total_users || 0 },
    { label: '活跃账号', value: d.active_users || 0 },
    { label: 'FAQ总数', value: d.total_faqs || 0 },
    { label: '今日问答', value: d.today_qa_count || 0 },
    ...(d.ticket_stats ? [
      { label: '待处理工单', value: d.ticket_stats.pending || 0 },
      { label: '已完成工单', value: d.ticket_stats.completed || 0 },
    ] : []),
  ]
})

onMounted(async () => {
  try { const res = await dashboardApi.get(); data.value = res.data } catch (_) {}
  await nextTick()
  if (chartRef.value) {
    const chart = echarts.init(chartRef.value)
    const trend = data.value.trend_7days || data.value.qa_trend_7days || []
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: trend.map((t: any) => t.date) },
      yAxis: { type: 'value' },
      series: [{ data: trend.map((t: any) => t.count), type: 'line', smooth: true, areaStyle: {} }],
    })
  }
})
</script>

<style scoped>
.stat-card { background: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
.stat-value { font-size: 32px; font-weight: bold; color: #409EFF; }
.stat-label { font-size: 14px; color: #909399; margin-top: 8px; }
</style>
