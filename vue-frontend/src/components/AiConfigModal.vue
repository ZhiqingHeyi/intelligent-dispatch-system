<template>
  <div v-if="store.aiConfigModalOpen" class="modal-overlay" @click.self="close">
    <div class="modal-content ai-config-modal">
      <div class="modal-header">
        <h3>⚙ AI模型配置</h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <div v-if="saveStatus.message" class="status-banner" :class="saveStatus.type">
          <span class="status-icon">{{ saveStatus.type === 'success' ? '✓' : saveStatus.type === 'error' ? '✗' : '⟳' }}</span>
          <span class="status-text">{{ saveStatus.message }}</span>
        </div>

        <div class="config-section">
          <h4 class="section-title">API 配置</h4>

          <div class="form-group">
            <label>API 地址 <span class="required">*</span></label>
            <input v-model="form.api_url" class="form-input" :class="{ error: errors.api_url }" placeholder="https://api.openai.com/v1/chat/completions" />
            <span v-if="errors.api_url" class="form-error">{{ errors.api_url }}</span>
            <span v-else class="form-hint">支持OpenAI兼容接口（如DeepSeek、通义千问等）</span>
          </div>

          <div class="form-group">
            <label>API Key <span class="required">*</span></label>
            <div class="key-input-wrapper">
              <input
                v-model="form.api_key"
                class="form-input"
                :class="{ error: errors.api_key }"
                :type="showApiKey ? 'text' : 'password'"
                :placeholder="apiKeyPlaceholder"
                @focus="onApiKeyFocus"
              />
              <button class="key-toggle" @click="showApiKey = !showApiKey">
                {{ showApiKey ? '🙈' : '👁' }}
              </button>
            </div>
            <span v-if="errors.api_key" class="form-error">{{ errors.api_key }}</span>
            <span v-else-if="store.aiConfig.api_key_configured" class="form-hint success">✓ 已配置密钥（留空保持不变）</span>
            <span v-else class="form-hint">API密钥，安全存储在本地数据库中</span>
          </div>

          <div class="form-group">
            <label>模型名称 <span class="required">*</span></label>
            <input v-model="form.model" class="form-input" :class="{ error: errors.model }" placeholder="gpt-4o / deepseek-chat / qwen-plus" />
            <span v-if="errors.model" class="form-error">{{ errors.model }}</span>
            <span v-else class="form-hint">输入模型标识符，需与API服务商匹配</span>
          </div>
        </div>

        <div class="config-section">
          <h4 class="section-title">模型参数</h4>

          <div class="form-row">
            <div class="form-group half">
              <label>Temperature</label>
              <input v-model.number="form.temperature" class="form-input" type="number" min="0" max="2" step="0.1" />
              <span class="form-hint">0=精确, 1=创造</span>
            </div>
            <div class="form-group half">
              <label>Max Tokens</label>
              <input v-model.number="form.max_tokens" class="form-input" type="number" min="64" max="32768" step="256" />
              <span class="form-hint">最大输出长度</span>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h4 class="section-title">自动调度</h4>

          <div class="form-group">
            <label class="toggle-label">
              <span>启用AI自动调度</span>
              <button
                class="toggle-switch"
                :class="{ active: form.auto_dispatch_enabled }"
                @click="form.auto_dispatch_enabled = !form.auto_dispatch_enabled"
              >
                <span class="switch-dot"></span>
              </button>
            </label>
            <span class="form-hint">AI将按设定间隔自动分析并执行调度</span>
          </div>

          <div v-if="form.auto_dispatch_enabled" class="form-group">
            <label>调度间隔</label>
            <div class="interval-select">
              <button
                v-for="opt in intervalOptions"
                :key="opt.value"
                class="interval-option"
                :class="{ active: form.dispatch_interval === opt.value }"
                @click="form.dispatch_interval = opt.value"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h4 class="section-title">常用API配置参考</h4>
          <div class="preset-list">
            <button class="preset-btn" @click="applyPreset('volcengine')">
              <span class="preset-name">火山引擎Ark</span>
              <span class="preset-model">GLM-4</span>
            </button>
            <button class="preset-btn" @click="applyPreset('openai')">
              <span class="preset-name">OpenAI</span>
              <span class="preset-model">GPT-4o</span>
            </button>
            <button class="preset-btn" @click="applyPreset('deepseek')">
              <span class="preset-name">DeepSeek</span>
              <span class="preset-model">deepseek-chat</span>
            </button>
            <button class="preset-btn" @click="applyPreset('qwen')">
              <span class="preset-name">通义千问</span>
              <span class="preset-model">qwen-plus</span>
            </button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-test" @click="testConnection" :disabled="testing || !canTest">
          <span v-if="testing" class="btn-spinner"></span>
          {{ testing ? '测试中...' : '🔗 测试连接' }}
        </button>
        <button class="btn-primary" @click="save" :disabled="saving">
          <span v-if="saving" class="btn-spinner"></span>
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import * as api from '@/api/dispatch'

const store = useDispatchStore()

const form = reactive({
  api_url: '',
  api_key: '',
  model: '',
  temperature: 0.3,
  max_tokens: 2048,
  auto_dispatch_enabled: false,
  dispatch_interval: 180,
})

const errors = reactive<Record<string, string>>({
  api_url: '',
  api_key: '',
  model: '',
})

const saving = ref(false)
const testing = ref(false)
const showApiKey = ref(false)
const apiKeyEdited = ref(false)

const saveStatus = reactive({
  type: '' as 'success' | 'error' | 'loading' | '',
  message: '',
})

const intervalOptions = [
  { label: '1分钟', value: 60 },
  { label: '3分钟', value: 180 },
  { label: '5分钟', value: 300 },
  { label: '10分钟', value: 600 },
  { label: '30分钟', value: 1800 },
]

const presets: Record<string, any> = {
  volcengine: {
    api_url: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    model: 'glm-4-7-251222',
  },
  openai: {
    api_url: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4o',
  },
  deepseek: {
    api_url: 'https://api.deepseek.com/v1/chat/completions',
    model: 'deepseek-chat',
  },
  qwen: {
    api_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    model: 'qwen-plus',
  },
  zhipu: {
    api_url: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    model: 'glm-4',
  },
}

const apiKeyPlaceholder = computed(() => {
  if (store.aiConfig.api_key_configured) {
    return '已配置密钥，留空保持不变，输入新值则替换'
  }
  return '请输入API Key'
})

const canTest = computed(() => {
  const hasUrl = form.api_url.trim().length > 0
  const hasModel = form.model.trim().length > 0
  const hasKey = form.api_key.trim().length > 0 || store.aiConfig.api_key_configured
  return hasUrl && hasModel && hasKey
})

watch(() => store.aiConfigModalOpen, (open) => {
  if (open) {
    saveStatus.type = ''
    saveStatus.message = ''
    Object.keys(errors).forEach(k => errors[k] = '')
    apiKeyEdited.value = false
    showApiKey.value = false

    Object.assign(form, {
      api_url: store.aiConfig.api_url || '',
      api_key: '',
      model: store.aiConfig.model || '',
      temperature: store.aiConfig.temperature ?? 0.3,
      max_tokens: store.aiConfig.max_tokens ?? 2048,
      auto_dispatch_enabled: store.aiConfig.auto_dispatch_enabled ?? false,
      dispatch_interval: store.aiConfig.dispatch_interval ?? 180,
    })
  }
})

const onApiKeyFocus = () => {
  if (!apiKeyEdited.value && store.aiConfig.api_key_configured) {
    form.api_key = ''
  }
}

const validateForm = (): boolean => {
  Object.keys(errors).forEach(k => errors[k] = '')
  let valid = true

  if (!form.api_url.trim()) {
    errors.api_url = 'API地址不能为空'
    valid = false
  } else if (!form.api_url.trim().startsWith('http')) {
    errors.api_url = 'API地址必须以http://或https://开头'
    valid = false
  }

  if (!form.api_key.trim() && !store.aiConfig.api_key_configured) {
    errors.api_key = '首次配置必须输入API Key'
    valid = false
  } else if (form.api_key.trim() && form.api_key.trim().length < 8 && !store.aiConfig.api_key_configured) {
    errors.api_key = 'API Key长度不足，请检查是否输入完整'
    valid = false
  }

  if (!form.model.trim()) {
    errors.model = '模型名称不能为空'
    valid = false
  }

  return valid
}

const applyPreset = (key: string) => {
  const preset = presets[key]
  if (preset) {
    form.api_url = preset.api_url
    form.model = preset.model
    errors.api_url = ''
    errors.model = ''
  }
}

const save = async () => {
  if (!validateForm()) return

  saving.value = true
  saveStatus.type = 'loading'
  saveStatus.message = '正在保存配置...'

  try {
    const payload: Record<string, any> = {
      api_url: form.api_url.trim(),
      model: form.model.trim(),
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      auto_dispatch_enabled: form.auto_dispatch_enabled,
      dispatch_interval: form.dispatch_interval,
    }

    if (form.api_key.trim()) {
      payload.api_key = form.api_key.trim()
    }

    const { data } = await api.saveAiConfig(payload)

    if (data.success) {
      saveStatus.type = 'success'
      saveStatus.message = data.verified ? '✓ 配置保存成功并已验证' : '配置已保存，但建议检查配置是否完整'
      await store.fetchAiConfig()
      form.api_key = ''
      apiKeyEdited.value = false
    } else {
      saveStatus.type = 'error'
      saveStatus.message = data.message || '保存失败，请重试'
      if (data.errors && data.errors.length > 0) {
        data.errors.forEach((err: string) => {
          if (err.includes('API地址')) errors.api_url = err
          else if (err.includes('API Key')) errors.api_key = err
          else if (err.includes('模型')) errors.model = err
        })
      }
    }
  } catch (e: any) {
    saveStatus.type = 'error'
    const msg = e?.response?.data?.message || e?.message || '网络请求失败'
    saveStatus.message = `保存失败: ${msg}`
  } finally {
    saving.value = false
  }
}

const testConnection = async () => {
  testing.value = true
  saveStatus.type = 'loading'
  saveStatus.message = '正在测试连接...'

  try {
    const payload: Record<string, any> = {
      api_url: form.api_url.trim(),
      model: form.model.trim(),
    }
    if (form.api_key.trim()) {
      payload.api_key = form.api_key.trim()
    }

    const { data } = await api.testAiConnection(payload)

    saveStatus.type = data.success ? 'success' : 'error'
    saveStatus.message = data.message || (data.success ? '连接成功' : '连接失败')
  } catch (e: any) {
    saveStatus.type = 'error'
    const msg = e?.response?.data?.message || e?.message || '网络请求失败'
    saveStatus.message = `测试失败: ${msg}`
  } finally {
    testing.value = false
  }
}

const close = () => {
  if (saving.value || testing.value) return
  store.aiConfigModalOpen = false
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.ai-config-modal {
  width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(8, 16, 40, 0.98) 0%, rgba(4, 8, 20, 0.98) 100%);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 107, 107, 0.1);
  color: var(--accent-red);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.modal-body::-webkit-scrollbar {
  width: 4px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.2);
  border-radius: 2px;
}

.status-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.status-banner.success {
  background: rgba(0, 255, 136, 0.08);
  border: 1px solid rgba(0, 255, 136, 0.2);
  color: var(--accent-green);
}

.status-banner.error {
  background: rgba(255, 107, 107, 0.08);
  border: 1px solid rgba(255, 107, 107, 0.2);
  color: var(--accent-red);
}

.status-banner.loading {
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: var(--accent-blue);
}

.status-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.status-text {
  flex: 1;
  line-height: 1.4;
}

.config-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 12px;
  color: var(--accent-blue);
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.required {
  color: var(--accent-red);
}

.form-input {
  width: 100%;
  height: 34px;
  padding: 0 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus {
  border-color: rgba(0, 212, 255, 0.4);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.1);
}

.form-input.error {
  border-color: rgba(255, 107, 107, 0.5);
  box-shadow: 0 0 8px rgba(255, 107, 107, 0.1);
}

.form-error {
  display: block;
  font-size: 11px;
  color: var(--accent-red);
  margin-top: 3px;
}

.form-hint {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 3px;
}

.form-hint.success {
  color: var(--accent-green);
}

.key-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.key-input-wrapper .form-input {
  padding-right: 40px;
}

.key-toggle {
  position: absolute;
  right: 4px;
  width: 30px;
  height: 26px;
  border-radius: 4px;
  border: none;
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.key-toggle:hover {
  background: rgba(0, 212, 255, 0.1);
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-group.half {
  flex: 1;
}

.toggle-label {
  display: flex !important;
  align-items: center;
  justify-content: space-between;
}

.toggle-switch {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  border: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.toggle-switch.active {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.4);
}

.switch-dot {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all 0.2s;
}

.toggle-switch.active .switch-dot {
  left: 20px;
  background: var(--accent-blue);
}

.interval-select {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.interval-option {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.interval-option.active {
  background: rgba(0, 212, 255, 0.15);
  border-color: rgba(0, 212, 255, 0.3);
  color: var(--accent-blue);
}

.preset-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.preset-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
}

.preset-name {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
}

.preset-model {
  font-size: 10px;
  color: var(--text-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-secondary,
.btn-primary,
.btn-test {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.btn-test {
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: var(--accent-blue);
}

.btn-test:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.15);
  border-color: rgba(0, 212, 255, 0.4);
}

.btn-test:disabled,
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
  border: none;
  color: #000;
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 0 16px rgba(0, 212, 255, 0.3);
}

.btn-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
