<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/faq')" :content="isEdit ? '编辑FAQ' : '新增FAQ'" />
    <el-form :model="form" label-width="80px" style="margin-top:20px;max-width:800px" ref="formRef" :rules="rules">
      <el-form-item label="问题" prop="question"><el-input v-model="form.question" maxlength="500" show-word-limit /></el-form-item>
      <el-form-item label="分类" prop="category"><el-select v-model="form.category"><el-option v-for="c in categories" :key="c" :label="c" :value="c" /></el-select></el-form-item>
      <el-form-item label="答案" prop="answer"><el-input v-model="form.answer" type="textarea" :rows="10" maxlength="10000" show-word-limit /></el-form-item>
      <el-form-item label="标签"><el-input v-model="form.tags" placeholder="逗号分隔，最多5个" /></el-form-item>
      <el-form-item label="关键词"><el-input v-model="form.keywords" placeholder="逗号分隔，用于搜索匹配" /></el-form-item>
      <el-form-item v-if="isEdit" label="状态"><el-radio-group v-model="form.status"><el-radio value="published">已发布</el-radio><el-radio value="draft">草稿</el-radio></el-radio-group></el-form-item>
      <el-form-item><el-button type="primary" @click="handleSave" :loading="saving">保存</el-button><el-button @click="$router.push('/faq')">取消</el-button></el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { faqApi } from '@/api/faq'
import { ElMessage } from 'element-plus'

const route = useRoute(); const router = useRouter()
const isEdit = ref(!!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ question: '', answer: '', category: '', tags: '', keywords: '', status: 'published' })
const categories = ['账号问题', '网络问题', '硬件故障', '软件故障', '权限问题', '安全合规', '系统配置', '其他']
const rules = { question: [{ required: true, message: '请输入问题' }], answer: [{ required: true, message: '请输入答案' }], category: [{ required: true, message: '请选择分类' }] }

onMounted(async () => { if (isEdit.value) { const res = await faqApi.get(Number(route.params.id)); const d = res.data; Object.assign(form, { question: d.question, answer: d.answer, category: d.category, tags: d.tags || '', keywords: d.keywords || '', status: d.status }) } })

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return; saving.value = true
  const data = { question: form.question, answer: form.answer, category: form.category, tags: form.tags || null, keywords: form.keywords || null, status: form.status }
  try {
    if (isEdit.value) await faqApi.update(Number(route.params.id), data)
    else await faqApi.create(data)
    ElMessage.success(isEdit.value ? '已更新' : '已创建')
    router.push('/faq')
  } catch (_) {} finally { saving.value = false }
}
</script>
