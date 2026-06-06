<template>
  <div class="page-container">
    <div class="search-bar">
      <el-select v-model="filters.status" placeholder="状态" clearable @change="load">
        <el-option label="待处理" value="pending" /><el-option label="处理中" value="processing" />
        <el-option label="待回访确认" value="pending_confirmation" /><el-option label="已完成" value="completed" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="搜索问题..." clearable @keyup.enter="load" style="width:200px" />
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="ticket_no" label="工单编号" width="180" />
      <el-table-column prop="question" label="问题" show-overflow-tooltip />
      <el-table-column prop="urgency" label="紧急程度" width="100">
        <template #default="{ row }"><el-tag :type="row.urgency==='emergency'?'danger':row.urgency==='urgent'?'warning':'info'" size="small">{{ {normal:'一般',urgent:'紧急',emergency:'特急'}[row.urgency] }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="170" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" link @click="$router.push(`/tickets/${row.id}`)">详情</el-button>
          <el-popconfirm title="确认删除此工单？" @confirm="handleDelete(row.id)">
            <template #reference><el-button type="danger" link>删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" @current-change="load" layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ticketApi } from '@/api/ticket'
import { ElMessage } from 'element-plus'

const list = ref([]); const loading = ref(false); const total = ref(0); const page = ref(1)
const filters = reactive({ status: '', keyword: '' })

function statusType(s: string) { const m: Record<string, string> = { pending: 'info', processing: 'warning', pending_confirmation: '', completed: 'success' }; return m[s] || 'info' }
function statusLabel(s: string) { const m: Record<string, string> = { pending: '待处理', processing: '处理中', pending_confirmation: '待回访确认', completed: '已完成' }; return m[s] || s }

async function load() {
  loading.value = true
  try {
    const res = await ticketApi.list({ page: page.value, status: filters.status || undefined, keyword: filters.keyword || undefined })
    list.value = res.data.items; total.value = res.data.total
  } catch (_) {} finally { loading.value = false }
}

async function handleDelete(id: number) {
  try { await ticketApi.delete(id); ElMessage.success('工单已删除'); load() } catch (_) {}
}
load()
</script>
