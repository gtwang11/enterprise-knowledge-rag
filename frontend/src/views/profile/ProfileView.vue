<template>
  <div class="page-container" style="max-width:500px">
    <h3>修改密码</h3>
    <el-form :model="form" ref="formRef" :rules="rules" style="margin-top:20px">
      <el-form-item label="原密码" prop="old_password"><el-input v-model="form.old_password" type="password" show-password /></el-form-item>
      <el-form-item label="新密码" prop="new_password"><el-input v-model="form.new_password" type="password" show-password /><span style="font-size:12px;color:#909399">至少8位，含大小写字母、数字、特殊字符至少3类</span></el-form-item>
      <el-form-item label="确认密码" prop="confirm_password"><el-input v-model="form.confirm_password" type="password" show-password /></el-form-item>
      <el-form-item><el-button type="primary" @click="handleChange" :loading="loading">修改密码</el-button></el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const formRef = ref()
const form = reactive({ old_password: '', new_password: '', confirm_password: '' })
const rules = {
  old_password: [{ required: true, message: '请输入原密码' }],
  new_password: [{ required: true, min: 8, message: '至少8位' }],
  confirm_password: [{ required: true, message: '请确认新密码' }],
}

async function handleChange() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (form.new_password !== form.confirm_password) { ElMessage.error('两次输入的密码不一致'); return }
  loading.value = true
  try {
    await authApi.changePassword(form.old_password, form.new_password, form.confirm_password)
    ElMessage.success('密码已修改，请重新登录')
    userStore.clearAuth()
    router.push('/login')
  } catch (_) {} finally { loading.value = false }
}
</script>
