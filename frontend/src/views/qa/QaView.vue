<template>
  <div class="qa-page">
    <div class="chat-container">
      <div class="chat-messages" ref="msgContainer">
        <div v-if="messages.length === 0" class="welcome">
          <h3>👋 欢迎使用运维智能助手</h3>
          <p>您可以尝试以下问题：</p>
          <div class="examples">
            <el-tag v-for="q in sampleQuestions" :key="q" @click="question = q; sendQuestion()" style="cursor:pointer;margin:4px">{{ q }}</el-tag>
          </div>
        </div>
        <div v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role">
          <div class="avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
          <div class="bubble">
            <div v-if="msg.role === 'assistant'" v-html="formatAnswer(msg.content)"></div>
            <div v-else>{{ msg.content }}</div>
            <div v-if="msg.role === 'assistant' && msg.references?.length" class="refs">
              <span style="color:#909399;font-size:12px">参考来源：</span>
              <el-tag v-for="r in msg.references" :key="r.faq_id" size="small" type="info" style="margin:2px">FAQ #{{ r.faq_id }}</el-tag>
            </div>
            <div v-if="msg.role === 'assistant' && !msg.hasAnswer" class="no-answer">
              <el-button type="warning" size="small" @click="createTicketFromMsg(msg)">创建工单</el-button>
            </div>
          </div>
        </div>
        <div v-if="thinking" class="message assistant">
          <div class="avatar">AI</div>
          <div class="bubble"><em>AI 正在思考...</em></div>
        </div>
      </div>
      <div class="chat-input">
        <el-input v-model="question" :rows="3" type="textarea" placeholder="输入运维问题，如：交换机端口告警怎么排查？" @keyup.enter.exact="sendQuestion" :disabled="thinking" />
        <div class="input-actions">
          <el-button @click="openManualTicket" size="small">转人工服务</el-button>
          <el-button @click="loadHistory" size="small">历史记录</el-button>
          <el-button type="primary" @click="sendQuestion" :loading="thinking" size="small">发送</el-button>
        </div>
      </div>
    </div>

    <!-- 问答历史侧边栏 -->
    <el-drawer v-model="showHistory" title="问答历史" direction="rtl" size="400px">
      <div v-if="historyList.length === 0" style="text-align:center;color:#909399;padding:40px">暂无历史记录</div>
      <div v-for="h in historyList" :key="h.id" style="padding:12px;border-bottom:1px solid #eee">
        <div style="font-size:14px;font-weight:500;margin-bottom:4px;cursor:pointer" @click="h._expanded = !h._expanded">
          {{ h.question }}
          <span style="color:#409EFF;font-size:12px">{{ h._expanded ? '收起' : '展开' }}</span>
        </div>
        <div v-if="h._expanded" style="margin-top:8px;padding:8px;background:#f5f7fa;border-radius:4px;font-size:13px;line-height:1.6">
          <div v-if="h.has_answer">{{ h.answer }}</div>
          <el-tag v-else type="warning" size="small">未找到答案</el-tag>
        </div>
        <div style="font-size:12px;color:#909399;display:flex;justify-content:space-between;margin-top:4px">
          <span>{{ h.has_answer ? 'AI已回答' : '未找到答案' }}</span>
          <span>{{ h.created_at }}</span>
        </div>
      </div>
    </el-drawer>

    <!-- 创建工单弹窗 -->
    <el-dialog v-model="showTicketDialog" title="提交工单" width="500px">
      <el-form :model="ticketForm" label-width="80px">
        <el-form-item label="问题描述"><el-input v-model="ticketForm.question" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="补充说明"><el-input v-model="ticketForm.supplementary" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="紧急程度"><el-select v-model="ticketForm.urgency"><el-option label="一般" value="normal" /><el-option label="紧急" value="urgent" /><el-option label="特急" value="emergency" /></el-select></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTicketDialog = false">取消</el-button>
        <el-button type="primary" @click="submitTicket">提交工单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { qaApi } from '@/api/qa'
import { ticketApi } from '@/api/ticket'
import { ElMessage } from 'element-plus'

const question = ref('')
const thinking = ref(false)
const messages = ref<Array<Record<string, any>>>([])
const sampleQuestions = [
  '账号被冻结了怎么处理？',
  '网络连接不稳定怎么排查？',
  '服务器硬盘故障告警如何响应？',
  '没有访问某个系统的权限怎么办？',
  '如何更新服务器的hosts文件？',
]
const msgContainer = ref<HTMLElement>()
const showTicketDialog = ref(false)
const showHistory = ref(false)
const historyList = ref<any[]>([])
const ticketForm = reactive({ question: '', supplementary: '', urgency: 'normal' })

function formatAnswer(text: string) {
  return text.replace(/\n/g, '<br>')
}

async function sendQuestion() {
  const q = question.value.trim()
  if (!q || thinking.value) return
  messages.value.push({ role: 'user', content: q })
  question.value = ''
  ticketForm.question = q  // always set: user's question becomes default ticket description
  thinking.value = true
  await nextTick()
  scrollBottom()

  try {
    const res = await qaApi.ask(q)
    const d = res.data
    messages.value.push({
      role: 'assistant',
      content: d.answer || d.message || '',
      hasAnswer: d.has_answer,
      references: d.references || [],
    })
  } catch (_) {
    messages.value.push({ role: 'assistant', content: '请求失败，请重试', hasAnswer: false, references: [] })
  } finally {
    thinking.value = false
    await nextTick()
    scrollBottom()
  }
}

function openManualTicket() {
  // 如果输入框有未发送的文本，自动带入工单
  const pending = question.value.trim()
  if (pending) {
    ticketForm.question = pending
    question.value = ''
  }
  // 否则保留上一次 QA 的问题（已在 sendQuestion 中设置）
  showTicketDialog.value = true
}

function createTicketFromMsg(msg: any) {
  ticketForm.question = messages.value.find(m => m.role === 'user' && m.content)?.content || ''
  showTicketDialog.value = true
}

async function loadHistory() {
  showHistory.value = true
  try {
    const res = await qaApi.history({ page: 1, page_size: 20 })
    historyList.value = res.data.items || []
  } catch (_) {}
}

async function submitTicket() {
  if (!ticketForm.question) { ElMessage.warning('请填写问题描述'); return }
  try {
    await ticketApi.create({
      question: ticketForm.question,
      supplementary: ticketForm.supplementary,
      urgency: ticketForm.urgency,
    })
    ElMessage.success('工单已提交')
    showTicketDialog.value = false
    ticketForm.supplementary = ''
    ticketForm.urgency = 'normal'
  } catch (_) { /* handled */ }
}

function scrollBottom() {
  if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
}
</script>

<style scoped>
.qa-page { height: calc(100vh - 140px); display: flex; justify-content: center; }
.chat-container { width: 100%; max-width: 800px; display: flex; flex-direction: column; background: #fff; border-radius: 4px; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; }
.message { display: flex; gap: 10px; margin-bottom: 16px; }
.message.user { flex-direction: row-reverse; }
.avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
.message.user .avatar { background: #409EFF; color: #fff; }
.message.assistant .avatar { background: #67C23A; color: #fff; }
.bubble { max-width: 70%; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.6; }
.message.user .bubble { background: #409EFF; color: #fff; }
.message.assistant .bubble { background: #f4f4f5; color: #303133; }
.chat-input { padding: 12px 20px; border-top: 1px solid #e6e6e6; }
.input-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.no-answer { margin-top: 8px; }
.welcome { text-align: center; padding: 60px 20px; }
.welcome h3 { font-size: 24px; margin-bottom: 16px; }
.welcome p { color: #909399; margin-bottom: 16px; }
.examples { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
</style>
