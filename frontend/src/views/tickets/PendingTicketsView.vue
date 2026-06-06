<template>
  <div class="page-container">
    <div class="search-bar">
      <el-select v-model="filters.status" placeholder="状态" clearable @change="load"><el-option label="待处理" value="pending" /><el-option label="处理中" value="processing" /><el-option label="待回访确认" value="pending_confirmation" /></el-select>
      <el-select v-model="filters.urgency" placeholder="紧急程度" clearable @change="load"><el-option label="一般" value="normal" /><el-option label="紧急" value="urgent" /><el-option label="特急" value="emergency" /></el-select>
    </div>
    <el-table :data="list" stripe v-loading="loading" @row-click="(row: any) => $router.push(`/tickets/${row.id}`)" style="cursor:pointer">
      <el-table-column prop="ticket_no" label="工单编号" width="180" />
      <el-table-column prop="question" label="问题" show-overflow-tooltip />
      <el-table-column prop="urgency" label="紧急程度" width="100">
        <template #default="{ row }"><el-tag :type="row.urgency === 'emergency' ? 'danger' : row.urgency === 'urgent' ? 'warning' : 'info'" size="small">{{ { normal: '一般', urgent: '紧急', emergency: '特急' }[row.urgency] }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.status === 'pending' ? 'info' : row.status === 'processing' ? 'warning' : ''" size="small">{{ {pending:'待处理',processing:'处理中',pending_confirmation:'待回访确认',completed:'已完成'}[row.status] || row.status }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="170" />
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" @current-change="load" layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ticketApi } from '@/api/ticket'
const list = ref([]); const loading = ref(false); const total = ref(0); const page = ref(1)
const filters = reactive({ status: '', urgency: '' })
async function load() { loading.value = true; try { const res = await ticketApi.list({ page: page.value, ...filters }); list.value = res.data.items; total.value = res.data.total } catch (_) {} finally { loading.value = false } }
load()
</script>
