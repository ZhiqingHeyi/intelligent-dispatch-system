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

const STATE_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  loading: { bg: 'rgba(255,217,61,0.12)', color: '#ffd93d', border: 'rgba(255,217,61,0.3)' },
  delivering: { bg: 'rgba(0,212,255,0.12)', color: '#00d4ff', border: 'rgba(0,212,255,0.3)' },
  unloading: { bg: 'rgba(255,107,107,0.12)', color: '#ff6b6b', border: 'rgba(255,107,107,0.3)' },
  returning: { bg: 'var(--accent-green-bg)', color: 'var(--accent-green)', border: 'var(--accent-green-border)' },
  stopped: { bg: 'var(--bg-subtle)', color: 'var(--text-muted)', border: 'var(--border-subtle)' }
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
  if (props.vehicle.status === 'assigned') return '已调度'
  if (props.vehicle.state_label && props.vehicle.state !== 'stopped') return props.vehicle.state_label
  return DIRECTION_LABELS[props.vehicle.direction] || '待命'
})

const statusClass = computed(() => {
  const d = props.vehicle.direction
  const s = props.vehicle.status
  const st = props.vehicle.state
  if (s === 'assigned') return 'assigned'
  if (st === 'loading') return 'loading'
  if (st === 'delivering') return 'going'
  if (st === 'unloading') return 'unloading'
  if (st === 'returning' || d === 'returning') return 'returning'
  if (d === 'going') return 'going'
  return 'stopped'
})

const statusStyle = computed(() => {
  if (props.vehicle.status === 'assigned') {
    return {
      background: 'var(--accent-purple-bg)',
      color: 'var(--accent-purple)',
      border: '1px solid var(--accent-purple-border)'
    }
  }
  const st = props.vehicle.state
  if (st && STATE_COLORS[st]) {
    const s = STATE_COLORS[st]
    return { background: s.bg, color: s.color, border: `1px solid ${s.border}` }
  }
  const styles: Record<string, { bg: string; color: string; border: string }> = {
    going: { bg: 'var(--accent-blue-bg)', color: 'var(--accent-blue)', border: 'var(--accent-blue-border)' },
    returning: { bg: 'var(--accent-green-bg)', color: 'var(--accent-green)', border: 'var(--accent-green-border)' },
    stopped: { bg: 'var(--bg-subtle)', color: 'var(--text-muted)', border: 'var(--border-subtle)' }
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
  border-radius: clamp(8px, 1vw, 10px);
  padding: clamp(8px, 1.2vh, 12px);
  backdrop-filter: blur(10px);
  transition: all 0.25s ease;
  cursor: pointer;
  min-width: 0;
}

@media screen and (max-width: 1200px) {
  .vehicle-card {
    padding: 8px;
    border-radius: 8px;
  }
}

.vehicle-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--shadow-color);
}

.vehicle-card.selected {
  border-color: var(--accent-blue);
  box-shadow: 0 0 20px var(--accent-blue-bg);
}

.vehicle-card.going {
  border-color: var(--accent-blue-border-hover);
  animation: going-pulse 2s ease-in-out infinite;
}

.vehicle-card.returning {
  border-color: var(--accent-green-border);
}

.vehicle-card.unloading {
  border-color: rgba(255,107,107,0.4);
}

.vehicle-card.assigned {
  border-color: var(--accent-purple-border);
  opacity: 0.75;
  cursor: not-allowed;
}

@keyframes going-pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--accent-blue-bg); }
  50% { box-shadow: 0 0 12px 2px var(--accent-blue-bg); }
}

.card-glow-border {
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: 10px;
  background: var(--glow-border);
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
  font-size: clamp(11px, 1vw, 13px);
  font-weight: 600;
  color: var(--text-primary);
}

.vc-status {
  font-size: clamp(9px, 0.8vw, 10px);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

@media screen and (max-width: 1200px) {
  .vc-name {
    font-size: 11px;
  }
  .vc-status {
    font-size: 9px;
    padding: 2px 5px;
  }
}

.vc-bottom {
  display: flex;
  align-items: center;
}

.vc-grade-badge {
  font-size: clamp(9px, 0.8vw, 10px);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

@media screen and (max-width: 1200px) {
  .vc-grade-badge {
    font-size: 9px;
    padding: 2px 5px;
  }
}

.vc-grade-badge:hover {
  filter: brightness(1.3);
  transform: scale(1.05);
}

.vc-grade-badge.no-grade {
  background: var(--grade-no-bg);
  color: var(--text-muted);
  border: 1px dashed var(--text-muted);
}

.vc-grade-badge.no-grade:hover {
  background: var(--bg-subtle-hover);
}
</style>
