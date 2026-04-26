<template>
  <aside class="panel-right">
    <div class="panel-header">
      <span class="panel-title">◆ 运输车辆</span>
      <span class="panel-badge">{{ store.vehicles.length }}台</span>
    </div>
    
    <!-- 级配筛选 -->
    <div class="grade-filter">
      <button 
        v-for="filter in filters" 
        :key="filter.value"
        class="filter-btn"
        :class="{ active: currentFilter === filter.value }"
        @click="currentFilter = filter.value"
      >
        <span v-if="filter.color" class="filter-dot" :style="{ background: filter.color }"></span>
        {{ filter.label }}
      </button>
    </div>
    
    <div class="panel-body">
      <div v-for="(group, gradeName) in groupedVehicles" :key="gradeName" class="vehicle-group">
        <div class="group-header">
          <span class="group-dot" :style="{ background: group.color }"></span>
          <span class="group-name">{{ gradeName }}</span>
          <span class="group-count">{{ group.vehicles.length }}</span>
        </div>
        <div class="vehicle-grid">
          <VehicleCard
            v-for="vehicle in group.vehicles"
            :key="vehicle.id"
            :vehicle="vehicle"
            :is-selected="store.selectedVehicle === vehicle.id"
            @select="store.selectVehicle(vehicle.id)"
            @set-grade="openGradeModal(vehicle)"
          />
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import VehicleCard from './VehicleCard.vue'
import type { Vehicle } from '@/types'

const store = useDispatchStore()
const currentFilter = ref('all')

const filters = computed(() => [
  { label: '全部', value: 'all' },
  ...store.grades.map(g => ({ 
    label: g.name, 
    value: g.name,
    color: g.color 
  })),
  { label: '未分配', value: 'unassigned' }
])

const filteredVehicles = computed(() => {
  if (currentFilter.value === 'all') return store.vehicles
  if (currentFilter.value === 'unassigned') {
    return store.vehicles.filter(v => !v.grade_id)
  }
  const grade = store.grades.find(g => g.name === currentFilter.value)
  if (!grade) return store.vehicles
  return store.vehicles.filter(v => v.grade_id === grade.id)
})

const groupedVehicles = computed(() => {
  const groups: Record<string, { vehicles: Vehicle[], color: string }> = {}
  
  filteredVehicles.value.forEach(v => {
    const grade = store.grades.find(g => g.id === v.grade_id)
    const key = grade?.name || '未分配级配'
    const color = grade?.color || '#888'
    
    if (!groups[key]) {
      groups[key] = { vehicles: [], color }
    }
    groups[key].vehicles.push(v)
  })
  
  return groups
})

const emit = defineEmits<{
  'open-grade-modal': [data: { id: number; name: string; gradeId: number; type: 'cable_car' | 'vehicle' }]
}>()

const openGradeModal = (vehicle: Vehicle) => {
  emit('open-grade-modal', {
    id: vehicle.id,
    name: vehicle.name,
    gradeId: vehicle.grade_id || 0,
    type: 'vehicle'
  })
}
</script>

<style scoped>
.panel-right {
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

.grade-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 6px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 4px;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-btn:hover,
.filter-btn.active {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
  color: var(--text-primary);
}

.filter-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

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

.vehicle-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 6px;
}

.group-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.group-name {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.group-count {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  color: var(--text-muted);
  margin-left: auto;
}

.vehicle-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
</style>
