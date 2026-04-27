<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content grade-modal">
      <div class="modal-header">
        <h3>设置级配 - {{ targetName }}</h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <div class="grade-grid">
          <button
            v-for="grade in store.grades"
            :key="grade.id"
            class="grade-option"
            :class="{ selected: selectedGradeId === grade.id }"
            :style="{
              '--grade-color': grade.color,
              background: selectedGradeId === grade.id ? grade.color + '20' : 'var(--bg-subtle)',
              borderColor: selectedGradeId === grade.id ? grade.color : 'var(--border-color)',
              color: selectedGradeId === grade.id ? grade.color : 'var(--text-secondary)'
            }"
            @click="selectedGradeId = grade.id"
          >
            <span class="grade-dot" :style="{ background: grade.color }"></span>
            <span class="grade-name">{{ grade.name }}</span>
          </button>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="clearGrade">清除级配</button>
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" @click="confirm">确认</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import * as api from '@/api/dispatch'

const props = defineProps<{
  modelValue: boolean
  targetId: number | null
  targetName: string
  currentGradeId: number
  type: 'cable_car' | 'vehicle'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useDispatchStore()
const selectedGradeId = ref(0)

const show = computed(() => props.modelValue)

import { computed } from 'vue'

watch(() => props.modelValue, (val) => {
  if (val) {
    selectedGradeId.value = props.currentGradeId
  }
})

const confirm = async () => {
  if (!props.targetId) return
  try {
    if (props.type === 'cable_car') {
      await api.setCableCarGrade(props.targetId, selectedGradeId.value)
    } else {
      await api.setVehicleGrade(props.targetId, selectedGradeId.value)
    }
    await store.fetchData()
    close()
  } catch (e) {
    alert('操作失败')
  }
}

const clearGrade = async () => {
  if (!props.targetId) return
  try {
    if (props.type === 'cable_car') {
      await api.setCableCarGrade(props.targetId, 0)
    } else {
      await api.setVehicleGrade(props.targetId, 0)
    }
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

.grade-modal {
  width: 400px;
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

.grade-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.grade-option {
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

.grade-option:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--shadow-color);
}

.grade-option.selected {
  font-weight: 600;
}

.grade-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.grade-name {
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
