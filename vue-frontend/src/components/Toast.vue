<template>
  <Transition name="toast">
    <div v-if="visible" class="toast" :class="type">
      <span class="toast-icon">{{ iconMap[type ?? 'info'] }}</span>
      <span class="toast-message">{{ message }}</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  message: string
  type?: 'success' | 'error' | 'info' | 'warning'
  duration?: number
}>()

const visible = ref(false)
let timer: number | null = null

const iconMap: Record<string, string> = {
  success: '✓',
  error: '✗',
  info: 'ℹ',
  warning: '⚠',
}

watch(() => props.message, (val) => {
  if (val) {
    visible.value = true
    if (timer) clearTimeout(timer)
    timer = window.setTimeout(() => {
      visible.value = false
    }, props.duration || 3000)
  }
})
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  box-shadow: var(--modal-shadow);
  z-index: 10000;
  backdrop-filter: blur(12px);
}

.toast.success {
  border-color: var(--accent-green-border);
  color: var(--accent-green);
}

.toast.error {
  border-color: var(--accent-red-border);
  color: var(--accent-red);
}

.toast.info {
  border-color: var(--accent-blue-border);
  color: var(--accent-blue);
}

.toast.warning {
  border-color: var(--accent-yellow-border);
  color: var(--accent-yellow);
}

.toast-icon {
  font-size: 16px;
  font-weight: 700;
}

.toast-message {
  font-size: 14px;
  color: var(--text-primary);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
