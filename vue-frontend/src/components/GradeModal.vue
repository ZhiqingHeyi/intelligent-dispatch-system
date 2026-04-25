<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <div class="modal">
          <div class="modal-header">
            <h3>设置级配 - {{ targetName }}</h3>
            <button class="modal-close" @click="close">&times;</button>
          </div>
          <div class="modal-body">
            <div
              v-for="grade in grades"
              :key="grade.id"
              class="grade-option"
              :class="{ selected: currentGradeId === grade.id }"
              :style="{ '--gc': grade.color }"
              @click="selectGrade(grade.id)"
            >
              <div class="grade-option-dot" :style="{ background: grade.color }"></div>
              <span class="grade-option-name">{{ grade.name }}</span>
              <span v-if="currentGradeId === grade.id" class="grade-option-check">✓</span>
            </div>
            <div class="grade-option-clear" @click="selectGrade(0)">
              <span>✕</span>
              <span>清除级配</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { useDispatchStore } from '@/stores/dispatch'

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
const grades = store.grades

const close = () => {
  emit('update:modelValue', false)
}

const selectGrade = async (gradeId: number) => {
  if (!props.targetId) return
  
  if (props.type === 'cable_car') {
    await store.setCableCarGrade(props.targetId, gradeId)
  } else {
    await store.setVehicleGrade(props.targetId, gradeId)
  }
  
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

.grade-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.grade-option:hover {
  background: var(--bg-card-hover);
  border-color: var(--gc, rgba(0, 212, 255, 0.3));
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.06);
}

.grade-option.selected {
  border-color: var(--gc, var(--accent-blue));
  background: rgba(0, 212, 255, 0.05);
  box-shadow: 0 0 16px rgba(0, 212, 255, 0.08);
}

.grade-option-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.grade-option-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.grade-option-check {
  color: var(--accent-green);
  font-weight: 700;
  font-size: 16px;
}

.grade-option-clear {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 71, 87, 0.05);
  border: 1px solid rgba(255, 71, 87, 0.15);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-muted);
}

.grade-option-clear:hover {
  background: rgba(255, 71, 87, 0.1);
  border-color: rgba(255, 71, 87, 0.3);
  color: var(--accent-red);
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
