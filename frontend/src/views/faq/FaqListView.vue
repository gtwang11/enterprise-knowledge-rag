<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="filters.keyword" placeholder="搜索问题..." clearable @clear="load" @keyup.enter="load" style="width:200px" />
      <el-select v-model="filters.category" placeholder="分类" clearable @change="load" style="width:140px">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable @change="load" style="width:120px">
        <el-option label="已发布" value="published" /><el-option label="草稿" value="draft" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <div style="flex:1" />
      <el-button v-if="userStore.role === 'admin'" @click="$router.push('/faq/create')">新增FAQ</el-button>
      <el-button v-if="userStore.role === 'admin'" @click="$router.push('/faq/import')">批量导入</el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading" @selection-change="(rows: any) => selected = rows.map((r: any) => r.id)">
      <el-table-column v-if="userStore.role === 'admin'" type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="question" label="问题" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="status" label="状态" width="80"><template #default="{row}"><el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">{{ row.status === 'published' ? '已发布' : '草稿' }}</el-tag></template></el-table-column>
      <el-table-column prop="version" label="版本" width="60" />
      <el-table-column prop="updated_at" label="更新时间" width="170" />
      <el-table-column v-if="userStore.role === 'admin'" label="操作" width="180">
        <template #default="{row}">
          <el-button type="primary" link @click="$router.push(`/faq/${row.id}/edit`)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="display:flex;justify-content:space-between;align-items:center">
      <el-button v-if="userStore.role === 'admin' && selected.length" type="danger" @click="handleBatchDelete" size="small">批量删除({{ selected.length }})</el-button>
      <el-pagination v-model:current-page="page" :total="total" :page-size="20" @current-change="load" layout="total, prev, pager, next" style="margin-top:16px" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import { faqApi } from '@/api/faq'
import { ElMessage, ElMessageBox } from 'element-plus'

const userStore = useUserStore()
const list = ref([]); const loading = ref(false); const total = ref(0); const page = ref(1)
const selected = ref<number[]>([])
const filters = reactive({ keyword: '', category: '', status: '' })
const categories = ['账号问题', '网络问题', '硬件故障', '软件故障', '权限问题', '安全合规', '系统配置', '其他']

async function load() { loading.value = true; try { const res = await faqApi.list({ page: page.value, ...filters }); list.value = res.data.items; total.value = res.data.total } catch (_) {} finally { loading.value = false } }
async function handleDelete(id: number) { try { await ElMessageBox.confirm('确认删除该FAQ？此操作不可恢复', '确认', { type: 'warning' }); await faqApi.delete(id); ElMessage.success('已删除'); load() } catch (_) {} }
async function handleBatchDelete() { try { await ElMessageBox.confirm(`确认删除 ${selected.value.length} 条FAQ？`, '确认', { type: 'warning' }); await faqApi.batchDelete(selected.value); ElMessage.success('已删除'); selected.value = []; load() } catch (_) {} }
load()
</script>
