<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content state-modal">
      <div class="modal-header">
        <h3>设置状态 - {{ targetName }}</h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <div class="state-grid">
          <button
            v-for="state in states"
            :key="state.value"
            class="state-option"
            :class="{ selected: selectedState === state.value }"
            :style="{
              background: selectedState === state.value ? state.color + '20' : 'var(--bg-subtle)',
              borderColor: selectedState === state.value ? state.color : 'var(--border-color)',
              color: selectedState === state.value ? state.color : 'var(--text-secondary)'
            }"
            @click="selectedState = state.value"
          >
            <span class="state-icon">{{ state.icon }}</span>
            <span class="state-name">{{ state.label }}</span>
          </button>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" @click="confirm">确认</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import * as api from '@/api/dispatch'

const props = defineProps<{
  modelValue: boolean
  targetId: number | null
  targetName: string
  currentState: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useDispatchStore()
const selectedState = ref('normal')

const show = computed(() => props.modelValue)

const states = [
  { value: 'normal', label: '正常运行', icon: '✅', color: '#00ff88' },
  { value: 'rest', label: '休息中', icon: '💤', color: '#c084fc' },
  { value: 'other', label: '打杂中', icon: '🔧', color: '#888888' },
]

watch(() => props.modelValue, (val) => {
  if (val) {
    selectedState.value = props.currentState
  }
})

const confirm = async () => {
  if (!props.targetId) return
  try {
    await api.setCableCarState(props.targetId, selectedState.value)
    await store.fetchData()
    close()
  } catch (e) {
    alert('操作失败')
  }
}

const close = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.state-modal {
  width: 360px;
  background: var(--modal-bg);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--modal-shadow);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
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
  font-size: 12px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--close-btn-hover-bg);
  color: var(--accent-red);
}

.modal-body {
  padding: 20px;
}

.state-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.state-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-subtle);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.state-option:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--shadow-color);
}

.state-option.selected {
  font-weight: 600;
}

.state-icon {
  font-size: 18px;
}

.state-name {
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-secondary,
.btn-primary {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--bg-subtle);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background: var(--bg-subtle-hover);
  color: var(--text-primary);
}

.btn-primary {
  background: var(--btn-gradient);
  border: none;
  color: var(--btn-gradient-text);
}

.btn-primary:hover {
  transform: scale(1.02);
  box-shadow: 0 0 16px var(--accent-blue-bg);
}
</style>
