<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>运维数字员工门户</h2>
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="账号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width:100%">登 录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
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
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await authApi.login(form.username, form.password)
    const d = res.data
    userStore.setAuth(d.access_token, d.role, d.display_name, d.is_first_login)
    ElMessage.success('登录成功')
    if (d.is_first_login) ElMessage.warning('请尽快修改默认密码')
    if (d.role === 'operator') router.push('/qa')
    else if (d.role === 'expert') router.push('/tickets/pending')
    else if (d.role === 'admin') router.push('/dashboard')
  } catch (e: any) {
    const msg = e?.response?.data?.message || e?.message || '登录失败'
    ElMessage.error(msg)
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { width: 100%; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
.login-card { width: 400px; }
.login-card h2 { text-align: center; margin-bottom: 24px; color: #303133; }
</style>
