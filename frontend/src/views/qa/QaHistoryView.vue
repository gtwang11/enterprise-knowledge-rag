<template>
  <div class="page-container">
    <h3>问答历史记录</h3>
    <div class="search-bar" style="margin:16px 0">
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="load" style="width:260px" />
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="question" label="问题" show-overflow-tooltip min-width="200" />
      <el-table-column prop="answer" label="AI回答" show-overflow-tooltip min-width="300">
        <template #default="{ row }">
          <span v-if="row.has_answer">{{ row.answer }}</span>
          <el-tag v-else type="warning" size="small">未找到答案</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="similarity_score" label="相似度" width="90">
        <template #default="{ row }">{{ row.similarity_score ? (row.similarity_score * 100).toFixed(1) + '%' : '-' }}</template>
      </el-table-column>
      <el-table-column prop="processing_time_ms" label="耗时" width="80">
        <template #default="{ row }">{{ row.processing_time_ms }}ms</template>
      </el-table-column>
      <el-table-column prop="created_at" label="提问时间" width="170" />
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" @current-change="load" layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { qaApi } from '@/api/qa'
import { ElMessage } from 'element-plus'

const list = ref([]); const loading = ref(false); const total = ref(0); const page = ref(1)
const dateRange = ref<any>(null)

async function load() {
  loading.value = true
  const params: any = { page: page.value, page_size: 20 }
  if (dateRange.value) {
    params.start_date = dateRange.value[0].toISOString().slice(0, 10)
    params.end_date = dateRange.value[1].toISOString().slice(0, 10)
  }
  try {
    const res = await qaApi.history(params)
    list.value = res.data.items; total.value = res.data.total
  } catch (_) {} finally { loading.value = false }
}
load()
</script>
