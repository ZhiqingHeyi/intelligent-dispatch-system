<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <div class="modal">
          <div class="modal-header">
            <h3>设置状态 - {{ targetName }}</h3>
            <button class="modal-close" @click="close">&times;</button>
          </div>
          <div class="modal-body">
            <div
              v-for="option in stateOptions"
              :key="option.id"
              class="state-option"
              :class="{ selected: currentState === option.id }"
              :style="{ '--sc': option.color }"
              @click="selectState(option.id)"
            >
              <div 
                class="state-option-dot" 
                :style="{ background: option.color, boxShadow: `0 0 8px ${option.color}` }"
              ></div>
              <div class="state-option-info">
                <span class="state-option-name">{{ option.name }}</span>
                <span class="state-option-desc">{{ option.desc }}</span>
              </div>
              <span v-if="currentState === option.id" class="state-option-check">✓</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { ManualState } from '@/types'

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

const stateOptions = [
  { id: 'normal' as ManualState, name: '正常运行', color: '#00ff88', desc: '恢复自动状态检测' },
  { id: 'rest' as ManualState, name: '休息中', color: '#c084fc', desc: '缆机暂停工作，休息中' },
  { id: 'other' as ManualState, name: '打杂中', color: '#888888', desc: '缆机执行其他任务' }
]

const close = () => {
  emit('update:modelValue', false)
}

const selectState = async (stateId: ManualState) => {
  if (!props.targetId) return
  
  await store.setCableCarState(props.targetId, stateId)
  close()
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  width: 360px;
  max-width: 90vw;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 71, 87, 0.1);
  color: var(--accent-red);
}

.modal-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.state-option {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.state-option:hover {
  background: var(--bg-card-hover);
  border-color: var(--sc, rgba(0, 212, 255, 0.3));
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.06);
}

.state-option.selected {
  border-color: var(--sc, var(--accent-blue));
  background: rgba(0, 212, 255, 0.05);
  box-shadow: 0 0 16px rgba(0, 212, 255, 0.08);
}

.state-option-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.state-option-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.state-option-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.state-option-desc {
  font-size: 11px;
  color: var(--text-muted);
}

.state-option-check {
  color: var(--accent-green);
  font-weight: 700;
  font-size: 16px;
}

/* 过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.modal-enter-to,
.modal-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>
