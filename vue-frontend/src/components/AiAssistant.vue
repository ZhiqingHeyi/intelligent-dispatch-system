<template>
  <transition name="ai-panel">
    <aside v-if="store.aiPanelOpen" class="ai-panel">
      <div class="ai-panel-header">
        <div class="ai-header-left">
          <span class="ai-icon">🤖</span>
          <span class="ai-title">AI智能调度</span>
          <span class="ai-status-dot" :class="{ active: store.aiApiConfigured, running: schedulerRunning }"></span>
        </div>
        <div class="ai-header-actions">
          <button class="ai-header-btn" @click="showScheduler = !showScheduler" title="定时调度">
            <span>⏱</span>
          </button>
          <button class="ai-header-btn" @click="store.aiConfigModalOpen = true" title="设置">
            <span>⚙</span>
          </button>
          <button class="ai-header-btn close" @click="store.toggleAiPanel()" title="关闭">
            <span>✕</span>
          </button>
        </div>
      </div>

      <div v-if="showScheduler" class="ai-scheduler-bar">
        <div class="scheduler-row">
          <span class="scheduler-label">自动调度</span>
          <button
            class="scheduler-toggle"
            :class="{ active: schedulerRunning }"
            @click="toggleScheduler"
          >
            <span class="toggle-dot"></span>
            {{ schedulerRunning ? '运行中' : '已停止' }}
          </button>
        </div>
        <div class="scheduler-row">
          <span class="scheduler-label">间隔</span>
          <div class="interval-options">
            <button
              v-for="opt in intervalOptions"
              :key="opt.value"
              class="interval-btn"
              :class="{ active: currentInterval === opt.value }"
              @click="setInterval(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
        <div v-if="store.aiSchedulerStatus" class="scheduler-info">
          <span v-if="store.aiSchedulerStatus.last_dispatch_time">
            上次调度: {{ store.aiSchedulerStatus.last_dispatch_time.substring(11, 19) }}
          </span>
          <span v-if="store.aiSchedulerStatus.dispatch_count > 0">
            已调度 {{ store.aiSchedulerStatus.dispatch_count }} 次
          </span>
        </div>
      </div>

      <div class="ai-experience-bar" v-if="store.aiExperienceSummary">
        <div class="exp-stat">
          <span class="exp-value" :style="{ color: 'var(--accent-green)' }">{{ store.aiExperienceSummary.success_rate }}%</span>
          <span class="exp-label">成功率</span>
        </div>
        <div class="exp-stat">
          <span class="exp-value">{{ store.aiExperienceSummary.total }}</span>
          <span class="exp-label">总调度</span>
        </div>
        <div class="exp-stat">
          <span class="exp-value" :style="{ color: 'var(--accent-red)' }">{{ store.aiExperienceSummary.overrides }}</span>
          <span class="exp-label">被修正</span>
        </div>
      </div>

      <div class="ai-chat-area" ref="chatAreaRef">
        <div v-if="store.aiChatMessages.length === 0" class="ai-empty">
          <div class="ai-empty-icon">🤖</div>
          <p class="ai-empty-title">AI智能调度助手</p>
          <p class="ai-empty-desc">我可以帮你分析缆机车辆状态、执行智能匹配调度</p>
          <div class="ai-quick-actions">
            <button class="quick-btn" @click="quickAction('分析当前系统状态')">📊 分析状态</button>
            <button class="quick-btn" @click="triggerDispatch">🔄 智能调度</button>
            <button class="quick-btn" @click="quickAction('查看位置排名')">📍 位置排名</button>
            <button class="quick-btn" @click="quickAction('查看调度经验')">💡 调度经验</button>
          </div>
        </div>

        <div
          v-for="msg in store.aiChatMessages"
          :key="msg.id"
          class="ai-message"
          :class="msg.role"
        >
          <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="msg-content">
            <div class="msg-text" v-html="formatMessage(msg.content)"></div>
            <div v-if="msg.tool_results && msg.tool_results.length > 0" class="msg-tools">
              <div v-for="(tr, idx) in msg.tool_results" :key="idx" class="tool-result">
                <div class="tool-header">
                  <span class="tool-icon">🔧</span>
                  <span class="tool-name">{{ tr.tool_name }}</span>
                </div>
                <div class="tool-body">
                  <template v-if="tr.result?.success">
                    <span class="tool-success">✓ {{ tr.result.message || '执行成功' }}</span>
                  </template>
                  <template v-else-if="tr.result?.error">
                    <span class="tool-error">✗ {{ tr.result.error }}</span>
                  </template>
                  <template v-else-if="tr.result?.message">
                    <span class="tool-error">✗ {{ tr.result.message }}</span>
                  </template>
                  <template v-else>
                    <span class="tool-info">已执行</span>
                  </template>
                </div>
              </div>
            </div>
            <div class="msg-time">{{ msg.created_at?.substring(11, 19) || '' }}</div>
          </div>
        </div>

        <div v-if="store.aiChatLoading" class="ai-message assistant">
          <div class="msg-avatar">🤖</div>
          <div class="msg-content">
            <div class="msg-typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="ai-input-area">
        <div class="ai-input-row">
          <button class="dispatch-btn" @click="triggerDispatch" :disabled="store.aiChatLoading" title="一键智能调度">
            🔄
          </button>
          <input
            v-model="inputText"
            class="ai-input"
            placeholder="输入消息或指令..."
            @keydown.enter="sendMessage"
            :disabled="store.aiChatLoading"
          />
          <button
            class="send-btn"
            @click="sendMessage"
            :disabled="!inputText.trim() || store.aiChatLoading"
          >
            ➤
          </button>
        </div>
        <div class="ai-input-hint">
          <button class="clear-btn" @click="clearHistory">🗑 清空记录</button>
        </div>
      </div>
    </aside>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'

const store = useDispatchStore()
const inputText = ref('')
const showScheduler = ref(false)
const chatAreaRef = ref<HTMLElement | null>(null)

const intervalOptions = [
  { label: '1分钟', value: 60 },
  { label: '3分钟', value: 180 },
  { label: '5分钟', value: 300 },
  { label: '10分钟', value: 600 },
]

const schedulerRunning = computed(() => store.aiSchedulerStatus?.running ?? false)
const currentInterval = computed(() => store.aiSchedulerStatus?.interval ?? store.aiConfig.dispatch_interval ?? 180)

const scrollToBottom = () => {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

watch(() => store.aiChatMessages.length, () => {
  scrollToBottom()
})

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || store.aiChatLoading) return
  inputText.value = ''
  await store.sendAiChat(text)
  scrollToBottom()
}

const quickAction = async (message: string) => {
  if (store.aiChatLoading) return
  await store.sendAiChat(message)
  scrollToBottom()
}

const triggerDispatch = async () => {
  if (store.aiChatLoading) return
  await store.triggerAiDispatch()
  scrollToBottom()
}

const toggleScheduler = async () => {
  if (schedulerRunning.value) {
    await store.stopAiSchedulerAction()
  } else {
    if (!store.aiApiConfigured) {
      store.aiConfigModalOpen = true
      return
    }
    await store.startAiSchedulerAction()
  }
}

const setInterval = async (value: number) => {
  await store.saveAiConfigAction({ dispatch_interval: value, auto_dispatch_enabled: true })
  await store.fetchAiScheduler()
}

const clearHistory = async () => {
  await store.clearAiChatHistoryAction()
}

const formatMessage = (content: string) => {
  if (!content) return ''
  let text = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/`(.*?)`/g, '<code>$1</code>')
  text = text.replace(/\n/g, '<br>')
  return text
}

onMounted(async () => {
  await Promise.all([
    store.fetchAiConfig(),
    store.fetchAiChatHistory(),
    store.fetchAiScheduler(),
    store.fetchAiExperience(),
  ])
  scrollToBottom()
})
</script>

<style scoped>
.ai-panel {
  width: 100%;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  overflow: hidden;
  position: relative;
}

/* AI面板容器响应式 - 在grid中控制宽度 */
@media screen and (min-width: 1920px) {
  .ai-panel {
    border-radius: 16px;
  }
}

@media screen and (max-width: 1400px) {
  .ai-panel {
    border-radius: 12px;
  }
}

@media screen and (max-width: 1200px) {
  .ai-panel {
    border-radius: 10px;
  }
}

@media screen and (max-width: 1024px) {
  .ai-panel {
    border-radius: 8px;
  }
}

.ai-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--ai-panel-gradient);
  pointer-events: none;
}

.ai-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: clamp(8px, 1vh, 12px) clamp(10px, 1vw, 14px);
  border-bottom: 1px solid var(--border-color);
  position: relative;
  z-index: 1;
}

@media screen and (max-width: 1200px) {
  .ai-panel-header {
    padding: 8px 10px;
  }
}

.ai-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 18px;
}

.ai-title {
  font-size: clamp(12px, 1.1vw, 14px);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 1px;
}

@media screen and (max-width: 1200px) {
  .ai-title {
    font-size: 12px;
  }
}

.ai-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.ai-status-dot.active {
  background: var(--accent-green);
  box-shadow: 0 0 8px var(--accent-green);
}

.ai-status-dot.running {
  background: var(--accent-blue);
  box-shadow: 0 0 8px var(--accent-blue);
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.ai-header-actions {
  display: flex;
  gap: 4px;
}

.ai-header-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-subtle);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  transition: all 0.2s;
}

.ai-header-btn:hover {
  background: var(--accent-blue-bg);
  border-color: var(--accent-blue-border-hover);
  color: var(--text-primary);
}

.ai-header-btn.close:hover {
  background: var(--close-btn-hover-bg);
  border-color: var(--accent-red-border);
  color: var(--accent-red);
}

.ai-scheduler-bar {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
  background: var(--ai-scheduler-bg);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.scheduler-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.scheduler-row:last-child {
  margin-bottom: 0;
}

.scheduler-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.scheduler-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-subtle);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.scheduler-toggle.active {
  background: var(--accent-blue-bg);
  border-color: var(--accent-blue-border-hover);
  color: var(--accent-blue);
}

.toggle-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.interval-options {
  display: flex;
  gap: 4px;
}

.interval-btn {
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-subtle);
  color: var(--text-muted);
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.interval-btn.active {
  background: var(--accent-blue-bg-hover);
  border-color: var(--accent-blue-border-hover);
  color: var(--accent-blue);
}

.scheduler-info {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 6px;
}

.ai-experience-bar {
  display: flex;
  justify-content: space-around;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.exp-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.exp-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.exp-label {
  font-size: 10px;
  color: var(--text-muted);
}

.ai-chat-area {
  flex: 1;
  overflow-y: auto;
  padding: clamp(8px, 1vw, 12px);
  position: relative;
  z-index: 1;
  min-height: 120px;
  max-height: calc(100% - 160px);
}

@media screen and (max-width: 1200px) {
  .ai-chat-area {
    padding: 8px;
    min-height: 100px;
    max-height: calc(100% - 140px);
  }
}

@media screen and (max-width: 1024px) {
  .ai-chat-area {
    min-height: 80px;
    max-height: calc(100% - 130px);
  }
}

.ai-chat-area::-webkit-scrollbar {
  width: 4px;
}

.ai-chat-area::-webkit-scrollbar-track {
  background: var(--scrollbar-track);
}

.ai-chat-area::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 2px;
}

.ai-empty {
  text-align: center;
  padding: 30px 16px;
}

.ai-empty-icon {
  font-size: 40px;
  margin-bottom: 12px;
  opacity: 0.6;
}

.ai-empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.ai-empty-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.ai-quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.quick-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: var(--accent-blue-bg);
  border-color: var(--accent-blue-border-hover);
  color: var(--text-primary);
}

.ai-message {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-message.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  background: var(--ai-msg-avatar-bg);
}

.ai-message.assistant .msg-avatar {
  background: var(--ai-msg-avatar-gradient);
  border: 1px solid var(--ai-msg-avatar-border);
}

.msg-content {
  max-width: 85%;
  min-width: 0;
}

.msg-text {
  font-size: clamp(11px, 1vw, 13px);
  line-height: 1.6;
  color: var(--text-primary);
  word-break: break-word;
}

@media screen and (max-width: 1200px) {
  .msg-text {
    font-size: 11px;
  }
}

.msg-text :deep(code) {
  background: var(--ai-code-bg);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
  color: var(--accent-blue);
}

.msg-text :deep(strong) {
  color: var(--accent-green);
}

.ai-message.user .msg-text {
  background: var(--ai-msg-user-bg);
  border: 1px solid var(--ai-msg-user-border);
  border-radius: 10px 10px 2px 10px;
  padding: 8px 12px;
}

.ai-message.assistant .msg-text {
  background: var(--ai-msg-assistant-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px 10px 10px 2px;
  padding: 8px 12px;
}

.msg-tools {
  margin-top: 6px;
}

.tool-result {
  background: var(--bg-inset);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 10px;
  margin-bottom: 4px;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.tool-icon {
  font-size: 11px;
}

.tool-name {
  font-size: 11px;
  color: var(--accent-blue);
  font-weight: 500;
}

.tool-body {
  font-size: 11px;
}

.tool-success {
  color: var(--accent-green);
}

.tool-error {
  color: var(--accent-red);
}

.tool-info {
  color: var(--text-muted);
}

.msg-time {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
  text-align: right;
}

.msg-typing {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  background: var(--ai-msg-assistant-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px 10px 10px 2px;
}

.msg-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-blue);
  animation: typing-bounce 1.2s ease-in-out infinite;
}

.msg-typing span:nth-child(2) { animation-delay: 0.2s; }
.msg-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

.ai-input-area {
  padding: clamp(8px, 1vh, 10px) clamp(10px, 1vw, 12px);
  border-top: 1px solid var(--border-color);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  background: var(--bg-card);
}

@media screen and (max-width: 1200px) {
  .ai-input-area {
    padding: 8px 10px;
  }
}

.ai-input-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.dispatch-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--accent-blue-border-hover);
  background: var(--accent-blue-bg);
  color: var(--accent-blue);
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dispatch-btn:hover:not(:disabled) {
  background: var(--accent-blue-bg-hover);
  box-shadow: 0 0 12px var(--accent-blue-bg);
}

.dispatch-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ai-input {
  flex: 1;
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.ai-input:focus {
  border-color: var(--accent-blue-border-hover);
  box-shadow: 0 0 8px var(--accent-blue-glow);
}

.ai-input::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: none;
  background: var(--btn-gradient);
  color: var(--btn-gradient-text);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0 12px var(--accent-blue-bg);
}

.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  transform: none;
}

.ai-input-hint {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.clear-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 10px;
  cursor: pointer;
  padding: 2px 6px;
  transition: color 0.2s;
}

.clear-btn:hover {
  color: var(--accent-red);
}

.ai-panel-enter-active,
.ai-panel-leave-active {
  transition: all 0.3s ease;
}

.ai-panel-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.ai-panel-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
