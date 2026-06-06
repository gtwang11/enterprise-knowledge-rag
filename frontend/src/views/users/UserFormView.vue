<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/users')" :content="isEdit ? '编辑账号' : '创建账号'" />
    <el-form :model="form" label-width="80px" style="margin-top:20px;max-width:600px" ref="formRef" :rules="rules">
      <el-form-item label="账号名" prop="username"><el-input v-model="form.username" :disabled="isEdit" maxlength="20" /></el-form-item>
      <el-form-item label="姓名" prop="display_name"><el-input v-model="form.display_name" maxlength="50" /></el-form-item>
      <el-form-item label="手机号" prop="phone"><el-input v-model="form.phone" maxlength="11" /></el-form-item>
      <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
      <el-form-item label="部门" prop="department"><el-input v-model="form.department" /></el-form-item>
      <el-form-item label="角色" prop="role"><el-select v-model="form.role"><el-option label="一线运维人员" value="operator" /><el-option label="资深运维专家" value="expert" /></el-select></el-form-item>
      <el-form-item><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button><el-button @click="$router.push('/users')">取消</el-button></el-form-item>
    </el-form>
    <div v-if="initialPassword" style="margin-top:20px">
      <el-alert :title="`账号创建成功！初始密码：${initialPassword}`" type="success" :closable="false"><template #default><p>请记录此密码并告知用户，首次登录后需修改。</p></template></el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { ElMessage } from 'element-plus'

const route = useRoute(); const router = useRouter()
const isEdit = ref(!!route.params.id)
const saving = ref(false)
const formRef = ref()
const initialPassword = ref('')
const form = reactive({ username: '', display_name: '', phone: '', email: '', department: '', role: 'operator' })
const rules = {
  username: [{ required: true, message: '请输入账号名' }, { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: '3-20位字母数字下划线' }],
  display_name: [{ required: true, message: '请输入姓名' }],
  phone: [{ required: true, pattern: /^\d{11}$/, message: '请输入11位手机号' }],
  department: [{ required: true, message: '请输入部门' }],
  role: [{ required: true, message: '请选择角色' }],
}

onMounted(async () => { if (isEdit.value) { const res = await userApi.get(Number(route.params.id)); Object.assign(form, res.data) } })

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return; saving.value = true
  try {
    if (isEdit.value) {
      await userApi.update(Number(route.params.id), form)
      ElMessage.success('已更新'); router.push('/users')
    } else {
      const res = await userApi.create(form)
      initialPassword.value = res.data.initial_password
      ElMessage.success('已创建')
    }
  } catch (_) {} finally { saving.value = false }
}
</script>
