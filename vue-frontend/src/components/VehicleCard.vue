<template>
  <div 
    class="vehicle-card"
    :class="{ 
      selected: isSelected,
      going: vehicle.direction === 'going'
    }"
    @click="$emit('select')"
  >
    <div class="card-glow-border"></div>
    
    <div class="vc-top">
      <span class="vc-name">{{ vehicle.name }}</span>
      <span 
        v-if="grade"
        class="vc-grade"
        :style="{
          background: `${grade.color}18`,
          color: grade.color,
          border: `1px solid ${grade.color}44`
        }"
      >
        {{ grade.name }}
      </span>
      <span v-else class="vc-grade no-grade" @click.stop="$emit('set-grade')">
        未分配
      </span>
    </div>
    
    <div class="vc-info">
      <div class="vc-info-item">
        <span class="label">位置</span>
        <span class="value">{{ vehicle.result_x?.toFixed(1) || '-' }}, {{ vehicle.result_y?.toFixed(1) || '-' }}</span>
      </div>
      <div class="vc-info-item">
        <span class="label">速度</span>
        <span class="value" :class="{ active: vehicle.speed > 0 }">
          {{ vehicle.speed?.toFixed(1) || '0.0' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { Vehicle } from '@/types'

const props = defineProps<{
  vehicle: Vehicle
  isSelected: boolean
}>()

defineEmits<{
  select: []
  'set-grade': []
}>()

const store = useDispatchStore()

const grade = computed(() => store.grades.find(g => g.id === props.vehicle.grade_id))
</script>

<style scoped>
.vehicle-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.25s ease;
  cursor: pointer;
}

.vehicle-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.vehicle-card.selected {
  border-color: var(--accent-blue);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.15);
}

.vehicle-card.going {
  border-color: rgba(0, 212, 255, 0.35);
  animation: going-pulse 2s ease-in-out infinite;
}

@keyframes going-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0, 212, 255, 0.2); }
  50% { box-shadow: 0 0 12px 2px rgba(0, 212, 255, 0.15); }
}

.card-glow-border {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), transparent, rgba(0, 255, 136, 0.1));
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.vehicle-card:hover .card-glow-border {
  opacity: 1;
}

.vc-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 8px;
}

.vc-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.vc-grade {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
}

.vc-grade.no-grade {
  background: rgba(74, 82, 112, 0.1);
  color: var(--text-muted);
  border: 1px dashed var(--text-muted);
}

.vc-grade.no-grade:hover {
  background: rgba(74, 82, 112, 0.2);
}

.vc-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.vc-info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}

.vc-info-item .label {
  color: var(--text-muted);
}

.vc-info-item .value {
  color: var(--text-primary);
  font-family: 'Orbitron', monospace;
}

.vc-info-item .value.active {
  color: var(--accent-green);
}
</style>
