<template>
  <div class="page-container" v-loading="loading">
    <template v-if="ticket">
      <el-page-header @back="$router.back()" :content="'工单 ' + ticket.ticket_no" />
      <el-descriptions :column="2" border style="margin:20px 0">
        <el-descriptions-item label="状态"><el-tag :type="statusType(ticket.status)">{{ statusLabel(ticket.status) }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="紧急程度"><el-tag :type="ticket.urgency === 'emergency' ? 'danger' : ticket.urgency === 'urgent' ? 'warning' : 'info'">{{ { normal: '一般', urgent: '紧急', emergency: '特急' }[ticket.urgency] }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="提交人">{{ ticket.submitter_name }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ ticket.handler_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ ticket.created_at }}</el-descriptions-item>
        <el-descriptions-item label="问题描述" :span="2">{{ ticket.question }}</el-descriptions-item>
        <el-descriptions-item v-if="ticket.supplementary" label="补充说明" :span="2">{{ ticket.supplementary }}</el-descriptions-item>
        <el-descriptions-item v-if="ticket.solution" label="处理方案" :span="2">{{ ticket.solution }}</el-descriptions-item>
        <el-descriptions-item v-if="ticket.reject_reason" label="退回原因" :span="2">{{ ticket.reject_reason }}</el-descriptions-item>
      </el-descriptions>

      <!-- 操作按钮 -->
      <div class="actions">
        <template v-if="userStore.role === 'expert' && ticket.status === 'pending'">
          <el-button type="primary" @click="handleClaim" :loading="actionLoading">领取工单</el-button>
        </template>
        <template v-if="userStore.role === 'expert' && ticket.status === 'processing' && ticket.handler_id === currentUserId">
          <div class="solution-area">
            <h4>填写处理方案</h4>
            <el-input v-model="solution" type="textarea" :rows="6" placeholder="请输入处理方案（支持 Markdown 格式）" />
            <div style="margin-top:12px;display:flex;gap:8px">
              <el-button type="primary" @click="handleSolution" :loading="actionLoading">提交方案</el-button>
              <el-button @click="rejectMode = !rejectMode">{{ rejectMode ? '取消退回' : '退回工单' }}</el-button>
            </div>
            <div v-if="rejectMode" style="margin-top:12px">
              <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入退回原因" />
              <el-button type="warning" @click="handleReject" :loading="actionLoading" style="margin-top:8px">确认退回</el-button>
            </div>
          </div>
        </template>
        <template v-if="canConfirmTicket">
          <el-button type="success" @click="handleConfirm" :loading="actionLoading">确认解决</el-button>
          <el-button type="warning" @click="handleUnconfirm" :loading="actionLoading">未解决</el-button>
        </template>
        <template v-if="(userStore.role === 'expert' || userStore.role === 'admin') && ticket.status === 'completed'">
          <el-button type="primary" @click="showPublishDialog = true">录入知识库</el-button>
        </template>
      </div>

      <!-- 时间线 -->
      <el-divider>处理记录</el-divider>
      <el-timeline v-if="ticket.timeline?.length">
        <el-timeline-item v-for="t in ticket.timeline" :key="t.created_at" :timestamp="t.created_at">
          {{ t.operator_name }} - {{ actionLabel(t.action) }} {{ t.comment ? '：' + t.comment : '' }}
        </el-timeline-item>
      </el-timeline>
    </template>

    <!-- 录入知识库弹窗 -->
    <el-dialog v-model="showPublishDialog" title="录入知识库" width="600px">
      <el-form label-width="80px">
        <el-form-item label="问题"><el-input v-model="publishForm.question" /></el-form-item>
        <el-form-item label="答案"><el-input v-model="publishForm.answer" type="textarea" :rows="5" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="publishForm.category" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showPublishDialog = false">取消</el-button><el-button type="primary" @click="handlePublish">录入</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ticketApi } from '@/api/ticket'
import { ElMessage } from 'element-plus'

const route = useRoute()
const userStore = useUserStore()
const ticket = ref<any>(null)
const loading = ref(false)
const showSolutionDialog = ref(false)
const showRejectDialog = ref(false)
const rejectMode = ref(false)
const showPublishDialog = ref(false)
const solution = ref('')
const rejectReason = ref('')
const publishForm = reactive({ question: '', answer: '', category: '工单转换' })
const currentUserId = ref(0)
const canConfirmTicket = computed(() => {
  return ['operator', 'admin'].includes(userStore.role)
    && ticket.value?.status === 'pending_confirmation'
    && ticket.value?.submitter_id === currentUserId.value
})

// Parse user ID from JWT token (stored in localStorage)
function getUserIdFromToken(): number {
  try {
    const token = userStore.token || localStorage.getItem('token') || ''
    const payload = JSON.parse(atob(token.split('.')[1]))
    return parseInt(payload.sub) || 0
  } catch { return 0 }
}

function statusType(s: string) { const m: Record<string, string> = { pending: 'info', processing: 'warning', pending_confirmation: '', completed: 'success' }; return m[s] || 'info' }
function statusLabel(s: string) { const m: Record<string, string> = { pending: '待处理', processing: '处理中', pending_confirmation: '待回访确认', completed: '已完成' }; return m[s] || s }
function actionLabel(a: string) { const m: Record<string, string> = { submit: '提交工单', claim: '领取工单', solution: '提交方案', reject: '退回工单', confirm: '确认解决', unconfirm: '反馈未解决', publish_faq: '录入知识库' }; return m[a] || a }

async function load() {
  loading.value = true
  currentUserId.value = getUserIdFromToken()
  try {
    const res = await ticketApi.get(Number(route.params.id))
    ticket.value = res.data
    publishForm.question = res.data.question
    publishForm.answer = res.data.solution || ''
  } catch (_) {} finally { loading.value = false }
}

const actionLoading = ref(false)
async function handleClaim() { actionLoading.value = true; try { await ticketApi.claim(ticket.value.id); ElMessage.success('已领取'); load() } catch (_) {} finally { actionLoading.value = false } }
async function handleSolution() { if (!solution.value) return; actionLoading.value = true; try { await ticketApi.submitSolution(ticket.value.id, solution.value); ElMessage.success('方案已提交'); load() } catch (_) {} finally { actionLoading.value = false } }
async function handleReject() { if (!rejectReason.value) { ElMessage.warning('请填写退回原因'); return }; actionLoading.value = true; try { await ticketApi.reject(ticket.value.id, rejectReason.value); ElMessage.success('已退回'); rejectMode.value = false; load() } catch (_) {} finally { actionLoading.value = false } }
async function handleConfirm() { actionLoading.value = true; try { await ticketApi.confirm(ticket.value.id); ElMessage.success('已确认解决'); load() } catch (_) {} finally { actionLoading.value = false } }
async function handleUnconfirm() { actionLoading.value = true; try { await ticketApi.unconfirm(ticket.value.id); ElMessage.success('已反馈未解决'); load() } catch (_) {} finally { actionLoading.value = false } }
async function handlePublish() { actionLoading.value = true; try { await ticketApi.publishToFaq(ticket.value.id, publishForm); ElMessage.success('已录入知识库'); showPublishDialog.value = false; load() } catch (_) {} finally { actionLoading.value = false } }

onMounted(load)
</script>
