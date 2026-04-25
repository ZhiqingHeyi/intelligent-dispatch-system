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
import { ref } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import CableCarCard from './CableCarCard.vue'
import type { CableCar } from '@/types'

const store = useDispatchStore()
const gradeModalCar = ref<CableCar | null>(null)
const stateModalCar = ref<CableCar | null>(null)

const openGradeModal = (car: CableCar) => {
  gradeModalCar.value = car
}

const openStateModal = (car: CableCar) => {
  stateModalCar.value = car
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
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: var(--accent-blue);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 自定义滚动条 */
.panel-body::-webkit-scrollbar {
  width: 4px;
}

.panel-body::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.panel-body::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.2);
  border-radius: 2px;
}

.panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.4);
}
</style>
