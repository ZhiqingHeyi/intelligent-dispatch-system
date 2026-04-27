<template>
  <aside class="panel-left">
    <div class="panel-header">
      <span class="panel-title">◆ 缆机状态</span>
      <span class="panel-badge">{{ store.cableCars.length }}台</span>
    </div>
    
    <div class="panel-body">
      <CableCarCard
        v-for="car in store.cableCars"
        :key="car.id"
        :car="car"
        :is-selected="store.selectedCableCar === car.id"
        @select="store.selectCableCar(car.id)"
        @set-grade="openGradeModal(car)"
        @set-state="openStateModal(car)"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useDispatchStore } from '@/stores/dispatch'
import CableCarCard from './CableCarCard.vue'
import type { CableCar } from '@/types'

const store = useDispatchStore()

const emit = defineEmits<{
  'open-grade-modal': [data: { id: number; name: string; gradeId: number; type: 'cable_car' | 'vehicle' }]
  'open-state-modal': [data: { id: number; name: string; currentState: string }]
}>()

const openGradeModal = (car: CableCar) => {
  emit('open-grade-modal', {
    id: car.id,
    name: car.name,
    gradeId: car.grade_id || 0,
    type: 'cable_car'
  })
}

const openStateModal = (car: CableCar) => {
  emit('open-state-modal', {
    id: car.id,
    name: car.name,
    currentState: car.manual_state || 'normal'
  })
}
</script>

<style scoped>
.panel-left {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 6px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 2px;
}

.panel-badge {
  font-size: 12px;
  padding: 4px 12px;
  background: var(--accent-blue-bg);
  border: 1px solid var(--accent-blue-border);
  border-radius: 12px;
  color: var(--accent-blue);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: clamp(4px, 0.5vw, 6px);
  display: flex;
  flex-direction: column;
  gap: clamp(8px, 1vh, 10px);
}

@media screen and (max-width: 1200px) {
  .panel-body {
    gap: 8px;
    padding-right: 4px;
  }
}

.panel-body::-webkit-scrollbar {
  width: 4px;
}

.panel-body::-webkit-scrollbar-track {
  background: var(--scrollbar-track);
  border-radius: 2px;
}

.panel-body::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 2px;
}

.panel-body::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}
</style>
