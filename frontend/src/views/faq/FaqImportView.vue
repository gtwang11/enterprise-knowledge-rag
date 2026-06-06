<template>
  <div class="page-container">
    <el-page-header @back="$router.push('/faq')" content="批量导入FAQ" />
    <div style="margin:20px 0">
      <el-upload :auto-upload="false" :on-change="onFileSelect" :limit="1" accept=".xlsx,.csv,.json" drag :show-file-list="true">
        <el-icon><UploadFilled /></el-icon>
        <div>拖拽或点击上传 Excel/CSV/JSON 文件</div>
        <template #tip><div style="margin-top:8px">支持 .xlsx、.csv 和 .json 格式，<el-button type="primary" link @click="downloadTemplate">下载模板</el-button></div></template>
      </el-upload>
    </div>
    <div v-if="selectedFile" style="margin-bottom:20px">
      <el-button type="primary" @click="doImport" :loading="importing" size="large">
        {{ importing ? '导入中...' : `确认导入 ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)` }}
      </el-button>
    </div>
    <div v-if="result">
      <el-alert :title="`成功导入 ${result.success_count} 条，跳过 ${result.skip_count} 条`" :type="result.errors?.length ? 'warning' : 'success'" closable />
      <div v-if="result.errors?.length" style="margin-top:12px;max-height:300px;overflow-y:auto">
        <h4>错误记录：</h4>
        <ul><li v-for="(e, i) in result.errors" :key="i">{{ e }}</li></ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { faqApi } from '@/api/faq'
import { ElMessage } from 'element-plus'

const result = ref<any>(null)
const selectedFile = ref<any>(null)
const importing = ref(false)

function onFileSelect(file: any) {
  selectedFile.value = file.raw
}

async function doImport() {
  if (!selectedFile.value) return
  importing.value = true
  result.value = null
  try {
    const res = await faqApi.importFile(selectedFile.value)
    result.value = res.data
    ElMessage.success(res.message)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.message || '导入失败')
  } finally {
    importing.value = false
  }
}

function downloadTemplate() {
  const sample = JSON.stringify([
    { question: "账号被冻结了怎么处理？", answer: "请访问 http://itsm.company.com/unfreeze 自助解冻。", category: "账号问题", keywords: "冻结,解冻" }
  ], null, 2)
  const blob = new Blob([sample], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = 'FAQ导入模板.json'; a.click()
}
</script>
