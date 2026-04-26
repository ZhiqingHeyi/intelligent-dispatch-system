<template>
  <div 
    class="vehicle-card"
    :class="{ 
      selected: isSelected,
      going: vehicle.direction === 'going',
      returning: vehicle.direction === 'returning',
      assigned: vehicle.status === 'assigned'
    }"
    @click="handleClick"
  >
    <div class="card-glow-border"></div>
    
    <div class="vc-top">
      <span class="vc-name">{{ vehicle.name }}</span>
      <span 
        class="vc-status"
        :class="statusClass"
        :style="statusStyle"
      >
        {{ statusLabel }}
      </span>
    </div>
    
    <div class="vc-bottom">
      <span 
        class="vc-grade-badge"
        :class="{ 'no-grade': !grade }"
        :style="grade ? {
          background: grade.color + '18',
          color: grade.color,
          border: '1px solid ' + grade.color + '44'
        } : {}"
        @click.stop="$emit('set-grade')"
      >
        {{ grade ? grade.name : '设置级配' }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDispatchStore } from '@/stores/dispatch'
import type { Vehicle } from '@/types'

const DIRECTION_LABELS: Record<string, string> = {
  returning: '返程',
  going: '送料',
  stopped: '停止',
  idle: '待命',
  assigned: '已调度'
}

const props = defineProps<{
  vehicle: Vehicle
  isSelected: boolean
}>()

const emit = defineEmits<{
  select: []
  'set-grade': []
}>()

const store = useDispatchStore()

const grade = computed(() => store.grades.find(g => g.id === props.vehicle.grade_id))

const statusLabel = computed(() => {
  return DIRECTION_LABELS[props.vehicle.direction] || DIRECTION_LABELS[props.vehicle.status] || '待命'
})

const statusClass = computed(() => {
  const d = props.vehicle.direction
  const s = props.vehicle.status
  if (s === 'assigned') return 'assigned'
  if (d === 'going') return 'going'
  if (d === 'returning') return 'returning'
  return 'stopped'
})

const statusStyle = computed(() => {
  const styles: Record<string, { bg: string; color: string; border: string }> = {
    assigned: { bg: 'rgba(192, 132, 252, 0.12)', color: '#c084fc', border: 'rgba(192, 132, 252, 0.25)' },
    going: { bg: 'rgba(0, 212, 255, 0.12)', color: '#00d4ff', border: 'rgba(0, 212, 255, 0.25)' },
    returning: { bg: 'rgba(0, 255, 136, 0.12)', color: '#00ff88', border: 'rgba(0, 255, 136, 0.25)' },
    stopped: { bg: 'rgba(90, 99, 128, 0.12)', color: '#5a6380', border: 'rgba(90, 99, 128, 0.25)' }
  }
  const s = styles[statusClass.value] || styles.stopped
  return {
    background: s.bg,
    color: s.color,
    border: `1px solid ${s.border}`
  }
})

const handleClick = () => {
  if (props.vehicle.status === 'assigned') return
  emit('select')
}
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

.vehicle-card.assigned {
  border-color: rgba(192, 132, 252, 0.35);
  opacity: 0.75;
  cursor: not-allowed;
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

.vc-status {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

.vc-bottom {
  display: flex;
  align-items: center;
}

.vc-grade-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

.vc-grade-badge:hover {
  filter: brightness(1.3);
  transform: scale(1.05);
}

.vc-grade-badge.no-grade {
  background: rgba(74, 82, 112, 0.1);
  color: var(--text-muted);
  border: 1px dashed var(--text-muted);
}

.vc-grade-badge.no-grade:hover {
  background: rgba(74, 82, 112, 0.2);
}
</style>
