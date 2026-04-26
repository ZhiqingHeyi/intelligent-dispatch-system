<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="modelValue" class="toast" :class="type">
        {{ message }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean
  message: string
  type?: 'success' | 'error' | 'info'
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 10000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.toast.success {
  background: rgba(0, 255, 136, 0.9);
  color: #000;
}

.toast.error {
  background: rgba(255, 107, 107, 0.9);
  color: #fff;
}

.toast.info {
  background: rgba(0, 212, 255, 0.9);
  color: #000;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
