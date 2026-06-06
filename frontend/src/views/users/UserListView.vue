<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="filters.username" placeholder="账号名" clearable style="width:140px" />
      <el-input v-model="filters.display_name" placeholder="姓名" clearable style="width:140px" />
      <el-select v-model="filters.role" placeholder="角色" clearable style="width:120px"><el-option label="一线运维" value="operator" /><el-option label="资深专家" value="expert" /><el-option label="管理员" value="admin" /></el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:100px"><el-option label="正常" value="active" /><el-option label="冻结" value="frozen" /></el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <div style="flex:1" />
      <el-button type="primary" @click="$router.push('/users/create')">创建账号</el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="username" label="账号名" width="120" />
      <el-table-column prop="display_name" label="姓名" width="100" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column prop="role" label="角色" width="100"><template #default="{row}">{{ {operator:'一线运维',expert:'资深专家',admin:'管理员'}[row.role] }}</template></el-table-column>
      <el-table-column prop="status" label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='active'?'success':'danger'" size="small">{{ row.status==='active'?'正常':'冻结' }}</el-tag></template></el-table-column>
      <el-table-column prop="last_login_at" label="最后登录" width="170" />
      <el-table-column label="操作" width="240">
        <template #default="{row}">
          <el-button type="primary" link @click="$router.push(`/users/${row.id}/edit`)">编辑</el-button>
          <el-button :type="row.status==='active'?'warning':'success'" link @click="handleToggle(row)">{{ row.status==='active'?'冻结':'解冻' }}</el-button>
          <el-button type="danger" link @click="handleReset(row)">重置密码</el-button>
          <el-button v-if="row.username !== 'admin'" type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" @current-change="load" layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { userApi } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([]); const loading = ref(false); const total = ref(0); const page = ref(1)
const filters = reactive({ username: '', display_name: '', role: '', status: '' })

async function load() { loading.value = true; try { const res = await userApi.list({ page: page.value, ...filters }); list.value = res.data.items; total.value = res.data.total } catch (_) {} finally { loading.value = false } }

async function handleToggle(row: any) {
  const action = row.status === 'active' ? '冻结' : '解冻'
  try { await ElMessageBox.confirm(`确认${action}账号 ${row.username}？`); await userApi.toggleStatus(row.id); ElMessage.success(`已${action}`); load() } catch (_) {}
}

async function handleReset(row: any) {
  try { await ElMessageBox.confirm(`确认重置账号 ${row.username} 的密码？`); const res = await userApi.resetPassword(row.id); ElMessage.success(`新密码：${res.data.new_password}`) } catch (_) {}
}
async function handleDelete(row: any) {
  try { await ElMessageBox.confirm(`确认永久删除账号 ${row.username}？此操作不可恢复`, '警告', { type: 'warning', confirmButtonText: '确认删除' }); await userApi.delete(row.id); ElMessage.success('已删除'); load() } catch (_) {}
}
load()
</script>
